from flask import Blueprint, request, jsonify,render_template
from .models import Task
from .extensions import db
task_bp = Blueprint('task', __name__)
@task_bp.route('/', methods=['GET'])
def tasks_index():
    page=request.args.get("page",1,type=int)
    per_page=request.args.get("per_page",10,type=int)
    filters = {}
    if request.args:
        for key in ["name", "status", "url"]:
            value = request.args.get(key)
            if value is not None:
                filters[key] = value
    query = Task.query.filter_by(**filters)
    tasks = query.paginate(page=page, per_page=per_page, error_out=False).items
    response_data={
        "tasks":[
            {
                "id":task.id,
                "name":task.name,
                "url":task.url,
                "status":task.status,
                "created_at":task.created_at,
                "updated_at":task.updated_at
            } for task in tasks
        ],
        "page":page,
        "per_page":per_page,
        "total":len(tasks)
    }
    return render_template('task/index.html', tasks=response_data)
