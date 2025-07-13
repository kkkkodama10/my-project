from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Pet(db.Model):
    __tablename__ = 'pets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    species = db.Column(db.String(30), nullable=False)
    sex = db.Column(db.Enum('male', 'female', 'unknown', name='sex_enum'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
