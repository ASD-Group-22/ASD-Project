"""Real HTTP/SQLite integration; only Ollama is replaced with a controlled server."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

ROOT = Path(__file__).resolve().parents[2]


def test_services_over_http(tmp_path):
    processes = []
    logs = []

    def start(folder, bootstrap, extra=None):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]

        env = os.environ.copy()
        env.update(extra or {})
        env['PYTHONPATH'] = str(ROOT / folder) + os.pathsep + env.get('PYTHONPATH', '')

        log = open(tmp_path / f'{port}.log', 'w+')
        logs.append(log)

        code = bootstrap + f'\nfrom werkzeug.serving import make_server\nmake_server("127.0.0.1", {port}, app.app).serve_forever()'
        process = subprocess.Popen([sys.executable, '-B', '-c', code], cwd=tmp_path, env=env, stdout=log, stderr=log)
        processes.append(process)
        url = f'http://127.0.0.1:{port}'

        for _ in range(100):
            if process.poll() is not None:
                log.seek(0)
                raise AssertionError(log.read())

            try:
                requests.get(url, timeout=0.2)
                return url
            except requests.ConnectionError:
                time.sleep(0.05)

        raise AssertionError(f'Service {folder} did not start')

    captured = []

    class Ollama(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured.append(payload)
            context = json.loads(payload['messages'][1]['content'])
            ids = [s['student_id'] for s in context['students']]
            groups, offset = [], 0

            for size in context['group_sizes']:
                groups.append({'student_ids': ids[offset:offset+size], 'reasoning': 'Test model response using supplied profiles.'})
                offset += size

            body = json.dumps({'message': {'content': json.dumps({'groups': groups})}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    fake = HTTPServer(('127.0.0.1', 0), Ollama)
    thread = threading.Thread(target=fake.serve_forever, daemon=True)
    thread.start()

    try:
        skill_db = start('student-4/database',
            f'import init_db\ninit_db.DATA_DIR = {str(tmp_path)!r}\ninit_db.DATABASE_PATH = {str(tmp_path / "skills.db")!r}\ninit_db.init_db()\nimport app\napp.DATABASE_PATH = init_db.DATABASE_PATH')

        skill_api = start('student-4/backend', 'import app', {'DATABASE_SERVICE_URL': skill_db})
        group_db = start('student-3/database-service', 'import init_db\nimport app',
                         {'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'groups.db')})

        group_api = start('student-3/backend-service', 'import app',
            {'DB_URL': group_db, 'SKILL_PROFILE_SERVICE_URL': skill_api,
             'OLLAMA_URL': os.getenv('LIVE_OLLAMA_URL', f'http://127.0.0.1:{fake.server_port}')})

        assert 'ASD' in requests.get(group_api + '/ui/subjects', timeout=5).json()
        requirements = {'subject': 'ASD', 'requirements': {'python': {'level': 'intermediate', 'amount': 'extensive'}}}
        assert requests.post(group_api + '/ui/skills/create', json=requirements, timeout=5).status_code == 201
        assert requests.post(group_api + '/ui/skills/create', json={
            'subject': 'ASD', 'requirements': {'html/css': {'level': 'beginner', 'amount': 'little'}}}, timeout=5).status_code == 200

        deleted = requests.delete(group_api + '/ui/skills/delete/ASD/html%2Fcss', timeout=5)
        assert deleted.status_code == 200
        assert 'html/css' not in deleted.json()

        live = requests.get(group_api + '/ai/profiles', timeout=5).json()
        assert len(live) == 10
        profile_id = live[0]['profile_id']
        assert requests.put(skill_api + f'/api/profiles/{profile_id}', json={
            'skills': [{'skill_name':'Python', 'skill_level':'Advanced', 'strength':'Updated live'}]}, timeout=5).status_code == 200

        response = requests.post(group_api + '/ai/group-recommendation', json={'subject':'ASD'}, timeout=390)
        assert response.status_code == 200, response.text
        data = response.json()

        assert data['students'][0]['skills']['python'] == 3
        assert data['students'][0]['skill_details'][0]['strength'] == 'Updated live'
        assert sorted(s for g in data['recommendation']['groups'] for s in g['student_ids']) == list(range(1, 11))
        assert len(captured) == (0 if os.getenv('LIVE_OLLAMA_URL') else 1)
        assert requests.get(group_db + '/groups', timeout=5).json() == []

    finally:
        fake.shutdown()
        fake.server_close()

        for process in processes:
            process.terminate()
            process.wait(timeout=10)

        for log in logs:
            log.close()
