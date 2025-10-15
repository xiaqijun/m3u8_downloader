from flask import Blueprint, request, jsonify, render_template
from .models import Task, Segment
from .extensions import db,scheduler
import requests
import os
from datetime import datetime, timedelta
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
    # 初始状态统一为 '等待解析'
    new_task = Task(name=data['name'], url=data['url'], status='等待解析')
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Task created", "task_id": new_task.id}), 201

@task_bp.route('/download/<int:task_id>', methods=['POST'])
def download_task(task_id):
    task = Task.query.get(task_id)
    segment=Segment.query.filter_by(task_id=task_id, downloaded=True)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    # 允许下载的前置状态应为 '解析完成'
    if task.segments.downloaded.count() == 0:
        return jsonify({"error": "Task not ready for download", "current_status": task.status}), 400
    # 使用本地时间（与配置 Asia/Shanghai 保持一致）
    run_at = datetime.now() + timedelta(seconds=1)
    job_id = f"download_task_{task.id}"
    print(f"[DownloadSchedule] 添加任务 job_id={job_id} run_at={run_at.isoformat()} task_id={task.id}")
    scheduler.add_job(
        func=download_segments,
        args=[task.id],
        id=job_id,
        replace_existing=True,
        trigger='date',
    )
    task.status = '下载中'
    db.session.commit()
    return jsonify({"message": f"Download scheduled for task {task_id}", "job_id": job_id}), 200


def download_segments(task_id):
    print(f"[DownloadWorker] 准备下载 任务ID={task_id}")
    with scheduler.app.app_context():
        task = Task.query.get(task_id)
        if not task:
            print(f"[DownloadWorker] 任务 {task_id} 不存在，终止。")
            return
        if task.status not in ['下载中', '解析完成']:
            print(f"[DownloadWorker] 警告：任务当前状态为 {task.status}，仍继续执行。")
        print(f"[DownloadWorker] 开始下载 任务 {task.id} - {task.name}")
        # 查询未下载分片
        segments = Segment.query.filter_by(task_id=task.id, downloaded=False).order_by(Segment.sequence.asc()).all()
        print(f"[DownloadWorker] 未下载分片数量: {len(segments)}")
        if not segments:
            task.status = '下载完成'
            db.session.commit()
            print(f"[DownloadWorker] 无需下载，直接标记完成。")
            return
        base_dir = os.path.join('tmp/downloads', f'task_{task.id}')
        os.makedirs(base_dir, exist_ok=True)
        for segment in segments:
            print(f"[DownloadWorker] 下载分片 seq={segment.sequence} uri={segment.uri}")
            try:
                response = requests.get(segment.uri, timeout=15)
                response.raise_for_status()
                segment_path = os.path.join(base_dir, f'segment_{segment.sequence}.ts')
                with open(segment_path, 'wb') as f:
                    f.write(response.content)
                segment.downloaded = True
                db.session.commit()
                print(f"[DownloadWorker] 分片 {segment.sequence} 成功")
            except Exception as e:
                print(f"[DownloadWorker] 分片 {segment.sequence} 失败: {e}")
                continue
        # 检查是否全部完成
        remaining = Segment.query.filter_by(task_id=task.id, downloaded=False).count()
        if remaining == 0:
            task.status = '下载完成'
        else:
            task.status = f'部分完成(剩余{remaining})'
        db.session.commit()
        print(f"[DownloadWorker] 任务 {task.id} 完成状态: {task.status}")
    
@task_bp.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200