from flask import Flask
from .extensions import db,scheduler,migrate
def create_app(test_config=None):
    app=Flask(__name__,instance_relative_config=True) #创建Flask应用实例,instance_relative_config=True表示配置文件相对于实例文件夹
    if test_config is None:
        app.config.from_pyfile('../config.py',silent=True)
    else:
        app.config.from_mapping(test_config)
    db.init_app(app)
    migrate.init_app(app,db)
    scheduler.init_app(app)
    if scheduler.state == 0:
        scheduler.start()
    register_blueprints(app)
    with app.app_context():
        db.create_all()
    return app

def register_blueprints(app):
    from .task import task_bp
    app.register_blueprint(task_bp,url_prefix='/tasks')