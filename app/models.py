from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin

db = SQLAlchemy()
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Game + progress
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    current_streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    topic = db.relationship('Topic', backref='owner', lazy=True)
    words = db.relationship('Word', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.username} - Level {self.level}>'

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    words = db.relationship('Word', backref='topic_category', lazy=True)

    def __repr__(self):
        return f'<Topic {self.name}>'

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)

    topic = db.Column(db.String(50), nullable=False, default='general')
    term = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    example_sentence = db.Column(db.Text)
    synonyms = db.Column(db.String(200))
    antonyms = db.Column(db.String(200))

    # Spaced Repetition System de nhac nho nguoi dung
    times_tested = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    is_mastered = db.Column(db.Boolean, default=False)
    date_mastered = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Word {self.term}>'