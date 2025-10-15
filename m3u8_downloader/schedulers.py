from datetime import datetime, timezone
import m3u8
from .extensions import scheduler, db
from .models import Segment, Task
from .ffmpeg_update import update_ffmpeg
import urllib.parse
@scheduler.task(
    'interval',
    id='start_downloader',
    seconds=30,
    misfire_grace_time=900,
    max_instances=1,
    next_run_time=datetime.now(timezone.utc),
)
def start_downloader():
    """定时任务：解析 M3U8 分片"""
    with scheduler.app.app_context():
        try:
            pending_task = Task.query.filter_by(status='等待解析').first()
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
                pending_task.status = '解析完成'
                db.session.commit()
                print(f"任务 {pending_task.name} 分片解析完成, 共 {len(segment_list)} 个分片")
            except Exception as exc:
                print(f"解析分片失败: {exc}")
                pending_task.status = '失败'
                db.session.commit()
        except Exception as exc:
            # 避免任务抛异常导致调度器静默失败
            print(f"分片解析任务执行失败: {exc}")

def abs_url(base, uri):
    return urllib.parse.urljoin(base, uri)

def get_segments(URL):
    playlist = m3u8.load(URL)
    segments = []
    # 如果是多码率主列表
    if playlist.playlists:
        for sub in playlist.playlists:
            sub_url = abs_url(URL, sub.uri)
            sub_playlist = m3u8.load(sub_url)
            for i, segment in enumerate(sub_playlist.segments):
                segments.append({
                    'uri': abs_url(sub_url, segment.uri),
                    'duration': segment.duration,
                    'sequence': i
                })
    else:
        for i, segment in enumerate(playlist.segments):
            segments.append({
                'uri': abs_url(URL, segment.uri),
                'duration': segment.duration,
                'sequence': i
            })
    return segments

@scheduler.task(
    'interval',
    id='update_ffmpeg_task',
    hours=24,
    misfire_grace_time=3600,
    max_instances=1,
    next_run_time=datetime.now(timezone.utc),
)
def update_ffmpeg_task():
    """定时任务：每天更新一次 FFmpeg"""
    with scheduler.app.app_context():
        try:
            print("正在检查并更新 FFmpeg...")
            ffmpeg_path = update_ffmpeg()
            print(f"FFmpeg 更新完成，路径: {ffmpeg_path}")
        except Exception as exc:
            print(f"FFmpeg 更新失败: {exc}")