# Calendar, Tasks, Contacts Tool

This project provides an interactive command-line tool for managing list-based information like a calendar, a set of tasks, and a set of contacts in a virtual environment. This was created to help train AI on tool use by making various calls which you can simulate the responses in this fictional virtual world.  It has an environment of a calendar, tasks and contacts. Each calendar has events which include things such as the title, the date, the duration and an optional set of users on that event. The tasks have a title, description, when it's due, the current progress percentage and a type of state. The contacts contain common information you'd have for a contact such as first/last name, title, phone, email, etc. This isn't meant to be any sort of real way to setup these things, it's just a virtual environment for training AI on the use of tools.

## Project Structure

```text
CalTskCts
├── data
│   └── app.db
├── LICENSE
├── logging_config.json
├── logging_demo.py
├── logs
│   ├── calmsgcts.log
│   └── tasks.log
├── pytest.ini
├── README.md
├── requirements.txt
├── setup.py
├── src
│   └── caltskcts
│       ├── calendars.py
│       ├── config.py
│       ├── contacts.py
│       ├── __init__.py
│       ├── logger_config.py
│       ├── logger.py
│       ├── __main__.py
│       ├── state_manager.py
│       ├── tasks.py
│       └── validation_utils.py
├── templates
│   ├── _calendar.json
│   ├── _contacts.json
│   └── _tasks.json
└── tests
    ├── __init__.py
    ├── test_calendars_edge_cases.py
    ├── test_calendars.py
    ├── test_calendars_with_mocks.py
    ├── test_contacts_db_with_mocks.py
    ├── test_contacts_edge_cases.py
    ├── test_contacts.py
    ├── test_contacts_with_mocks.py
    ├── test_tasks.py
    └── test_tasks_with_mocks.py
```

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/<fictional>/CalTskCts.git
   cd CalTskCts
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:***

   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package (optional, for editable installs):**

   ```bash
   pip install -e .
   ```

## Setup Instructions

Before running the application, you can copy the template state files to create the actual state of your pseudo office administration environment, or you can just start running and do all the creation manually.

```bash
cp templates/_calendar.json _calendar.json
cp templates/_tasks.json _tasks.json
cp templates/_contacts.json _contacts.json
```

Or, if you want to use the DB component then you can copy the template DB from the templates directory.

```bash
cp templates/app.db data/app.db
```

## Running the Application

If you performed the `pip install -e .` above, then you can start the interactive command-line tool by running:

```bash
caltskcts
```

Otherwise, start the interactive command-line tool by running:

```bash
PYTHONPATH=src python -m caltskcts
```

Follow the on-screen instructions to enter commands.

## Running Tests

If you have `pytest` installed, run your tests with:

```bash
pytest
```

## Requirements

* Python 3.6 or higher
* (Optional) `pytest` for running tests

## License

MIT License
