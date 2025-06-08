import os
import pytest
from api import create_app

@pytest.fixture
def app(tmp_path, monkeypatch):
    # each test gets its own SQLite file
    dbfile = tmp_path / "test.db"
    uri    = f"sqlite:///{dbfile}"
    monkeypatch.setenv("STATE_URI", uri)

    app = create_app()
    app.config.update(TESTING=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_contacts_crud(client):
    # list is empty
    rv = client.get("/contacts")
    assert rv.status_code == 200
    assert rv.get_json() == {}

    # create
    payload = {"first_name":"Alice","last_name":"Wonder","email":"a@b.com"}
    rv = client.post("/contacts", json=payload)
    assert rv.status_code == 201
    data = rv.get_json()
    cid  = data["id"]

    # read
    rv = client.get(f"/contacts/{cid}")
    assert rv.status_code == 200
    contact = rv.get_json()
    assert contact["first_name"] == "Alice"
    assert contact["email"] == "a@b.com"

    # update
    rv = client.put(f"/contacts/{cid}", json={"company":"QA Inc."})
    assert rv.status_code == 200
    assert "updated" in rv.get_json()["message"].lower()
    rv = client.get(f"/contacts/{cid}")
    assert rv.get_json()["company"] == "QA Inc."

    # delete
    rv = client.delete(f"/contacts/{cid}")
    assert rv.status_code == 200
    assert "deleted" in rv.get_json()["message"].lower()
    rv = client.get(f"/contacts/{cid}")
    assert rv.status_code == 404

def test_events_crud(client):
    # list empty
    rv = client.get("/events")
    assert rv.status_code == 200
    assert rv.get_json() == {}

    # create
    evt = {
        "title":"Meeting",
        "date":"06/10/2025 14:00",
        "duration":30,
        "users":["Alice","Bob"]
    }
    rv = client.post("/events", json=evt)
    assert rv.status_code == 201
    eid = rv.get_json()["id"]

    # read
    rv = client.get(f"/events/{eid}")
    assert rv.status_code == 200
    e = rv.get_json()
    assert e["title"] == "Meeting"
    assert e["duration"] == 30

    # update
    rv = client.put(f"/events/{eid}", json={"duration":45})
    assert rv.status_code == 200
    assert "updated" in rv.get_json()["message"].lower()
    rv = client.get(f"/events/{eid}")
    assert rv.get_json()["duration"] == 45

    # delete
    rv = client.delete(f"/events/{eid}")
    assert rv.status_code == 200
    rv = client.get(f"/events/{eid}")
    assert rv.status_code == 404

def test_tasks_crud(client):
    # list empty
    rv = client.get("/tasks")
    assert rv.status_code == 200
    assert rv.get_json() == {}

    # create
    task = {
        "title":"New Task",
        "description":"Do something",
        "due_date":"06/15/2025",
        "progress":0,
        "state":"Not Started"
    }
    rv = client.post("/tasks", json=task)
    assert rv.status_code == 201
    tid = rv.get_json()["id"]

    # read
    rv = client.get(f"/tasks/{tid}")
    assert rv.status_code == 200
    t = rv.get_json()
    assert t["title"] == "New Task"
    assert t["progress"] == 0

    # update
    rv = client.put(f"/tasks/{tid}", json={"progress":100})
    assert rv.status_code == 200
    # confirmed progress=100 auto-flips state
    rv = client.get(f"/tasks/{tid}")
    t = rv.get_json()
    assert t["progress"] == 100
    assert t["state"] == "Completed"

    # delete
    rv = client.delete(f"/tasks/{tid}")
    assert rv.status_code == 200
    rv = client.get(f"/tasks/{tid}")
    assert rv.status_code == 404

def test_invalid_payloads(client):
    # missing required for contact
    rv = client.post("/contacts", json={"first_name":"X"})
    assert rv.status_code == 400

    # bad date for event
    rv = client.post("/events", json={
        "title":"X","date":"2025-06-15","duration":30,"users":["A"]
    })
    assert rv.status_code == 400

    # bad state for task
    rv = client.post("/tasks", json={
        "title":"X","description":"X","due_date":"06/20/2025","progress":50,"state":"BAD"
    })
    assert rv.status_code == 400
