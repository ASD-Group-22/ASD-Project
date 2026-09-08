"""Single proposal with advisory review and human decision; no network dependencies."""
import json

MAX_ATTEMPTS = 1
BALANCE_TARGET = 0.25


class LoopError(Exception):
    def __init__(self, message, status, loop):
        super().__init__(message)
        self.status = status
        self.loop = loop


def make_plan(context):
    requirements = context['requirements']
    students = context['students']
    count = len(context['group_sizes'])
    shortages = []
    lower_bound = 0

    for skill, spec in requirements.items():
        qualified = [s['student_id'] for s in students
                     if s['skills'].get(skill, 0) >= spec['minimum_level']]
        missing_groups = max(0, count - len(qualified))
        lower_bound += missing_groups * spec['weight']

        if missing_groups:
            shortages.append({'skill': skill, 'required_level': spec['level'],
                              'qualified_student_ids': qualified,
                              'minimum_groups_without_coverage': missing_groups})

    return {
        'group_sizes': context['group_sizes'],
        'max_attempts': MAX_ATTEMPTS,
        'balance_target': BALANCE_TARGET,
        'unavoidable_weighted_gap_lower_bound': lower_bound,
        'known_shortages': shortages,
        'priority': 'Minimize weighted missing requirements first, then balance average skill scores per student.',
        'balance_definition': '(highest group average - lowest group average) / mean group average; zero when every score is zero.',
        'limitation': 'The shortage bound checks each skill separately. It does not prove that all requirements can be satisfied together.',
    }


def evaluate(groups, requirements, plan):
    weighted_gaps = sum(requirements[skill]['weight']
                        for group in groups for skill in group['unmet_requirements'])
    averages = [g['weighted_skill_score'] / len(g['student_ids']) for g in groups]
    mean = sum(averages) / len(averages)
    ratio = (max(averages) - min(averages)) / mean if mean else 0.0

    return {
        'weighted_gaps': weighted_gaps,
        'gap_above_known_lower_bound': max(0, weighted_gaps - plan['unavoidable_weighted_gap_lower_bound']),
        'average_skill_scores': [round(n, 4) for n in averages],
        'balance_ratio': ratio,
        'all_requirements_covered': weighted_gaps == 0,
        'criteria_met': weighted_gaps <= plan['unavoidable_weighted_gap_lower_bound'] and ratio <= BALANCE_TARGET,
    }


def parse_review(text):
    review = json.loads(text)
    if not isinstance(review, dict) or type(review.get('approved')) is not bool:
        raise ValueError('Reviewer must return a boolean approved value.')

    if not isinstance(review.get('reason'), str) or not review['reason'].strip():
        raise ValueError('Reviewer must explain its decision.')

    if not isinstance(review.get('issues'), list) or any(not isinstance(i, str) for i in review['issues']):
        raise ValueError('Reviewer issues must be a list of strings.')


    return review


def run_loop(context, proposer_prompt, reviewer_prompt, propose, review_model, validate, event=None):
    event = event or (lambda stage, **details: None)
    plan = make_plan(context)
    plan['review_policy'] = 'Advisory only. One proposal, at most one Llama review, then human decision.'
    event('PLAN', context=context, plan=plan)
    loop = {'plan': plan, 'trace': [], 'stop_reason': 'human_review',
            'selected_attempt': None, 'quality': None, 'review': None,
            'attempts': 1, 'requires_human_review': True}
    messages = [{'role': 'system', 'content': proposer_prompt},
                {'role': 'user', 'content': json.dumps(context)}]
    try:
        raw = propose(messages, 1)
    except Exception as exc:
        loop['stop_reason'] = 'proposal_error'
        loop['trace'] = [{'attempt': 1, 'status': 'proposal_error', 'feedback': [str(exc)]}]
        raise LoopError('The proposal call failed. See the loop details.', 503, loop) from exc
    try:
        groups = validate(json.loads(raw), context['students'], context['group_sizes'], context['requirements'])
    except (ValueError, TypeError, KeyError) as exc:
        loop['stop_reason'] = 'invalid_proposal'
        loop['trace'] = [{'attempt': 1, 'status': 'invalid', 'feedback': [str(exc)]}]
        raise LoopError('The proposal has invalid membership or JSON. See the loop details.', 502, loop) from exc
    quality = evaluate(groups, context['requirements'], plan)
    event('OBSERVE', attempt=1, valid=True, quality=quality)
    review_completed = True
    try:
        review = parse_review(review_model([
            {'role': 'system', 'content': reviewer_prompt},
            {'role': 'user', 'content': json.dumps({**context, 'proposal': groups, 'python_checks': quality})}
        ], 1))
    except Exception as exc:
        review_completed = False
        review = {'approved': False, 'reason': 'Llama review unavailable; decide using the groups and Python checks.',
                  'issues': [str(exc)]}
    feedback = [review['reason'], *review['issues']]
    if not quality['all_requirements_covered']:
        feedback.append('Some required skills are missing. This is a warning, not a rejection.')
    if not quality['criteria_met']:
        feedback.append('Suggested quality targets were not met. You may still accept this proposal.')
    loop.update(selected_attempt=1, quality=quality, review=review,
                review_completed=review_completed,
                trace=[{'attempt': 1, 'status': 'valid', 'quality': quality,
                        'review': review, 'groups': groups, 'feedback': feedback}])
    event('ADAPT', attempt=1, action='return_for_human_review', feedback=feedback)
    return groups, loop
