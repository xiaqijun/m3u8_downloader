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
    return render_template('task/index.html', response_data=response_data)

@task_bp.route('/create', methods=['POST'])
def create_task():
    data = request.json
    if not data or 'name' not in data or 'url' not in data:
        return jsonify({"error": "Invalid input"}), 400
    new_task = Task(name=data['name'], url=data['url'], status='等待中')
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Task created", "task_id": new_task.id}), 201
