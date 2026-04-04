import os


class Config:
    # Use an environment variable for security, with a fallback
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'

    # Get the database URL from the environment, or use local SQLite
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///vocab.db')

    # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False