"""二维码生成工具."""

import io
from pathlib import Path
from typing import Optional

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer


def generate_qr(
    data: str,
    output_path: Optional[str] = None,
    box_size: int = 8,
    border: int = 2,
    fill_color: str = "black",
    back_color: str = "white",
) -> str:
    """生成二维码图片."""
    qr = qrcode.QRCode(
        version=None,  # 自动选择
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    if output_path:
        img.save(output_path)
        return output_path
    else:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf


def generate_payment_qr(
    amount: float,
    platform: str,
    work_id: str,
    output_dir: str,
) -> str:
    """生成支付二维码 (模拟支付链接)."""
    data = f"oristudio:pay:{platform}:{work_id}:{amount:.2f}"
    output_path = str(Path(output_dir) / f"pay_{work_id}_{platform}.png")
    return generate_qr(data, output_path)


def generate_verification_qr(
    cert_id: str,
    output_dir: str,
) -> str:
    """生成验证二维码 (指向证书验证页面)."""
    data = f"https://oristudio.local/verify/{cert_id}"
    output_path = str(Path(output_dir) / f"verify_{cert_id}.png")
    return generate_qr(data, output_path)
