import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def patient_payload() -> dict:
    return {
        'diabetes': False,
        'family_history': True,
        'obesity': False,
        'alcohol_consumption': False,
        'previous_heart_problems': True,
        'medication_use': True,
        'diet': 1,
        'stress_level': 8,
        'physical_activity_days_per_week': 3,
        'age': 0.5,
        'cholesterol': 0.6,
        'heart_rate': 0.7,
        'exercise_hours_per_week': 0.3,
        'sedentary_hours_per_day': 0.8,
        'bmi': 0.75,
        'triglycerides': 0.5,
        'sleep_hours_per_day': 0.6,
        'blood_sugar': 0.4,
        'ck_mb': 0.3,
        'troponin': 0.2,
        'systolic_blood_pressure': 0.65,
        'diastolic_blood_pressure': 0.45,
    }


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['model_loaded'] is False
    assert data['model_name'] == 'heart_attack_rf'


def test_ready_success(client, monkeypatch):
    class FakeManager:
        def load_model(self):
            pass

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    response = client.get('/ready')
    assert response.status_code == 200
    assert response.json()['status'] == 'ready'


def test_ready_failure(client, monkeypatch):
    class FakeManager:
        def load_model(self):
            raise RuntimeError('model not found')

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    response = client.get('/ready')
    assert response.status_code == 503
    assert 'model not found' in response.json()['detail']


def test_metrics(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'predict_requests_total' in response.text


def test_main_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'Проверь своё сердце' in response.text


def test_predict_success(client, monkeypatch):
    class FakeManager:
        def predict_patients(self, patients):
            assert len(patients) == 2
            return [0.123456, 0.876544]

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    payload = {'patients': [patient_payload(), patient_payload()]}
    response = client.post('/predict', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data['predictions']) == 2
    assert data['predictions'][0]['id'] == 1
    assert data['predictions'][0]['prediction'] == 0
    assert data['predictions'][1]['prediction'] == 1
    assert 'probability' in data['predictions'][0]

    metrics_response = client.get('/metrics')
    assert 'predict_requests_total 1.0' in metrics_response.text


def test_predict_empty(client):
    response = client.post('/predict', json={'patients': []})
    assert response.status_code == 422


def test_predict_invalid_payload(client):
    response = client.post('/predict', json={'patients': [{'age': 'abc'}]})
    assert response.status_code == 422


def test_get_prediction_success(client, monkeypatch):
    class FakeManager:
        def predict_patients(self, patients):
            assert len(patients) == 1
            return [0.852]

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    response = client.post('/api/get_prediction/', json=patient_payload())
    assert response.status_code == 200
    assert response.json() == {'predict': 85.2}


def test_get_prediction_invalid(client):
    response = client.post('/api/get_prediction/', json={'diet': 1})
    assert response.status_code == 422


def test_get_predictions_success(client, monkeypatch):
    class FakeManager:
        def predict_csv(self, content):
            assert b'diabetes' in content
            return [{'id': 1, 'predict': 85.2}, {'id': 2, 'predict': 12.4}]

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    csv_content = b'id,diabetes,age\n1,0,0.5\n2,1,0.7\n'
    response = client.post(
        '/api/get_predictions/',
        files={'file': ('heart.csv', csv_content, 'text/csv')},
    )
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'predict': 85.2},
        {'id': 2, 'predict': 12.4},
    ]


def test_get_predictions_invalid_type(client, monkeypatch):
    class FakeManager:
        def predict_csv(self, content):
            return []

    monkeypatch.setattr(app.state, 'model_manager', FakeManager())
    response = client.post(
        '/api/get_predictions/',
        files={'file': ('heart.txt', b'not csv', 'text/plain')},
    )
    assert response.status_code == 400
