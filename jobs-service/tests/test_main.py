import os

os.environ["DATABASE_URL"] = "sqlite:///./test_jobs.db"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_jobs_secess():
    job_data = {
        "title": "Test Job",
        "description": "Testing the functionality",
        "company": "Test Comp",
        "location": "Canada",
        "salary_range": "100-150"
    }
    
    response = client.post("/jobs", json=job_data)
    assert response.status_code == 201

    body = response.json()
    assert body["title"] == job_data["title"]
    assert "id" in body
    assert "created_at" in body

def test_jobs_fail():
    incomplete_job_data = {
        "title": "Test Job",
        "description": "Testing the functionality",
        "location": "Canada"
    }
    
    response = client.post("/jobs", json=incomplete_job_data)
    assert response.status_code == 422

def test_non_existent_ID():
    missing_id = "this-job-does-not-exist"
    response = client.get(f"/jobs/{missing_id}")
    assert response.status_code == 404