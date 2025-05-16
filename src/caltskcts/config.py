import os

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "sqlite:///./data/app.db"
)