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

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    uri = db.Column(db.String(256), nullable=False)
    duration = db.Column(db.Float, nullable=False) #
    sequence = db.Column(db.Integer, nullable=False)
    downloaded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    task = db.relationship('Task', backref=db.backref('segments', lazy=True))
    def __repr__(self):
        return f'<Segment {self.uri} - Downloaded: {self.downloaded}>'