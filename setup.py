from setuptools import setup, find_packages

setup(
    name="caltskcts",
    version="0.1.0",
    description="An interactive command-line tool for Calendar, Contacts, Tasks Management",
    author="Your Name",
    author_email="youremail@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "caltskcts = caltskcts.__main__:main",
        ],
    },
    install_requires=[
        "SQLAlchemy>=1.4",
        "pytest==8.3.4",
        "pytest-asyncio==0.25.3",
        "pytest-django==4.9.0",
        "psycopg[binary]"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
