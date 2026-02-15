import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from src.controller import app


def test_system_design_health_endpoint():
    client = app.test_client()
    response = client.get('/api/system-design/health')

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'ok'
    assert payload['try']['ui'] == '/system-design.html'


def test_system_design_shortcut_redirects_to_static_page():
    client = app.test_client()
    response = client.get('/system-design')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/system-design.html')
