from setuptools import setup, find_packages

setup(
    name="server-admin-tool",
    version="0.1.0",
    description="An interactive command-line tool for server administration including disk, process, and ticket management.",
    author="Your Name",
    author_email="youremail@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "srvadmin=main:main",
        ],
    },
    install_requires=[
        # This project uses only the standard library.
        # Add any external packages here if needed.
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
