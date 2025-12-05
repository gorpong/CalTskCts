# Calendar, Tasks, Contacts Tool

This project provides an interactive command-line tool for managing list-based information like a calendar, a set of tasks, and a set of contacts in a virtual environment. This was created to help train AI on tool use by making various calls which you can simulate the responses in this fictional virtual world.  It has an environment of a calendar, tasks and contacts. Each calendar has events which include things such as the title, the date, the duration and an optional set of users on that event. The tasks have a title, description, when it's due, the current progress percentage and a type of state. The contacts contain common information you'd have for a contact such as first/last name, title, phone, email, etc. This isn't meant to be any sort of real way to setup these things, it's just a virtual environment for training AI on the use of tools.

## Project Structure

```text
CalTskCts/
├── data
│   └── app.db
├── frontend
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── src
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── index.jsx
│   │   └── main.jsx
│   ├── tailwind.config.js
│   └── vite.config.js
├── LICENSE
├── logging_config.json
├── logging_demo.py
├── logs
│   ├── caltskcts.log
│   └── tasks.log
├── pytest.ini
├── README.md
├── requirements.txt
├── scripts
│   └── build_db.py
├── setup.py
├── src
│   └── caltskcts
│       ├── api.py
│       ├── calendars.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── contacts.py
│       ├── dispatch_utils.py
│       ├── import_export.py
│       ├── __init__.py
│       ├── logger_config.py
│       ├── logger.py
│       ├── __main__.py
│       ├── schemas.py
│       ├── state_manager.py
│       ├── tasks.py
│       └── templates
│           └── index.html
├── templates
│   ├── app.db
│   ├── _calendar.json
│   ├── _contacts.json
│   └── _tasks.json
└── tests
    ├── __init__.py
    ├── test_api.py
    ├── test_calendars.py
    ├── test_cli_flags.py
    ├── test_cli.py
    ├── test_contacts.py
    ├── test_db_persistence.py
    ├── test_import_export.py
    ├── test_main.py
    ├── test_statefile_lock.py
    ├── test_statefile_persistence.py
    └── test_tasks.py
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

3. **Install dependencies:**

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

### Optional Command Line Arguments

```text
usage: caltskcts [-h] [-f | -db [DATABASE]]

Calendar, Tasks, and Contacts Manager

options:
  -h, --help            show this help message and exit
  -f, --files           Use JSON files for state storage (default)
  -db [DATABASE], --database [DATABASE]
                        Use SQLite database for state storage (optional path; defaults to config.DATABASE_URI [data/app.db])
```

Follow the on-screen instructions to enter commands.

## Running Tests

If you have `pytest` installed, run your tests with:

```bash
pytest
```
## Running a Docker Container

If you want to build this into a docker container, and a Dockerfile exists where you got this code from, then you should build it appropriately and then you can run it via:

```bash
docker run -it <imagename> caltskcts <arguments, see above>
```

That will launch the docker container that had the `pip install -e .` already done as part of the `docker build` step.

### Running the CLI in the Docker Container

The Docker container doesn't save state in the current configuration unless you map a directory, so everything you do has to be checked within the same instance. Given that, you have a couple of ways to run the CLI components:  (1) run the interactive command interpreter; (2) use the CLI components to just to get information, (3) use the CLI components interactively so you can get, change, review, etc.  Note that with #2, it's ephemeral, so as soon as you stop the container, the state resets.

1. Run as interactive command intepreter:

```bash
docker run -it <imagename> caltskcts [optional -f, -db]
```

2. Run a single CLI command (e.g., for listing things):

```bash
docker run -it <imagename> caltskcts cal list_events
```

3. Run a shell interactively to use CLI commands:

```bash
docker run -it <imagename> sh
caltskcts cal add_event --title "This is a new one" --date "11/15/2014 10:00" --duration 45
caltskcts cal list_events
...
```

## Running the Flask API in a Docker Container

If you want to run the Flask API app in a docker container and be able to hit it with a web browser, you can run this:

```bash
docker run -e STATE_URI="sqlite:////app/data/app.db" --network=host caltskc-api flask run
```

This will launch it using the built-in copy of the templates database and it will start listening on port 5000. You can then connect your web browser to http://localhost:5000/contacts to look at the contacts, and similarly for /tasks and /calendars.

## Requirements

* Python 3.6 or higher
* (Optional) `pytest` for running tests

## License

MIT License
