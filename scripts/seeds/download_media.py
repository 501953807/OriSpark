"""媒体数据下载器 — 为种子数据准备真实媒体文件.

使用免费API下载测试用的图片、音频、视频:
- 图片: picsum.photos (随机高质量图片)
- 音频: 使用免费样本或生成空白音频
- 视频: 使用简短测试视频
"""

import os
import sys
from pathlib import Path
import requests
from PIL import Image
import io
import uuid


MEDIA_DIR = Path(__file__).parent.parent / "test_media"
MEDIA_DIR.mkdir(exist_ok=True)

IMAGE_DIR = MEDIA_DIR / "images"
AUDIO_DIR = MEDIA_DIR / "audio"
VIDEO_DIR = MEDIA_DIR / "video"

for d in [IMAGE_DIR, AUDIO_DIR, VIDEO_DIR]:
    d.mkdir(exist_ok=True)


def download_image(url: str, filename: str, width: int = 800, height: int = 600) -> str:
    """下载图片并保存."""
    dest = IMAGE_DIR / filename
    if dest.exists():
        return str(dest)

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            dest.write_bytes(resp.content)
            print(f"  ✓ {filename}")
            return str(dest)
    except Exception as e:
        print(f"  ✗ 下载失败 {filename}: {e}")

    # 备用: 生成占位图片
    img = Image.new('RGB', (width, height), color=(random_color(), random_color(), random_color()))
    img.save(dest)
    print(f"  ✓ {filename} (占位)")
    return str(dest)


def random_color():
    """生成随机颜色."""
    import random
    return random.randint(50, 200)


def generate_blank_audio(filename: str, duration_sec: int = 5, sample_rate: int = 44100) -> str:
    """生成空白音频文件(WAV格式)."""
    dest = AUDIO_DIR / filename
    if dest.exists():
        return str(dest)

    try:
        import struct
        import math

        num_samples = sample_rate * duration_sec
        # 生成正弦波作为测试音频
        freq = 440  # A4音符
        with open(dest, 'wb') as f:
            # WAV header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + num_samples * 2))  # file size
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))  # chunk size
            f.write(struct.pack('<H', 1))   # PCM
            f.write(struct.pack('<H', 1))   # mono
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))   # block align
            f.write(struct.pack('<H', 16))  # bits per sample
            f.write(b'data')
            f.write(struct.pack('<I', num_samples * 2))
            for i in range(num_samples):
                # 简单正弦波
                value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sample_rate))
                f.write(struct.pack('<h', value))

        print(f"  ✓ {filename}")
        return str(dest)
    except Exception as e:
        print(f"  ✗ 生成音频失败 {filename}: {e}")
        return ""


def generate_blank_video(filename: str, duration_sec: int = 5, width: int = 320, height: int = 240) -> str:
    """生成空白视频文件(使用FFmpeg或占位图片序列)."""
    dest = VIDEO_DIR / filename
    if dest.exists():
        return str(dest)

    try:
        # 尝试使用FFmpeg生成简单视频
        import subprocess
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'color=c=blue:s={width}x{height}:d={duration_sec}:r=30',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            str(dest)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0 and dest.exists():
            print(f"  ✓ {filename}")
            return str(dest)
    except Exception as e:
        print(f"  ✗ 生成视频失败 {filename}: {e}")

    # 备用: 创建占位图片
    import random
    from PIL import Image
    img = Image.new('RGB', (width, height), color=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
    img.save(dest.with_suffix('.jpg'))
    print(f"  ! {filename} (使用图片占位)")
    return str(dest.with_suffix('.jpg'))


def download_all_media():
    """下载所有需要的测试媒体."""
    print("=== 下载测试媒体文件 ===\n")

    # 插画师作品 (PNG/JPG)
    print("1. 插画师作品图片...")
    for i in range(10):
        download_image(
            f"https://picsum.photos/800/600?random={i+1}",
            f"illustrator_work_{i+1}.png"
        )

    # 摄影师作品 (JPG)
    print("\n2. 摄影师作品图片...")
    for i in range(10):
        download_image(
            f"https://picsum.photos/1200/800?random={i+11}",
            f"photographer_work_{i+1}.jpg"
        )

    # 视频创作者作品 (MP4)
    print("\n3. 视频创作者作品...")
    for i in range(5):
        generate_blank_video(f"video_creator_work_{i+1}.mp4", duration_sec=3)

    # 手工艺人作品 (JPG/PNG)
    print("\n4. 手工艺人作品图片...")
    for i in range(8):
        download_image(
            f"https://picsum.photos/600/600?random={i+20}",
            f"crafter_work_{i+1}.jpg"
        )

    # 音乐人作品 (MP3)
    print("\n5. 音乐人作品音频...")
    for i in range(5):
        generate_blank_audio(f"musician_work_{i+1}.mp3", duration_sec=10)

    # 文字作者作品 (PDF占位)
    print("\n6. 文字作者作品...")
    from reportlab.pdfgen import canvas
    for i in range(5):
        dest = Path(f"/tmp/book_work_{i+1}.pdf")
        c = canvas.Canvas(str(dest), pagesize=(A4))
        c.drawString(100, 750, f"《{random_book_title()}》")
        c.drawString(100, 700, f"作者: 测试作家{i+1}")
        c.drawString(100, 650, "这是一本测试书籍的内容预览...")
        for j in range(20):
            c.drawString(100, 600-j*20, f"第{j+1}行测试内容 -  Lorem ipsum dolor sit amet.")
        c.showPage()
        c.save()
        import shutil
        shutil.copy(str(dest), str(MEDIA_DIR / f"writer_work_{i+1}.pdf"))
        print(f"  ✓ writer_work_{i+1}.pdf")

    # 生成书籍封面
    print("\n7. 书籍封面...")
    for i in range(5):
        download_image(
            f"https://picsum.photos/400/600?random={i+30}",
            f"book_cover_{i+1}.jpg"
        )

    print("\n=== 媒体下载完成 ===")
    print(f"图片: {len(list(IMAGE_DIR.glob('*')))} 个文件")
    print(f"音频: {len(list(AUDIO_DIR.glob('*')))} 个文件")
    print(f"视频: {len(list(VIDEO_DIR.glob('*')))} 个文件")


def random_book_title():
    """随机书籍标题."""
    import random
    titles = [
        "星辰大海的旅程", "时光倒流的五分钟", "最后的守护者",
        "云端之下的秘密", "回声谷", "月光编织者",
        "深海之谜", "风暴之眼", "无尽之夏",
        "沉默的证人"
    ]
    return random.choice(titles)


if __name__ == "__main__":
    download_all_media()
