from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, default=datetime.utcnow)
    tag = db.Column(db.String(50))
    completed = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    directory_id = db.Column(db.Integer, db.ForeignKey('directory.id'), nullable=True)

class Directory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    todos = db.relationship('Todo', backref='directory', lazy=True)