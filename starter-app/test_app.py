import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_health_ok_with_redis(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_visits_increments_in_redis(client):
    first = client.get("/visits").get_json()["visits"]
    second = client.get("/visits").get_json()["visits"]
    assert second == first + 1


def test_simulate_error_returns_500(client):
    assert client.get("/simulate-error").status_code == 500


def test_metrics_counts_requests(client):
    client.get("/status")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'http_requests_total{code="200",endpoint="/status",method="GET"}' in body
    assert "http_request_duration_seconds_bucket" in body
    assert "app_version_info" in body
