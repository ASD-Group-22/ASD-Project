import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest


class RecommendationHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.old_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(cls.temporary.name) / 'history.db')
        cls.saved_modules = {name: value for name, value in sys.modules.items()
                             if name == 'services' or name.startswith('services.')
                             or name == 'models' or name.startswith('models.')}
        for name in cls.saved_modules:
            del sys.modules[name]
        cls.database_dir = Path(__file__).resolve().parents[1] / 'database-service'
        sys.path.insert(0, str(cls.database_dir))
        spec = importlib.util.spec_from_file_location('history_database_app', cls.database_dir / 'app.py')
        cls.database = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.database)
        cls.database.app.config['TESTING'] = True

    @classmethod
    def tearDownClass(cls):
        cls.database.engine.dispose()
        for name in list(sys.modules):
            if name == 'services' or name.startswith('services.') or name == 'models' or name.startswith('models.'):
                del sys.modules[name]
        sys.modules.update(cls.saved_modules)
        sys.path.remove(str(cls.database_dir))
        if cls.old_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = cls.old_url
        cls.temporary.cleanup()

    def setUp(self):
        self.client = self.database.app.test_client()
        db = self.database.SessionLocal()
        try:
            db.query(self.database.Recommendation).delete()
            db.commit()
        finally:
            db.close()

    def sample(self, subject='ASD'):
        return {
            'subject': subject,
            'recommendation': {'groups': [{'student_ids': [1, 2, 3], 'reasoning': 'Complementary skills.'}], 'warnings': []},
            'students': [{'student_id': 1, 'skills': {'python': 3}}],
            'requirements': {'python': {'level': 'intermediate'}},
            'model': 'llama3.1:8b',
        }

    def test_save_list_read_delete_and_no_update(self):
        payload = self.sample()
        created = self.client.post('/recommendations', json=payload)
        self.assertEqual(created.status_code, 201)
        record = created.json
        self.assertTrue(record['saved_at'])
        self.assertEqual(record['snapshot'], payload)
        record_id = record['id']
        history = self.client.get('/recommendations').json
        self.assertEqual(history[0]['id'], record_id)
        self.assertEqual(history[0]['group_count'], 1)
        self.assertNotIn('snapshot', history[0])
        self.assertEqual(self.client.get(f'/recommendations/history/{record_id}').json['snapshot'], payload)
        for method in ('put', 'patch'):
            self.assertEqual(getattr(self.client, method)(f'/recommendations/history/{record_id}', json=payload).status_code, 405)
        self.assertEqual(self.client.delete(f'/recommendations/history/{record_id}').status_code, 200)
        self.assertEqual(self.client.get('/recommendations').json, [])
        self.assertEqual(self.client.get(f'/recommendations/history/{record_id}').status_code, 404)
        self.assertEqual(self.client.delete(f'/recommendations/history/{record_id}').status_code, 404)

    def test_newest_first_filter_and_latest_compatibility(self):
        first = self.client.post('/recommendations', json=self.sample()).json
        second_payload = self.sample()
        second_payload['recommendation']['warnings'] = ['Second attempt']
        second = self.client.post('/recommendations', json=second_payload).json
        third = self.client.post('/recommendations', json=self.sample('AI')).json
        self.assertEqual([r['id'] for r in self.client.get('/recommendations').json], [third['id'], second['id'], first['id']])
        self.assertEqual([r['id'] for r in self.client.get('/recommendations?subject=ASD').json], [second['id'], first['id']])
        self.assertEqual(self.client.get('/recommendations/ASD').json, second_payload['recommendation'])
        self.assertEqual(self.client.get('/recommendations?subject=missing').json, [])

    def test_older_rows_are_readable_without_migration(self):
        db = self.database.SessionLocal()
        try:
            old = self.database.Recommendation(subject='ASD', recommendation='Legacy explanation')
            db.add(old)
            db.commit()
            record_id = old.id
        finally:
            db.close()
        record = self.client.get(f'/recommendations/history/{record_id}').json
        self.assertIsNone(record['saved_at'])
        self.assertEqual(record['snapshot']['recommendation'], 'Legacy explanation')
        self.assertEqual(self.client.get('/recommendations/ASD').json, 'Legacy explanation')

    def test_invalid_saves_do_not_create_rows(self):
        for payload in (None, [], {}, {'subject': ' ', 'recommendation': 'x'},
                        {'subject': 'ASD', 'recommendation': ''},
                        {'subject': 'ASD', 'recommendation': {}},
                        {'subject': 'ASD', 'recommendation': 12}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/recommendations', json=payload).status_code, 400)
        self.assertEqual(self.client.get('/recommendations').json, [])


if __name__ == '__main__':
    unittest.main()