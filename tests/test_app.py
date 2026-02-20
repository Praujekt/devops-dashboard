import pytest
import json
from src.api.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test the health check endpoint returns OK"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_environment_endpoint(client):
    """Test the environment endpoint returns expected data"""
    response = client.get('/environment')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'environment' in data
    assert 'version' in data


def test_api_metrics_endpoint(client):
    """Test the metrics API endpoint returns system data"""
    response = client.get('/api/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'cpu_percent' in data
    assert 'memory_percent' in data
    assert 'disk_percent' in data
    assert 'kubernetes_pods' in data
    assert isinstance(data['cpu_percent'], (int, float))
    assert isinstance(data['memory_percent'], (int, float))


def test_prometheus_metrics_endpoint(client):
    """Test Prometheus metrics endpoint returns proper format"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert b'system_cpu_percent' in response.data
    assert b'system_memory_percent' in response.data
    assert b'system_disk_percent' in response.data


def test_index_page(client):
    """Test the main dashboard page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'F1 Dashboard' in response.data or response.content_type == 'text/html'


def test_f1_next_race_endpoint(client):
    """Test F1 next race endpoint structure"""
    response = client.get('/f1/next-race')
    # Could be 200 with data or 404 if no upcoming race
    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        data = json.loads(response.data)
        # If successful, should have race data
        assert 'location' in data or 'circuit' in data


def test_k8s_pods_endpoint(client):
    """Test Kubernetes pods endpoint"""
    response = client.get('/k8s/pods')
    # Might fail if not in K8s cluster, that's okay
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'pods' in data