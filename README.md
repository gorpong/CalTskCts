# Calendar, Tasks, Contacts Tool

This project provides an interactive command-line tool for managing list-based information like a calendar, a set of tasks, and a set of contacts in a virtual environment. This was created to help train AI on tool use by making various calls which you can simulate the responses in this fictional virtual world.  It has and environment of a calendar, tasks and contacts. Each calendar has events which include things such as the title, the date, the duration and an optional set of users on that event. The tasks have a title, description, when it's due, the current progress percentage and a type of state. The contacts contain common information you'd have for a contact such as first/last name, title, phone, email, etc. This isn't meant to be any sort of real way to setup these things, it's just a virtual environment for training AI on the use of tools.

## Project Structure

```text
my_project/
├── README.md
├── setup.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── calendar.py
│   ├── tasks.py
│   ├── contacts.py
│   ├── utils.py
│   └── main.py
└── tests/
    ├── __init__.py
    ├── test_calendar.py
    ├── test_tasks.py
    ├── test_contacts.py
```

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
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

Before running the application, you can copy the template state files to create the actual state of your pseudo server administration environment, or you can just start running and do all the creation manually.

```bash
cp templates/_calendar.json _calendar.json
cp templates/_tasks.json _tasks.json
cp templates/_contacts.json _contacts.json
```

## Running the Application

Start the interactive command-line tool by running:

```bash
python -m src.main
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
