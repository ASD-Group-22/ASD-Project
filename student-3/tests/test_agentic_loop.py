import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend-service'))
from agentic_loop import run_loop, LoopError
from group_recommendations import validate_result

class SingleAttemptTests(unittest.TestCase):
    def context(self):
        return {'group_sizes': [3, 3], 'requirements': {'python': {'minimum_level': 2, 'level': 'intermediate', 'weight': 1, 'amount': 'little'}},
                'students': [{'student_id': i, 'name': str(i), 'skills': {'python': 3 if i == 1 else 0}} for i in range(1, 7)]}

    def run_case(self, approved=False, offline=False, invalid=False):
        calls = []
        def propose(messages, attempt):
            calls.append('proposal')
            return json.dumps({'groups': [{'student_ids': [1, 1, 3] if invalid else [1, 2, 3]}, {'student_ids': [4, 5, 6]}]})
        def review(messages, attempt):
            calls.append('review')
            if offline: raise RuntimeError('Offline')
            return json.dumps({'approved': approved, 'reason': 'Some skill gaps.', 'issues': ['Missing coverage']})
        result = run_loop(self.context(), 'Propose', 'Review', propose, review, validate_result)
        self.assertEqual(calls, ['proposal','review'])
        return result

    def test_reviewer_concerns_return_to_human_once(self):
        groups, loop = self.run_case()
        self.assertEqual(loop['attempts'], 1)
        self.assertEqual(loop['stop_reason'], 'human_review')
        self.assertFalse(loop['review']['approved'])
        self.assertFalse(loop['quality']['criteria_met'])
        self.assertEqual(len(groups), 2)

    def test_review_outage_does_not_discard_proposal(self):
        _, loop = self.run_case(offline=True)
        self.assertFalse(loop['review_completed'])

    def test_approval_can_include_caveats(self):
        _, loop = self.run_case(approved=True)
        self.assertTrue(loop['review']['approved'])

    def test_duplicates_still_fail_once(self):
        with self.assertRaises(LoopError) as caught: self.run_case(invalid=True)
        self.assertEqual(caught.exception.loop['attempts'], 1)
        self.assertEqual(caught.exception.loop['stop_reason'], 'invalid_proposal')

    def test_sizes_are_flexible_within_three_to_five(self):
        c = self.context()
        c['students'] += [{'student_id': i, 'name': str(i), 'skills': {}} for i in (7,8)]
        groups = validate_result({'groups':[{'student_ids':[1,2,3]}, {'student_ids':[4,5,6,7,8]}]}, c['students'], [4,4], c['requirements'])
        self.assertEqual([len(g['student_ids']) for g in groups], [3,5])
        self.assertIn('No explanation', groups[0]['reasoning'])

if __name__ == '__main__': unittest.main()
