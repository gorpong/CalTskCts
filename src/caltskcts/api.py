import os
import re
from flask import Flask, jsonify, request, abort, send_from_directory
from caltskcts.contacts import Contacts
from caltskcts.calendars import Calendar
from caltskcts.tasks import Tasks
from caltskcts.config import get_database_uri

def create_app():
    # Get the directory where this file lives
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'static')
    
    app = Flask(__name__, static_folder=static_dir, static_url_path='')

    # read from env or fall back to JSON files
    state_uri = get_database_uri()

    if state_uri:
        cal_uri = ctc_uri = tsk_uri = state_uri
    else:
        cal_uri = get_calendar_uri()
        ctc_uri = get_contacts_uri()
        tsk_uri = get_tasks_uri()
        
    # instantiate one manager of each type
    contacts = Contacts(ctc_uri)
    cal      = Calendar(cal_uri)
    tasks    = Tasks(tsk_uri)

    # ===== Helper Method ==========
    def _extract_id(msg: str) -> int:
        """
        Pulls the first integer out of a string like "Task 5 added".
        Raises ValueError if none found.
        """
        m = re.search(r"\b(\d+)\b", msg)
        if not m:
            raise ValueError(f"Could not parse ID from message: {msg!r}")
        return int(m.group(1))

    # ===== FRONTEND ROUTES =====

    @app.route("/")
    def serve_frontend():
        """Serve the main frontend application"""
        return send_from_directory(static_dir, 'index.html')

    @app.route("/<path:path>")
    def serve_static(path):
        """Serve static files, fallback to index.html for SPA routing"""
        if os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, 'index.html')

    # ===== CONTACTS ENDPOINTS =====

    @app.route("/contacts", methods=["GET"])
    def get_contacts():
        """Get all contacts or search contacts"""
        search_query = request.args.get('q')
        if search_query:
            return jsonify(contacts.search_contacts(search_query))
        return jsonify(contacts.list_contacts()), 200

    @app.route("/contacts/<int:cid>", methods=["GET"])
    def get_contact(cid):
        """Get a specific contact by ID"""
        c = contacts.get_contact(cid)
        if not c:
            abort(404, description=f"Contact with ID {cid} not found")
        return jsonify(c), 200

    @app.route("/contacts", methods=["POST"])
    def add_contact():
        """Add a new contact"""
        payload = request.get_json() or {}
        try:
            msg = contacts.add_contact(**payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            cid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": cid, "message": msg}), 201

    @app.route("/contacts/<int:cid>", methods=["PUT"])
    def update_contact(cid):
        """Update an existing contact"""
        payload = request.get_json() or {}
        try:
            msg = contacts.update_contact(cid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            cid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": cid, "message": msg}), 200

    @app.route("/contacts/<int:cid>", methods=["DELETE"])
    def delete_contact(cid):
        """Delete a contact"""
        try:
            msg = contacts.delete_contact(cid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            cid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": cid, "message": msg}), 200

    # ===== CALENDAR ENDPOINTS =====

    @app.route("/events", methods=["GET"])
    def get_events():
        """Get all events or events by date range (e.g., ?start=10/01/2023 09:00&end=10/31/2023 23:59)
           Get all events by date (e.g., ?date=10/01/2023)
        """
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        date = request.args.get('date')
        
        if start_date and end_date:
            return jsonify(cal.get_events_between(start_date, end_date))
        elif date:
            return jsonify(cal.get_events_by_date(date))
        return jsonify(cal.list_items()), 200

    @app.route("/events/<int:eid>", methods=["GET"])
    def get_event(eid):
        """Get a specific event by ID"""
        event = cal.get_event(eid)
        if not event:
            abort(404, description=f"Event with ID {eid} not found")
        return jsonify(event), 200

    @app.route("/events", methods=["POST"])
    def add_event():
        """Add a new event"""
        payload = request.get_json() or {}
        try:
            msg = cal.add_event(**payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            eid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": eid, "message": msg}), 201

    @app.route("/events/<int:eid>", methods=["PUT"])
    def update_event(eid):
        """Update an existing event"""
        payload = request.get_json() or {}
        try:
            msg = cal.update_event(eid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            eid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": eid, "message": msg}), 200

    @app.route("/events/<int:eid>", methods=["DELETE"])
    def delete_event(eid):
        """Delete an event"""
        try:
            msg = cal.delete_event(eid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"message": msg}), 200

    @app.route('/events/next-available', methods=['GET'])
    def find_next_available():
        """Find next available time slot"""
        start_datetime = request.args.get('start')
        duration = request.args.get('duration')
        try:
            duration = int(duration)
            result = cal.find_next_available(start_datetime, duration)
            return jsonify({"available_time": result})
        except (ValueError, TypeError) as e:
            abort(400, description=str(e))

    # ===== TASKS ENDPOINTS =====

    @app.route("/tasks", methods=["GET"])
    def get_tasks():
        """Get all tasks or filter by various criteria"""
        due_date = request.args.get('due_date')
        due_on_or_before = request.args.get('due_on_or_before')
        state = request.args.get('state')
        min_progress = request.args.get('min_progress')
        max_progress = request.args.get('max_progress')
        
        if due_date == 'today':
            return jsonify(tasks.get_tasks_due_today())
        elif due_date:
            return jsonify(tasks.get_tasks_due_on(due_date))
        elif due_on_or_before:
            return jsonify(tasks.get_tasks_due_on_or_before(due_on_or_before))
        elif state:
            return jsonify(tasks.get_tasks_by_state(state))
        elif min_progress or max_progress:
            min_p = float(min_progress) if min_progress else 0.0
            max_p = float(max_progress) if max_progress else 100.0
            return jsonify(tasks.get_tasks_with_progress(min_p, max_p))
        return jsonify(tasks.list_tasks())

    @app.route("/tasks/<int:tid>", methods=["GET"])
    def get_task(tid):
        """Get a specific task by ID"""
        t = tasks.get_task(tid)
        if not t:
            abort(404, description=f"Task with ID {tid} not found")
        return jsonify(t), 200

    @app.route("/tasks", methods=["POST"])
    def add_task():
        """Add a new task"""
        payload = request.get_json() or {}
        try:
            msg = tasks.add_task(**payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            tid = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"id": tid}), 201

    @app.route("/tasks/<int:tid>", methods=["PUT"])
    def update_task(tid):
        """Update an existing task"""
        payload = request.get_json() or {}
        try:
            msg = tasks.update_task(tid, **payload)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            id = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"id": id, "message": msg}), 200

    @app.route("/tasks/<int:tid>", methods=["DELETE"])
    def delete_task(tid):
        """Delete a task"""
        try:
            msg = tasks.delete_task(tid)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        try:
            id = _extract_id(msg)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify({"id": id, "message": msg}), 200

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
