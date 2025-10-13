from .extensions import db
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(64), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    def __repr__(self):
        return f'<Task {self.name} - {self.status}>'