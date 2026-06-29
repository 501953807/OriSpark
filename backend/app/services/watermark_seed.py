"""Watermark seed data — default presets for new OriStudio installations."""

from datetime import datetime
from sqlalchemy.orm import Session

from app.models.watermark import WatermarkPreset


def seed_default_presets(db: Session):
    """Insert default watermark presets if none exist."""
    existing = db.query(WatermarkPreset).filter(
        WatermarkPreset.is_default == True  # noqa: E712
    ).first()
    if existing:
        return

    defaults = [
        WatermarkPreset(
            name="Corner Logo",
            description="Small text watermark, bottom-right corner, subtle opacity",
            watermark_type="text",
            config={
                "text": "OriStudio",
                "font_size": 24,
                "font_color": "#FFFFFF",
                "opacity": 0.3,
                "position": "bottom_right",
                "rotation": 0,
                "padding": 16,
            },
            is_default=True,
        ),
        WatermarkPreset(
            name="Center Diagonal",
            description="Larger diagonal text watermark centered on the image",
            watermark_type="text",
            config={
                "text": "Copyright OriStudio",
                "font_size": 48,
                "font_color": "#FFFFFF",
                "opacity": 0.2,
                "position": "center",
                "rotation": 45,
                "padding": 32,
            },
            is_default=True,
        ),
        WatermarkPreset(
            name="Tiled Pattern",
            description="Repeated small text pattern across the entire image",
            watermark_type="tiled",
            config={
                "text": "© OriStudio",
                "tile_font_size": 16,
                "tile_opacity": 0.1,
                "tile_color": "#FFFFFF",
                "tile_width": 120,
                "tile_height": 40,
                "spacing": 80,
            },
            is_default=True,
        ),
    ]

    db.add_all(defaults)
    db.commit()
