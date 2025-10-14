from .extensions import scheduler, db
from .models import Task, Segment
import m3u8
@scheduler.task('interval', id='start_downloader', seconds=5000)
def start_downloader():
    with scheduler.app.app_context():
        pending_tasks = Task.query.filter_by(status='等待中').first()
        if not pending_tasks:
            print("正在执行分片解析任务, 任务名称: 无待处理任务")
            return
        print("正在执行分片解析任务, 任务名称:", pending_tasks.name)
        try:
            segment_list = get_segments(pending_tasks.url)
            print(segment_list)
        except Exception as e:
            # 避免任务抛异常导致调度器静默失败
            print("获取分片失败:", e)
            return
def get_segments(URL):
    playlist = m3u8.load(URL)
    segments = []
    for i, segment in enumerate(playlist.segments):
        segments.append({
            'uri': segment.uri,
            'duration': segment.duration,
            'sequence': i
        })
        print(segment.uri)
    return segments