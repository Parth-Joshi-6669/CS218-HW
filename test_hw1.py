import pytest
import os
from hw1 import app

# Set up the testing client and environment
@pytest.fixture
def client():
    # Explicitly set the API_KEY for testing
    os.environ['API_KEY'] = 'test_api_key'
    app.config['API_KEY'] = 'test_api_key'
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Test CPU Usage Endpoint
def test_cpu_usage(client):
    response = client.get('/cpu', headers={'X-API-KEY': 'test_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'cpu_usage' in data
    assert isinstance(data['cpu_usage'], (int, float))

# Test Memory Usage Endpoint
def test_memory_usage(client):
    response = client.get('/memory', headers={'X-API-KEY': 'test_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'memory_usage' in data
    assert isinstance(data['memory_usage'], (int, float))

# Test Disk Usage Endpoint
def test_disk_usage(client):
    response = client.get('/disk', headers={'X-API-KEY': 'test_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'disk_usage' in data
    assert isinstance(data['disk_usage'], (int, float))

# Test Bandwidth Usage Endpoint
def test_bandwidth_usage(client):
    response = client.get('/bandwidth', headers={'X-API-KEY': 'test_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'bandwidth_usage' in data
    assert isinstance(data['bandwidth_usage'], int)

# Test API Key Validation (Unauthorized Access)
def test_unauthorized_access(client):
    response = client.get('/cpu')
    assert response.status_code == 401
    assert response.is_json
    json_data = response.get_json()
    assert 'Invalid API Key' in json_data.get('message', '')

