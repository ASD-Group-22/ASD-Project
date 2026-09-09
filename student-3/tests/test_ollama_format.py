import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend-service'))
from group_recommendations import ollama_payload, ollama_content

class OllamaFormatTests(unittest.TestCase):
    def test_dynamic_schema_and_original_prompt_preserved(self):
        messages = [{'role':'system','content':'Propose'}, {'role':'user','content':'Context'}]
        payload = ollama_payload('qwen', 'proposer', messages, [{'student_id':i} for i in range(1,7)], [3,3])
        groups = payload['format']['properties']['groups']
        self.assertEqual(groups['minItems'], 2)
        self.assertEqual(groups['maxItems'], 2)
        self.assertEqual(groups['items']['properties']['student_ids']['items']['enum'], list(range(1,7)))
        self.assertEqual(messages[0]['content'], 'Propose')
        self.assertEqual(payload['options']['temperature'], 0)
        self.assertFalse(payload['stream'])

    def test_review_boolean_schema(self):
        payload = ollama_payload('llama', 'reviewer', [{'role':'system','content':'Review'}], [], [])
        self.assertEqual(payload['format']['properties']['approved']['type'], 'boolean')

    def test_truncated_output_is_explicit(self):
        with self.assertRaisesRegex(ValueError, 'token limit'):
            ollama_content({'done_reason':'length','message':{'content':'{"groups":['}})

    def test_complete_content_is_returned(self):
        self.assertEqual(ollama_content({'done_reason':'stop','message':{'content':'{}'}}), '{}')

if __name__ == '__main__': unittest.main()
