"""PDF 证书生成服务."""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, black, gray
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

import qrcode

from app.models.work import Work
from app.models.notary import NotaryRecord


def generate_certificate_pdf(
    work: Work,
    notary_record: NotaryRecord,
    output_dir: str,
    template_name: str = "default",
) -> str:
    """生成存证 PDF 证书."""
    cert_id = notary_record.id
    output_path = Path(output_dir) / f"cert_{cert_id}.pdf"

    # 创建文档
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        "CertificateTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=HexColor("#1a5632"),
        spaceAfter=20,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "CertificateSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=gray,
        spaceAfter=30,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=HexColor("#2d6a4f"),
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        textColor=black,
        fontName="Helvetica",
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        textColor=gray,
        fontName="Helvetica-Bold",
    )

    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=12,
        alignment=TA_CENTER,
        textColor=gray,
    )

    # 平台名称映射
    platform_names = {
        "banquanjia": "版权家 (DCI)",
        "antchain": "蚂蚁链 (AntChain)",
        "zhixinchain": "至信链 (ZhixinChain)",
    }

    # 构建内容
    story = []

    # 标题
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("数字作品存证证书", title_style))
    story.append(Paragraph("Digital Work Evidence Certificate", subtitle_style))
    story.append(Spacer(1, 0.5 * cm))

    # 证书编号
    story.append(Paragraph(f"<b>证书编号：</b>ORI-{notary_record.id[:12].upper()}", body_style))
    story.append(Paragraph(f"<b>存证平台：</b>{platform_names.get(notary_record.platform, notary_record.platform)}", body_style))
    story.append(Paragraph(f"<b>签发日期：</b>{notary_record.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if notary_record.confirmed_at else datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 0.8 * cm))

    # 分隔线
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f")))
    story.append(Spacer(1, 0.5 * cm))

    # 作品信息
    story.append(Paragraph("作品信息", section_style))

    # 表格布局
    info_data = [
        ["作品名称", work.title or "未命名作品"],
        ["文件名称", work.file_name],
        ["文件类型", work.file_extension.upper()],
        ["文件大小", format_file_size(work.file_size)],
        ["SHA-256 哈希", work.sha256 or "N/A"],
    ]

    if work.md5:
        info_data.append(["MD5 哈希", work.md5])

    info_table = Table(info_data, colWidths=[4 * cm, 10 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), gray),
        ("TEXTCOLOR", (1, 0), (1, -1), black),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e0e0e0")),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    # 区块链信息
    story.append(Paragraph("区块链存证信息", section_style))

    chain_data = [
        ["存证平台", platform_names.get(notary_record.platform, notary_record.platform)],
        ["存证哈希", notary_record.evidence_hash or work.sha256 or "N/A"],
    ]

    if notary_record.transaction_hash:
        chain_data.append(["交易哈希", notary_record.transaction_hash])
    if notary_record.block_height:
        chain_data.append(["区块高度", notary_record.block_height])
    if notary_record.platform_url:
        chain_data.append(["平台链接", notary_record.platform_url])

    chain_table = Table(chain_data, colWidths=[4 * cm, 10 * cm])
    chain_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), gray),
        ("TEXTCOLOR", (1, 0), (1, -1), black),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e0e0e0")),
    ]))

    story.append(chain_table)
    story.append(Spacer(1, 0.8 * cm))

    # 生成 QR 码
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr_data = f"https://oristudio.local/verify/{notary_record.id}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_path = Path(output_dir) / f"qr_{notary_record.id}.png"
    qr_img.save(qr_path)

    # QR 码区域
    qr_table_data = [[
        Paragraph("扫描二维码验证证书真伪", footer_style),
        RLImage(str(qr_path), width=3 * cm, height=3 * cm),
    ]]

    qr_table = Table(qr_table_data, colWidths=[8 * cm, 4 * cm])
    qr_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "RIGHT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("RIGHTPADDING", (0, 0), (0, 0), 20),
    ]))

    story.append(qr_table)
    story.append(Spacer(1, 1 * cm))

    # 页脚
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "本证书由 OriStudio 生成，数据来源于用户本地的 SHA-256 哈希计算及所选存证平台的存证记录。"
        "本证书仅供存证参考，不构成任何法律意见。",
        footer_style,
    ))
    story.append(Paragraph(
        f"Generated by OriStudio v0.1.0 | 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        footer_style,
    ))

    # 生成 PDF
    doc.build(story)

    return str(output_path.resolve())


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
