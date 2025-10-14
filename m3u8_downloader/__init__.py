from flask import Flask
from .extensions import db, scheduler, migrate
import os
def create_app(test_config=None):
    app=Flask(__name__,instance_relative_config=True) #创建Flask应用实例,instance_relative_config=True表示配置文件相对于实例文件夹
    if test_config is None:
        app.config.from_pyfile('../config.py',silent=True)
    else:
        app.config.from_mapping(test_config)
    # APScheduler 基本配置（可选）
    app.config.setdefault('SCHEDULER_API_ENABLED', False)
    app.config.setdefault('SCHEDULER_TIMEZONE', 'Asia/Shanghai')
    db.init_app(app)
    migrate.init_app(app, db)
    scheduler.init_app(app)
    # 确保任务注册：导入 schedulers 模块（不要删除）
    from . import schedulers  # noqa: F401
    # 仅在主进程启动调度器，避免 Flask 调试模式下重启导致的重复或不启动问题
    is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    if (app.debug and is_reloader_child) or (not app.debug):
        if scheduler.state == 0:
            scheduler.start()
            print('[APScheduler] started')
            try:
                jobs = [job.id for job in scheduler.get_jobs()]
                print('[APScheduler] jobs:', jobs)
            except Exception as _e:
                pass
    register_blueprints(app)
    with app.app_context():
        db.create_all()
    return app
def register_blueprints(app):
    from .task import task_bp
    app.register_blueprint(task_bp,url_prefix='/tasks')

