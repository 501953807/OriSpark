"""水印预设服务."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.watermark_preset import WatermarkPreset, PositionEnum


def get_presets(db: Session) -> List[dict]:
    """获取所有水印预设，按创建时间降序排列."""
    presets = db.query(WatermarkPreset).order_by(WatermarkPreset.created_at.desc()).all()
    return [p.to_dict() for p in presets]


def get_preset(db: Session, preset_id: str) -> Optional[dict]:
    """根据 ID 获取单个水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if preset:
        return preset.to_dict()
    return None


def create_preset(
    db: Session,
    name: str,
    position: str,
    opacity: int = 100,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
) -> dict:
    """创建新的水印预设."""
    # Convert string position to enum
    try:
        position_enum = PositionEnum(position)
    except ValueError:
        raise ValueError(f"无效的position值：{position}")

    preset = WatermarkPreset(
        name=name,
        position=position_enum,
        opacity=opacity,
        text=text,
        image_path=image_path,
    )
    db.add(preset)
    try:
        db.commit()
        db.refresh(preset)
        return preset.to_dict()
    except Exception:
        db.rollback()
        raise


def update_preset(
    db: Session,
    preset_id: str,
    name: Optional[str] = None,
    position: Optional[str] = None,
    opacity: Optional[int] = None,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
) -> dict:
    """更新现有水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        raise ValueError("预设不存在")

    if name is not None:
        preset.name = name
    if position is not None:
        try:
            preset.position = PositionEnum(position)
        except ValueError:
            raise ValueError(f"无效的position值：{position}")
    if opacity is not None:
        preset.opacity = opacity
    if text is not None:
        preset.text = text
    if image_path is not None:
        preset.image_path = image_path

    try:
        db.commit()
        db.refresh(preset)
        return preset.to_dict()
    except Exception:
        db.rollback()
        raise


def delete_preset(db: Session, preset_id: str) -> bool:
    """删除水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        return False
    db.delete(preset)
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def apply_watermark_to_work(
    db: Session, work_id: str, preset_id: str
) -> dict:
    """
    将水印预设应用到作品（批量操作接口）.

    注意：此函数主要负责验证和记录，实际的水印应用逻辑
    由外部服务或图像处理模块执行。
    """
    # 验证作品是否存在（work表存在说明作品已注册）
    from app.models.work import Work
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"作品 {work_id} 不存在")

    # 验证预设是否存在
    preset = get_preset(db, preset_id)
    if not preset:
        raise ValueError(f"水印预设 {preset_id} 不存在")

    # 记录水印应用（这里简化，实际可能需要水印日志表）
    return {
        "work_id": work_id,
        "preset_id": preset_id,
        "applied_at": datetime.now().isoformat(),
        "message": f"水印预设 '{preset['name']}' 已应用于作品 {work_id}"
    }
