"""Watermark seed data — default presets for new OriStudio installations."""

from sqlalchemy.orm import Session

from app.models.watermark_preset import WatermarkPreset, PositionEnum


def seed_default_presets(db: Session):
    """Insert default watermark presets if none exist."""
    # Check if any preset already exists (simple check)
    existing = db.query(WatermarkPreset).first()
    if existing:
        return

    defaults = [
        WatermarkPreset(
            name="Corner Logo",
            position=PositionEnum.BOTTOM_RIGHT,
            opacity=30,
            text="OriStudio",
        ),
        WatermarkPreset(
            name="Center Diagonal",
            position=PositionEnum.TOP_RIGHT,
            opacity=20,
            text="Copyright OriStudio",
        ),
        WatermarkPreset(
            name="Top Left Branding",
            position=PositionEnum.TOP_LEFT,
            opacity=15,
            text="© OriStudio",
        ),
    ]

    db.add_all(defaults)
    db.commit()
