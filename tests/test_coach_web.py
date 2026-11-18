import base64
import http.client
import json
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from royalemind.coach_web import handler


def test_hosted_password_and_post_guards(tmp_path, monkeypatch):
    monkeypatch.setenv('ROYALEMIND_PUBLIC', '1')
    monkeypatch.setenv('ROYALEMIND_ACCESS_PASSWORD', 'fixture-only')
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-key')
    monkeypatch.delenv('ROYALEMIND_REPLAY_AI_ENABLED', raising=False)
    journal = tmp_path / 'coach.sqlite'
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler(journal, tmp_path / 'uploads'))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    auth = {'Authorization': 'Basic ' + base64.b64encode(b'coach:fixture-only').decode()}
    browser = {**auth, 'X-Requested-With': 'royalemind-coach'}

    def call(method, path, headers=None, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    try:
        assert call('GET', '/api/matches')[0] == 401
        assert call('GET', '/api/capabilities', auth) == (200, b'{"replayAI": false}')
        with patch('royalemind.coach_web.analyze_video') as analyze:
            assert call('POST', '/api/analyze/replay', auth)[0] == 403
            assert call('POST', '/api/analyze/replay', browser)[0] == 503
            analyze.assert_not_called()
        assert not journal.exists()
        decision = {'own': 7, 'enemy': 5, 'cost': 4, 'context': 'defend'}
        status, body = call('POST', '/api/decision', {**browser, 'Content-Type': 'application/json'}, json.dumps(decision))
        assert status == 200
        assert json.loads(body)['remaining_elixir'] == 3
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
