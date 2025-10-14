import os
import platform
import requests
import shutil
import zipfile
import tarfile


GITHUB_API = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"


def detect_system():
    """识别系统和架构"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system.startswith("win"):
        os_name = "win"
    elif system.startswith("linux"):
        os_name = "linux"
    elif system.startswith("darwin"):
        os_name = "macos"
    else:
        raise RuntimeError(f"不支持的系统: {system}")

    if "arm" in machine or "aarch64" in machine:
        arch = "arm64"
    elif "64" in machine or "x86_64" in machine or "amd64" in machine:
        arch = "64"
    else:
        arch = "32"

    return os_name, arch


def get_latest_asset_url(os_name, arch, prefer="gpl-shared"):
    """从 GitHub Release 中查找匹配的下载链接"""
    response = requests.get(GITHUB_API, timeout=15)
    response.raise_for_status()
    data = response.json()

    assets = data.get("assets", [])
    for asset in assets:
        name = asset["name"].lower()
        if os_name in name and arch in name and prefer in name:
            return asset["browser_download_url"], asset["name"]

    raise RuntimeError(f"未找到匹配的 ffmpeg 版本: {os_name}-{arch}")


def extract_archive(filepath, target_dir):
    """自动识别压缩包类型并解压"""
    if filepath.endswith(".zip"):
        with zipfile.ZipFile(filepath, "r") as zf:
            zf.extractall(target_dir)
    elif filepath.endswith(".tar.xz"):
        with tarfile.open(filepath, "r:xz") as tf:
            tf.extractall(target_dir)
    elif filepath.endswith(".tar.gz"):
        with tarfile.open(filepath, "r:gz") as tf:
            tf.extractall(target_dir)
    else:
        raise RuntimeError(f"未知的压缩格式: {filepath}")

    # 统一重命名解压后的 FFmpeg 文件夹为 ffmpeg_bin
    subdirs = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]
    if len(subdirs) == 1:
        src = os.path.join(target_dir, subdirs[0])
        dst = os.path.join(target_dir, "ffmpeg_bin")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.rename(src, dst)


def update_ffmpeg():
    """
    自动下载并更新 FFmpeg 到 tmp/ffmpeg 目录。
    """
    os_name, arch = detect_system()
    print(f"检测到系统: {os_name}, 架构: {arch}")

    url, filename = get_latest_asset_url(os_name, arch)
    print(f"找到版本: {filename}")
    print(f"下载地址: {url}")

    # 固定下载目录 tmp/ffmpeg
    base_dir = os.path.join(os.getcwd(), "ffmpeg")
    os.makedirs(base_dir, exist_ok=True)

    archive_path = os.path.join(base_dir, filename)

    # 如果已下载且已解压，且 ffmpeg_bin 文件夹存在，直接返回
    ffmpeg_bin_dir = os.path.join(base_dir, "ffmpeg_bin")
    ffmpeg_extracted_flag = os.path.join(base_dir, '.extracted')
    if os.path.exists(archive_path) and os.path.exists(ffmpeg_extracted_flag) and os.path.exists(ffmpeg_bin_dir):
        print(f"✅ FFmpeg 已存在于 {ffmpeg_bin_dir}，跳过下载和解压")
        return ffmpeg_bin_dir

    # 清空旧内容
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    print("下载中...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(archive_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = downloaded * 100 // total if total else 0
    print("解压中...")
    extract_archive(archive_path, base_dir)
    # 标记已解压
    with open(ffmpeg_extracted_flag, 'w') as f:
        f.write('ok')

    print(f"✅ FFmpeg 已下载并解压至 {ffmpeg_bin_dir}")
    return ffmpeg_bin_dir
