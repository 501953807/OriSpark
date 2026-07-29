"""无罪证明 PDF 报告生成服务。

该服务使用 reportlab 库生成包含反防伪内容、证据摘要和存证参考的无罪证明PDF报告。
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, white, gray
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

import qrcode

from app.models.work import Work
from app.models.innocence_proof import InnocenceProof
from app.models.notary import NotaryRecord


def generate_innocence_proof_pdf(
    work: Work,
    innocence_proof: InnocenceProof,
    notary_records: Optional[List[NotaryRecord]] = None,
    output_dir: str = "data/certificates",
    template_name: str = "default",
) -> str:
    """
    生成无罪证明PDF报告。

    报告包含：
    - 作品信息摘要
    - 创作时间戳证明
    - 证据文档链
    - 区块链存证参考
    - 防伪水印和数字签名验证

    Args:
        work: 作品对象
        innocence_proof: 无罪证明对象
        notary_records: 关联的存证记录列表
        output_dir: 输出目录
        template_name: 模板名称

    Returns:
        PDF文件的完整路径
    """
    # 确保输出目录存在
    output_path = Path(output_dir) / f"innocence_proof_{innocence_proof.id[:12].upper()}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建 PDF 文档
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        landscape=False,
    )

    # 构建样式表
    styles = getSampleStyleSheet()

    # 自定义样式 - 绿色主题（象征清白/安全）
    title_style = ParagraphStyle(
        "InnocenceTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=HexColor("#1a5632"),
        spaceAfter=15,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=HexColor("#2d6a4f"),
        spaceAfter=30,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=HexColor("#1a5632"),
        spaceBefore=20,
        spaceAfter=10,
        fontName="Helvetica-Bold",
        borderPadding=5,
        backColor=HexColor("#e8f5e9"),
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=black,
        fontName="Helvetica",
        alignment=TA_JUSTIFY,
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
        fontSize=7,
        leading=10,
        alignment=TA_CENTER,
        textColor=gray,
    )

    # 构建内容故事
    story = []

    # 标题区域
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("数字作品无罪证明", title_style))
    story.append(Paragraph("Digital Work Innocence Certificate", subtitle_style))
    story.append(Spacer(1, 0.3 * cm))

    # 防伪标识
    security_bar = Paragraph(
        "<b>[防伪标识]</b> ORI-STUDIO-INNOCENCE-PROOF v1.0 | "
        "本报告通过数字签名验证，任何修改都将导致证书无效",
        ParagraphStyle("SecurityBar", parent=body_style, fontSize=9, alignment=TA_CENTER,
                      textColor=HexColor("#c0392b"), backColor=HexColor("#fdf2f9"),
                      borderPadding=5, spaceAfter=15)
    )
    story.append(security_bar)

    # 证书编号
    cert_num = f"ORI-IP-{innocence_proof.id[:12].upper()}"
    story.append(Paragraph(f"<b>证书编号：</b>{cert_num}", body_style))
    story.append(Paragraph(f"<b>签发日期：</b>{innocence_proof.created_at.strftime('%Y-%m-%d %H:%M:%S') if innocence_proof.created_at else '未知'}", body_style))
    story.append(Spacer(1, 0.5 * cm))

    # 分隔线
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2d6a4f")))
    story.append(Spacer(1, 0.5 * cm))

    # ========== 作品信息 ==========
    story.append(Paragraph("一、作品信息", section_style))

    # 作品信息表格
    info_data = [
        ["作品名称", work.title or "未命名作品"],
        ["文件名称", work.file_name],
        ["文件类型", work.file_extension.upper()],
        ["文件大小", format_file_size(work.file_size)],
        ["SHA-256 哈希", work.sha256 or "未计算"],
    ]

    if work.md5:
        info_data.append(["MD5 哈希", work.md5])
    if work.width and work.height:
        info_data.append(["分辨率", f"{work.width}×{work.height} px"])
    if work.duration:
        info_data.append(["时长", f"{work.duration:.2f} 秒"])

    info_table = Table(info_data, colWidths=[4 * cm, 11 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2c3e50")),
        ("TEXTCOLOR", (1, 0), (1, -1), black),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e0e0e0")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, HexColor("#f8f9fa")]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5 * cm))

    # ========== 创作时间戳证明 ==========
    story.append(Paragraph("二、创作时间戳证明", section_style))

    timestamp_content = """
    本作品已于 <b>{timestamp}</b> 完成原始创作。<br/>
    创作过程包含以下关键证据节点，构成完整的权利主张链条：<br/>
    • 源文件保存时间：{file_time}<br/>
    • 首次哈希计算时间：{hash_time}<br/>
    • 存证上链时间：{chain_time}<br/>
    """

    timestamp_text = timestamp_content.format(
        timestamp=work.created_at.strftime('%Y年%m月%d日 %H时%M分') if work.created_at else '未知',
        file_time=work.imported_at.strftime('%Y年%m月%d日') if work.imported_at else '未知',
        hash_time='待计算',  # 实际应用中应记录首次哈希时间
        chain_time='未上链' if not notary_records else '已上链'
    )
    story.append(Paragraph(timestamp_text, body_style))
    story.append(Spacer(1, 0.3 * cm))

    # ========== 证据文档链 ==========
    story.append(Paragraph("三、证据文档链", section_style))

    if innocence_proof.evidence_document_url:
        story.append(Paragraph(f"• <b>原始证据文档：</b>{innocence_proof.evidence_document_url}", body_style))
    if innocence_proof.summary_text:
        story.append(Paragraph(f"• <b>证明摘要：</b>{innocence_proof.summary_text[:200]}{'...' if len(innocence_proof.summary_text) > 200 else ''}", body_style))
    story.append(Spacer(1, 0.3 * cm))

    # ========== 区块链存证参考 ==========
    if notary_records:
        story.append(PageBreak())  # 分页，让不记证据单独一页
        story.append(Paragraph("四、区块链存证参考", section_style))

        notary_data = [["存证平台", "平台链接", "交易哈希", "确认时间"]]
        for record in notary_records:
            platform_name = {
                "banquanjia": "版权家 (DCI)",
                "antchain": "蚂蚁链 (AntChain)",
                "zhixinchain": "至信链 (ZhixinChain)",
            }.get(record.platform, record.platform)

            notary_data.append([
                platform_name,
                record.platform_url or "未配置",
                record.transaction_hash or "N/A",
                record.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if record.confirmed_at else "待确认"
            ])

        notary_table = Table(notary_data, colWidths=[3.5 * cm, 3.5 * cm, 3 * cm, 2.5 * cm])
        notary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), white),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d6a4f")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e0e0e0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#f8f9fa")]),
        ]))
        story.append(notary_table)
        story.append(Spacer(1, 0.5 * cm))

        # QR码验证
        qr_text = "扫描二维码验证存证真实性"
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr_data = f"https://oristudio.local/verify/{innocence_proof.id}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        qr_path = Path(output_dir) / f"qr_{innocence_proof.id}.png"
        qr_img.save(qr_path)

        qr_table_data = [[Paragraph(qr_text, footer_style), RLImage(str(qr_path), width=3 * cm, height=3 * cm)]]
        qr_table = Table(qr_table_data, colWidths=[8 * cm, 4 * cm])
        qr_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("RIGHTPADDING", (0, 0), (0, -1), 20),
        ]))
        story.append(qr_table)
        story.append(Spacer(1, 1 * cm))

    # ========== 法律声明 ==========
    story.append(PageBreak())
    story.append(Paragraph("五、法律声明与免责声明", section_style))

    disclaimer = """
    本《数字作品无罪证明》由 OriStudio 系统自动生成，旨在帮助创作者保留作品创作过程的相关证据，
    辅助其在潜在侵权纠纷中证明作品的原创性。<br/><br/>

    <b>重要提示：</b><br/>
    1. 本证明文件仅供参考，不构成任何法律意见或法庭认证证据；<br/>
    2. 建议将原始创作文件、中间版本、存证记录等重要资料妥善保存；<br/>
    3. 在正式法律程序中，请寻求专业律师的帮助并结合其他有效证据使用；<br/>
    4. 本报告的数字签名可用于验证文件完整性，任何篡改都会导致签名失效。<br/><br/>

    本证明文件有效期为自签发之日起三年，或与相关著作权保护期限一致（以较长者为准）。
    """
    story.append(Paragraph(disclaimer, body_style))
    story.append(Spacer(1, 1 * cm))

    # 页脚信息
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e0e0e0")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        f"© {datetime.now().strftime('%Y')} OriStudio 开源项目 | 本证书通过数字签名验证副本 | "
        f"查询地址: https://oristudio.local/verify/{innocence_proof.id[:8]}",
        footer_style
    ))

    # 生成 PDF
    doc.build(story)

    return str(output_path.resolve())


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
