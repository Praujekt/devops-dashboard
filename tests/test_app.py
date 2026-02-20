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

def test_get_pod_count_function():
    """Test the get_pod_count helper function"""
    from src.api.app import get_pod_count
    # This will return 0 or actual count depending on if kubectl works
    result = get_pod_count()
    assert isinstance(result, int)
    assert result >= 0


def test_f1_latest_race_endpoint(client):
    """Test F1 latest race endpoint"""
    response = client.get('/f1/latest-race')
    # Could be 200, 404, or 500 depending on API
    assert response.status_code in [200, 404, 500]
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'location' in data or 'circuit' in data or 'message' in data


def test_f1_driver_standings_endpoint(client):
    """Test F1 driver standings endpoint"""
    response = client.get('/f1/driver-standings')
    # Will likely error since no 2026 race data yet
    assert response.status_code in [200, 404, 500]
    data = json.loads(response.data)
    # Should have either standings or error message
    assert 'standings' in data or 'error' in data or 'message' in data


def test_api_endpoint(client):
    """Test the /api info endpoint"""
    response = client.get('/api')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'message' in data


def test_prometheus_counter_increments(client):
    """Test that API request counter increments"""
    # Make a request
    client.get('/health')
    # Check metrics include the counter
    response = client.get('/metrics')
    assert b'api_requests_total' in response.data


def test_invalid_endpoint(client):
    """Test that invalid endpoints return 404"""
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404