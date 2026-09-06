"""Live profile retrieval, Ollama team formation, and deterministic validation."""
import json
import math
import os
from pathlib import Path
from urllib.parse import quote
import requests

LEVELS = {'beginner': 1, 'intermediate': 2, 'advanced': 3, 'expert': 3}
WEIGHTS = {'little': 1, 'moderate': 2, 'extensive': 3}


class RecommendationError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def get_json(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RecommendationError('Could not retrieve data. Check the group database and skill profile services.', 503) from exc


def load_profiles():
    base = os.getenv('SKILL_PROFILE_SERVICE_URL', 'http://student-4-backend:5005')
    profiles = get_json(f'{base.rstrip("/")}/api/profiles')

    if not isinstance(profiles, list):
        raise RecommendationError('Skill profile service returned an invalid profile list.', 502)
    students, seen = [], set()

    for profile in profiles:
        if not isinstance(profile, dict):
            raise RecommendationError('Invalid skill profile record.', 502)
        
        sid = profile.get('student_id')

        if type(sid) is not int or sid <= 0 or sid in seen:
            raise RecommendationError('Skill profiles must contain unique positive student IDs.', 502)

        seen.add(sid)
        skills, details = {}, []
        raw_skills = profile.get('skills', [])

        if not isinstance(raw_skills, list):
            raise RecommendationError(f'Invalid skills for student {sid}.', 502)
        
        for skill in raw_skills:
            if not isinstance(skill, dict):
                raise RecommendationError(f'Invalid skill for student {sid}.', 502)
            name = str(skill.get('skill_name') or '').strip().lower()
            level = str(skill.get('skill_level') or '').strip().lower()
            if not name or level not in LEVELS:
                raise RecommendationError(f'Student {sid} has an unsupported skill name or level. Use Beginner, Intermediate, Advanced, or Expert.', 422)
            skills[name] = max(skills.get(name, 0), LEVELS[level])
            details.append({'skill_name': name, 'skill_level': level,
                            'strength': skill.get('strength') or '', 'weakness': skill.get('weakness') or ''})

        students.append({'student_id': sid, 'profile_id': profile.get('profile_id'),
                         'name': f'Student {sid}', 'skills': skills, 'skill_details': details})

    return students


def normalize_requirements(raw):
    if not isinstance(raw, dict) or not raw:
        raise RecommendationError('Add project skill requirements before requesting groups.', 422)

    requirements = {}

    for name, spec in raw.items():
        if not isinstance(spec, dict):
            raise RecommendationError('Invalid project requirement format.', 422)

        name = name.strip().lower()
        level = str(spec.get('level', '')).strip().lower()
        amount = str(spec.get('amount', '')).strip().lower()

        if not name or name in requirements or level not in LEVELS or amount not in WEIGHTS:
            raise RecommendationError('Requirements need unique skills, a supported level, and little/moderate/extensive amount.', 422)

        requirements[name] = {'level': level, 'minimum_level': LEVELS[level], 'amount': amount, 'weight': WEIGHTS[amount]}

    return requirements


def group_sizes(count, target):
    if count < 3:
        raise RecommendationError('At least three students with skill profiles are required.', 422)

    number = max(math.ceil(count / 5), min(math.ceil(count / target), count // 3))
    base, extra = divmod(count, number)

    return [base + (i < extra) for i in range(number)]


def validate_result(result, students, sizes, requirements):
    if not isinstance(result, dict) or not isinstance(result.get('groups'), list):
        raise ValueError('Return an object containing a groups array.')

    groups = result['groups']

    if len(groups) != len(sizes):
        raise ValueError(f'Return exactly {len(sizes)} groups.')

    by_id = {s['student_id']: s for s in students}
    assigned, actual_sizes, verified = [], [], []

    for index, group in enumerate(groups, 1):
        if not isinstance(group, dict):
            raise ValueError('Each group must be an object.')

        ids = group.get('student_ids')

        if not isinstance(ids, list) or any(type(sid) is not int or sid not in by_id for sid in ids):
            raise ValueError('Use only integer student IDs from the supplied profiles.')

        reasoning = group.get('reasoning')

        if not isinstance(reasoning, str) or not reasoning.strip():
            raise ValueError('Include reasoning for each group.')

        assigned.extend(ids)
        actual_sizes.append(len(ids))
        coverage, score = [], 0

        for skill, requirement in requirements.items():
            qualified = [sid for sid in ids if by_id[sid]['skills'].get(skill, 0) >= requirement['minimum_level']]
            coverage.append({'skill': skill, 'required_level': requirement['level'], 'amount': requirement['amount'],
                             'qualified_student_ids': qualified, 'met': bool(qualified)})
            score += requirement['weight'] * sum(by_id[sid]['skills'].get(skill, 0) for sid in ids)

        verified.append({'group_name': f'Group {index}', 'student_ids': ids,
                         'members': [by_id[sid]['name'] for sid in ids], 'reasoning': reasoning.strip(),
                         'coverage': coverage, 'unmet_requirements': [c['skill'] for c in coverage if not c['met']],
                         'weighted_skill_score': score})
    if sorted(actual_sizes) != sorted(sizes):
        raise ValueError(f'Group sizes must be {sizes}.')

    if len(assigned) != len(set(assigned)) or set(assigned) != set(by_id):
        raise ValueError('Assign every supplied student exactly once, without duplicates or omissions.')

    return verified


def recommend(data):
    if not isinstance(data, dict) or not isinstance(data.get('subject'), str) or not data['subject'].strip():
        raise RecommendationError('Select a subject.')
    
    subject = data['subject'].strip()
    target = data.get('group_size', 5)

    if type(target) is not int or not 3 <= target <= 5:
        raise RecommendationError('group_size must be an integer from 3 to 5.')
    
    db_url = os.getenv('DB_URL', 'http://database-service:6000').rstrip('/')
    requirements = normalize_requirements(get_json(f'{db_url}/requirements/{quote(subject, safe="")}'))
    students = load_profiles()
    selected = data.get('student_ids')

    if selected is not None:
        if (not isinstance(selected, list) or not selected or
                any(type(sid) is not int or sid <= 0 for sid in selected) or len(set(selected)) != len(selected)):
            raise RecommendationError('student_ids must be a nonempty list of unique positive integer IDs.')

        unknown = set(selected) - {s['student_id'] for s in students}

        if unknown:
            raise RecommendationError(f'No skill profiles found for student IDs: {sorted(unknown)}.', 422)

        students = [s for s in students if s['student_id'] in selected]

    empty = [s['student_id'] for s in students if not s['skills']]

    if empty:
        raise RecommendationError(f'Add skills for students {empty} before forming groups.', 422)

    sizes = group_sizes(len(students), target)
    context = {'subject': subject, 'requirements': requirements, 'students': students, 'group_sizes': sizes}

    prompt_root = Path(
        os.getenv(
            "PROMPT_ROOT",
            str(Path(__file__).resolve().parents[1] / "prompts"),
        )
    )

    prompt_file = (
        prompt_root
        / "group_service"
        / "implementation"
        / "group_balance_prompt.txt"
    )

    try:
        system = prompt_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RecommendationError(
            "Could not read the group balancing prompt. "
            "Check PROMPT_ROOT and the prompts volume mount.",
            503,
        ) from exc
    
    messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': json.dumps(context)}]
    model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    ollama_url = os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434').rstrip('/')

    for attempt in range(2):
        try:
            response = requests.post(f'{ollama_url}/api/chat', json={
                'model': model, 'messages': messages, 'format': 'json', 'stream': False,
                'options': {'temperature': 0.2}}, timeout=(10, 180))
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RecommendationError(f'Ollama is unavailable or model {model} is not installed. Check Ollama and pull the configured model.', 503) from exc

        text = ''

        try:
            text = response.json()['message']['content']
            groups = validate_result(json.loads(text), students, sizes, requirements)
            break
        except (ValueError, KeyError, TypeError) as exc:
            if attempt == 1:
                raise RecommendationError('Ollama returned invalid groups after a repair attempt. No groups were saved; try again or use a more capable model.', 502) from exc

            messages.extend([{'role': 'assistant', 'content': text if isinstance(text, str) else ''},
                             {'role': 'user', 'content': f'Validation failed: {exc}. Correct the JSON using the original profiles and constraints.'}])

    warnings = [f'{g["group_name"]} lacks the required level for: {", ".join(g["unmet_requirements"])}.'
                for g in groups if g['unmet_requirements']]

    return {'subject': subject, 'requirements': requirements, 'students': students,
            'recommendation': {'groups': groups, 'warnings': warnings}, 'model': model,
            'profile_source': 'student-4', 'attempts': attempt + 1,
            'note': 'AI proposal for review. Coverage is checked against recorded skills; balance is a heuristic, not an optimality guarantee.'}
