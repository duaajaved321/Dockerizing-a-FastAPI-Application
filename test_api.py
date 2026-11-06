"""API tests using an isolated temporary SQLite database."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "get_connection", lambda: sqlite3.connect(db_path))
    database.create_table()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_vitals():
    return {
        "patient_id": "P001",
        "age": 25,
        "blood_pressure": {"systolic": 120, "diastolic": 80},
        "glucose_level": 95,
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()


def test_save_vitals(client, valid_vitals):
    response = client.post("/vitals", json=valid_vitals)
    assert response.status_code == 200
    assert response.json()["message"] == "Vitals saved successfully"


def test_patient_history_and_limit(client, valid_vitals):
    client.post("/vitals", json=valid_vitals)
    client.post("/vitals", json={**valid_vitals, "glucose_level": 105})
    response = client.get("/patients/P001/vitals")
    assert response.status_code == 200
    assert len(response.json()) == 2
    limited = client.get("/patients/P001/vitals?limit=1")
    assert limited.status_code == 200
    assert len(limited.json()) == 1


def test_patient_summary(client, valid_vitals):
    client.post("/vitals", json=valid_vitals)
    second = {
        **valid_vitals,
        "blood_pressure": {"systolic": 130, "diastolic": 90},
        "glucose_level": 105,
    }
    client.post("/vitals", json=second)
    summary = client.get("/patients/P001/summary").json()
    assert summary["total_records"] == 2
    assert summary["avg_systolic"] == 125
    assert summary["avg_diastolic"] == 85
    assert summary["avg_glucose"] == 100


@pytest.mark.parametrize(
    "field,value",
    [
        ("age", -1), ("age", 121), ("age", "twenty"),
        ("patient_id", ""), ("patient_id", "   "),
        ("glucose_level", 0), ("glucose_level", -5), ("glucose_level", "95"),
    ],
)
def test_invalid_fields(client, valid_vitals, field, value):
    response = client.post("/vitals", json={**valid_vitals, field: value})
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("systolic", 49), ("systolic", 301), ("systolic", "120"),
        ("diastolic", 29), ("diastolic", 201), ("diastolic", "80"),
    ],
)
def test_invalid_blood_pressure(client, valid_vitals, field, value):
    payload = {
        **valid_vitals,
        "blood_pressure": {**valid_vitals["blood_pressure"], field: value},
    }
    response = client.post("/vitals", json=payload)
    assert response.status_code == 400


def test_missing_patient_id(client, valid_vitals):
    payload = {**valid_vitals}
    del payload["patient_id"]
    response = client.post("/vitals", json=payload)
    assert response.status_code == 400


def test_empty_patient_summary(client):
    summary = client.get("/patients/unknown/summary").json()
    assert summary["total_records"] == 0
    assert summary["avg_systolic"] is None
