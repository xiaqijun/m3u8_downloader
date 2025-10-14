from datetime import datetime, timezone
import m3u8
from .extensions import scheduler, db
from .models import Segment, Task


@scheduler.task(
    'interval',
    id='start_downloader',
    seconds=120,
    misfire_grace_time=900,
    max_instances=1,
    next_run_time=datetime.now(timezone.utc),
)
def start_downloader():
    """定时任务：解析 M3U8 分片"""
    with scheduler.app.app_context():
        try:
            pending_task = Task.query.filter_by(status='等待中').first()
            if not pending_task:
                print("正在执行分片解析任务, 任务名称: 无待处理任务")
                return

            print("正在执行分片解析任务, 任务名称:", pending_task.name)
            try:
                segment_list = get_segments(pending_task.url)
                for seg in segment_list:
                    existing_segment = Segment.query.filter_by(
                        task_id=pending_task.id,
                        uri=seg['uri'],
                    ).first()
                    if not existing_segment:
                        new_segment = Segment(
                            task_id=pending_task.id,
                            uri=seg['uri'],
                            duration=seg['duration'],
                            sequence=seg['sequence'],
                            downloaded=False,
                        )
                        db.session.add(new_segment)
                pending_task.status = '下载中'
                db.session.commit()
                print(f"任务 {pending_task.name} 分片解析完成, 共 {len(segment_list)} 个分片")
            except Exception as exc:
                print(f"解析分片失败: {exc}")
                pending_task.status = '失败'
                db.session.commit()
        except Exception as exc:
            # 避免任务抛异常导致调度器静默失败
            print(f"分片解析任务执行失败: {exc}")


def get_segments(url: str):
    playlist = m3u8.load(url)
    segments = []
    for index, segment in enumerate(playlist.segments):
        segments.append({
            'uri': segment.uri,
            'duration': segment.duration,
            'sequence': index,
        })
    return segments
