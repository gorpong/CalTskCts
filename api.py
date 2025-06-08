import os
from flask import Flask, jsonify, request, abort
from caltskcts.contacts import Contacts
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks

def create_app():
    app = Flask(__name__)

    # read from env or fall back to JSON files
    state_uri = os.getenv("STATE_URI", "sqlite:///:memory:")

    # instantiate one manager of each type
    contacts = Contacts(state_uri)
    cal      = Calendar(state_uri)
    tasks    = Tasks(state_uri)

    @app.route("/contacts", methods=["GET"])
    def list_contacts():
        return jsonify(contacts.list_items()), 200

    @app.route("/contacts/<int:cid>", methods=["GET"])
    def get_contact(cid):
        c = contacts.get_contact(cid)
        if not c:
            abort(404)
        return jsonify(c), 200

    @app.route("/contacts", methods=["POST"])
    def add_contact():
        payload = request.get_json() or {}
        cid = contacts._get_next_id()
        try:
            contacts.add_contact(contact_id=cid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"id": cid}), 201

    @app.route("/contacts/<int:cid>", methods=["PUT"])
    def update_contact(cid):
        payload = request.get_json() or {}
        try:
            msg = contacts.update_contact(cid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route("/contacts/<int:cid>", methods=["DELETE"])
    def delete_contact(cid):
        try:
            msg = contacts.delete_contact(cid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route("/events", methods=["GET"])
    def list_events():
        return jsonify(cal.list_items()), 200

    @app.route("/events/<int:eid>", methods=["GET"])
    def get_event(eid):
        c = cal.get_event(eid)
        if not c:
            abort(404)
        return jsonify(c), 200

    @app.route("/events", methods=["POST"])
    def add_event():
        payload = request.get_json() or {}
        eid = cal._get_next_id()
        try:
            cal.add_event(event_id=eid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"id": eid}), 201

    @app.route("/events/<int:eid>", methods=["PUT"])
    def update_event(eid):
        payload = request.get_json() or {}
        try:
            msg = cal.update_event(eid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route("/events/<int:eid>", methods=["DELETE"])
    def delete_event(eid):
        try:
            msg = cal.delete_event(eid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route("/tasks", methods=["GET"])
    def list_tasks():
        return jsonify(tasks.list_items()), 200

    @app.route("/tasks/<int:tid>", methods=["GET"])
    def get_task(tid):
        c = tasks.get_task(tid)
        if not c:
            abort(404)
        return jsonify(c), 200

    @app.route("/tasks", methods=["POST"])
    def add_task():
        payload = request.get_json() or {}
        tid = tasks._get_next_id()
        try:
            tasks.add_task(task_id=tid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"id": tid}), 201

    @app.route("/tasks/<int:tid>", methods=["PUT"])
    def update_task(tid):
        payload = request.get_json() or {}
        try:
            msg = tasks.update_task(tid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route("/tasks/<int:tid>", methods=["DELETE"])
    def delete_task(tid):
        try:
            msg = tasks.delete_task(tid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
