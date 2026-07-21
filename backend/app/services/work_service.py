"""作品管理业务服务 — 对应: docs/modules-v5/01-creative-assets.md
Phase 1.3: 视频缩略图30%位置关键帧 (非首帧)
增强: 失败时记录日志，不再静默吞错误"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("oristudio.works")


def get_image_dimensions(file_path: str) -> Tuple[Optional[int], Optional[int]]:
    try:
        from PIL import Image
        img = Image.open(file_path)
        return img.size
    except Exception:
        return None, None


def detect_file_type(extension: str) -> str:
    ext = extension.lower()
    # P2-1: RAW format support
    raw_exts = {"cr2","nef","arw","dng","rw2","orf","pef","raf","x3f","iiq","sr2","mos","mef","k25","kdc","srf","bay","ptx","dcraw","raw"}
    if ext in raw_exts: return "image"  # RAW images are still images
    if ext in {"jpg","jpeg","png","webp","gif","svg","bmp","tiff"}: return "image"
    if ext in {"mp3","wav","flac","ogg","aac","m4a"}: return "audio"
    if ext in {"mp4","mov","webm","avi","mkv"}: return "video"
    if ext in {"pdf","docx","doc","txt","md","rtf"}: return "document"
    if ext in {"psd","ai","fig","sketch"}: return "design"
    if ext in {"py","js","ts","html","css","json","xml","yaml","zip","tar","gz"}: return "code"
    return "other"


def generate_thumbnail(file_path: str, file_type: str, work_id: str) -> Optional[str]:
    thumb_dir = Path("data/thumbnails") / work_id[:2]
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / f"{work_id}_thumb.jpg"

    try:
        if file_type == "image":
            from PIL import Image
            img = Image.open(file_path)
            img.thumbnail((400, 400), Image.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=85)
            logger.debug(f"Thumbnail generated: {file_path} -> {thumb_path}")
            return str(thumb_path.resolve())

        elif file_type == "video":
            # Phase 1.3: 提取30%位置关键帧 (非首帧)
            try:
                probe = subprocess.run([
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", file_path
                ], capture_output=True, text=True, timeout=15)
                duration = float(probe.stdout.strip()) if probe.stdout.strip() else 0
            except Exception:
                logger.warning(f"ffprobe failed for {file_path}, using duration=0")
                duration = 0
            seek_time = duration * 0.3 if duration > 3 else (duration * 0.5 if duration > 0 else 0)
            r = subprocess.run([
                "ffmpeg", "-ss", str(seek_time), "-i", file_path,
                "-vframes", "1", "-s", "400x300", "-f", "image2",
                str(thumb_path), "-y"
            ], capture_output=True, timeout=30)
            if r.returncode == 0 and thumb_path.exists():
                logger.debug(f"Video thumbnail generated: {file_path} at {seek_time}s")
                return str(thumb_path.resolve())
            else:
                logger.warning(f"ffmpeg thumbnail failed for {file_path}: {r.stderr.decode()[:200] if r.stderr else 'unknown error'}")

        elif file_type == "audio":
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (400, 300), (240, 240, 245))
            draw = ImageDraw.Draw(img)
            import random
            random.seed(hash(file_path) % 10000)
            for i in range(0, 400, 4):
                h = random.randint(20, 200)
                draw.rectangle([i, 150 - h // 2, i + 2, 150 + h // 2], fill=(100, 180, 160))
            img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path.resolve())

        elif file_type == "document":
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (400, 300), (245, 245, 250))
            draw = ImageDraw.Draw(img)
            draw.text((200, 150), "DOC", fill=(100, 100, 100), anchor="mm")
            img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path.resolve())

        elif file_type == "design":
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (400, 300), (250, 245, 240))
            draw = ImageDraw.Draw(img)
            draw.text((200, 150), "DESIGN", fill=(100, 100, 100), anchor="mm")
            img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path.resolve())

        else:
            # Generic fallback for any file type
            from PIL import Image, ImageDraw
            img = Image.new("RGB", (400, 300), (245, 245, 250))
            draw = ImageDraw.Draw(img)
            draw.text((200, 150), file_type.upper()[:8], fill=(100, 100, 100), anchor="mm")
            img.save(thumb_path, "JPEG", quality=85)
            return str(thumb_path.resolve())

    except FileNotFoundError:
        logger.warning(f"File not found for thumbnail: {file_path}")
        return None
    except Exception as exc:
        logger.error(f"Thumbnail generation failed for {file_path}: {exc}")
        return None


def extract_exif(file_path: str) -> Optional[dict]:
    try:
        from PIL import Image; from PIL.ExifTags import TAGS
        img=Image.open(file_path); data=img.getexif()
        if not data: return None
        result={}
        for tid,val in data.items():
            name=TAGS.get(tid,tid)
            if isinstance(val,bytes):
                try: val=val.decode("utf-8",errors="replace")
                except: val=val.hex()
            result[name]=str(val)
        return result
    except: return None


# ====== 新增元数据提取 ======

def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """使用 mutagen 提取音频元数据: 时长/采样率/比特率/艺术家/专辑."""
    meta: Dict[str, Any] = {}
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(file_path)
        if audio is None: return meta
        if hasattr(audio.info, 'length'):
            meta["duration"] = round(audio.info.length, 1)
        if hasattr(audio.info, 'sample_rate'):
            meta["sample_rate"] = audio.info.sample_rate
        if hasattr(audio.info, 'bitrate'):
            meta["bitrate"] = audio.info.bitrate
        # tags
        for key in ['artist','album','title','genre','date']:
            if key in audio:
                meta[key] = str(audio[key][0]) if audio[key] else None
    except ImportError:
        pass  # mutagen 未安装
    except Exception:
        pass
    return meta


def extract_video_metadata(file_path: str) -> Dict[str, Any]:
    """使用 ffprobe 提取视频元数据: 分辨率/帧率/编码/时长."""
    meta: Dict[str, Any] = {}
    try:
        r = subprocess.run([
            "ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",file_path
        ], capture_output=True, text=True, timeout=30)
        if r.returncode != 0: return meta
        import json
        data = json.loads(r.stdout)
        for stream in data.get("streams",[]):
            if stream.get("codec_type")=="video":
                meta["width"] = stream.get("width")
                meta["height"] = stream.get("height")
                meta["codec"] = stream.get("codec_name")
                meta["fps"] = eval(stream.get("r_frame_rate","0/1"))
            elif stream.get("codec_type")=="audio":
                meta["audio_codec"] = stream.get("codec_name")
        fmt = data.get("format",{})
        meta["duration"] = round(float(fmt.get("duration",0)),1) if fmt.get("duration") else None
        meta["bitrate"] = int(fmt["bitrate"])//1000 if fmt.get("bitrate") else None
    except Exception:
        pass
    return meta


def extract_document_metadata(file_path: str) -> Dict[str, Any]:
    """提取文档元数据: 字数/页数/语言."""
    meta: Dict[str, Any] = {}
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".txt" or ext == ".md":
            with open(file_path,"r",encoding="utf-8",errors="replace") as f:
                text = f.read()
            meta["char_count"] = len(text)
            meta["word_count"] = len(text.split())
            meta["line_count"] = text.count("\n")+1
        elif ext == ".pdf":
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                meta["pages"] = len(reader.pages)
            except ImportError:
                pass
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(file_path)
                meta["paragraphs"] = len(doc.paragraphs)
                text = " ".join(p.text for p in doc.paragraphs)
                meta["char_count"] = len(text)
            except ImportError:
                pass
    except Exception:
        pass
    return meta


def get_all_metadata(file_path: str, file_type: str) -> Dict[str, Any]:
    """根据文件类型提取所有元数据."""
    meta: Dict[str, Any] = {}
    if file_type == "image":
        dims = get_image_dimensions(file_path)
        if dims[0]: meta["width"], meta["height"] = dims
        exif = extract_exif(file_path)
        if exif: meta["exif_data"] = exif
    elif file_type == "audio":
        meta.update(extract_audio_metadata(file_path))
    elif file_type == "video":
        meta.update(extract_video_metadata(file_path))
    elif file_type == "document":
        meta.update(extract_document_metadata(file_path))
    return meta
