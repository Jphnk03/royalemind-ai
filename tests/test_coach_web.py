import http.client
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from royalemind.coach_web import handler


def test_local_server_rejects_foreign_hosts_and_origins_and_keeps_ai_off(tmp_path):
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler(tmp_path/'coach.sqlite3', tmp_path/'uploads'))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host = f'127.0.0.1:{server.server_address[1]}'

    def request(method, path, **headers):
        client = http.client.HTTPConnection(host, timeout=5)
        try:
            client.request(method, path, body=b'' if method == 'POST' else None, headers=headers)
            response = client.getresponse()
            response.read()
            return response.status
        finally:
            client.close()

    try:
        assert request('GET', '/') == 200
        assert request('GET', '/', Host='foreign.example') == 403
        for headers in ({}, {'Origin':'https://foreign.example'}, {'Origin':'null'}, {'Origin':'http://'+host, 'Sec-Fetch-Site':'cross-site'}):
            assert request('POST', '/api/matches', **headers) == 403
        with patch.dict('os.environ', {'OPENAI_API_KEY':'test-only'}, clear=True), patch('royalemind.coach_web.analyze_video') as analysis:
            assert request('POST', '/api/analyze/example', Origin='http://'+host) == 503
            analysis.assert_not_called()
        assert not (tmp_path/'coach.sqlite3').exists(), 'blocked requests must not open or mutate the journal'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
