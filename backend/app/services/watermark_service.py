"""Watermark service — generate previews, apply watermarks, validate configs."""

from typing import Tuple


def validate_config(config: dict) -> Tuple[bool, str]:
    """Validate a watermark configuration dictionary.

    Returns (is_valid, error_message).
    """
    watermark_type = config.get("watermark_type")
    if watermark_type not in ("text", "image", "tiled"):
        return False, "Invalid watermark_type"

    if watermark_type == "text":
        text = config.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            return False, "text watermark requires non-empty 'text'"

    elif watermark_type == "image":
        image_url = config.get("image_url")
        if not image_url:
            return False, "image watermark requires 'image_url'"

    elif watermark_type == "tiled":
        tile_image_url = config.get("tile_image_url")
        if not tile_image_url:
            return False, "tiled watermark requires 'tile_image_url'"

    position = config.get("position", "bottom_right")
    valid_positions = (
        "top_left", "top_right", "bottom_left", "bottom_right",
        "center", "custom",
    )
    if position not in valid_positions:
        return False, f"Invalid position: {position}"

    opacity = config.get("opacity")
    if opacity is not None and not (0 <= opacity <= 1):
        return False, "opacity must be between 0 and 1"

    return True, ""


def generate_watermark_preview(preset_config: dict, image_path: str) -> str:
    """Generate a preview URL/path for a watermark preset applied to an image.

    Returns a file path string pointing to the preview image.
    """
    from pathlib import Path
    import shutil

    data_dir = Path("data") / "thumbnails" / "watermark_previews"
    data_dir.mkdir(parents=True, exist_ok=True)

    preview_path = str(data_dir / f"preview_{hash(str(preset_config))}.png")

    # MVP: copy source image as placeholder preview
    try:
        src = Path(image_path)
        if src.exists():
            shutil.copy2(str(src), preview_path)
        else:
            preview_path = image_path  # fall back to source
    except Exception:
        preview_path = image_path

    return preview_path


def apply_watermark(work_path: str, preset: dict, output_path: str) -> bool:
    """Apply a watermark preset to an image file.

    Returns True on success, False on failure.
    MVP stub: copies the file to output_path without real processing.
    """
    from pathlib import Path
    import shutil

    try:
        src = Path(work_path)
        dst = Path(output_path)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        return True
    except Exception:
        return False
