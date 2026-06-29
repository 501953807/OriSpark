"""P1.6.3 — OriStudio Verified 徽章服务.

生成:
- QR code (SVG 文本形式) 指向验证URL
- SVG 徽章
- PNG 徽章 (PIL)
- HTML/JS embed snippet
"""

import os
import base64
from io import BytesIO
from pathlib import Path

QR_CODE_AVAILABLE = False
try:
    import qrcode
    QR_CODE_AVAILABLE = True
except ImportError:
    pass

PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    pass

# 输出目录
BADGE_DIR = Path("data/certificates/badges")


class VerifiedBadgeService:
    """OriStudio Verified 徽章生成器."""

    def __init__(self, base_url: str = "https://oristudio.local"):
        self.base_url = base_url

    def generate(self, product_id: str, product_title: str = "") -> dict:
        """生成完整的 Verified 徽章集合.

        Returns:
            dict with keys: qr_url, qr_svg, badge_svg, badge_png_b64, verify_url, embed_code
        """
        BADGE_DIR.mkdir(parents=True, exist_ok=True)

        cert_id = f"cert_{product_id[:12]}"
        verify_url = f"{self.base_url}/verify?cert_id={cert_id}"

        # 生成 QR 码
        qr_result = self._generate_qr(verify_url, product_id)

        # 生成 SVG 徽章
        badge_svg = self._generate_badge_svg(product_id, product_title, qr_result.get("qr_svg", ""))

        # 生成 PNG 徽章
        badge_png_b64 = self._generate_badge_png(product_id, product_title, verify_url)

        # 生成嵌入代码
        embed_code = self.generate_embed_snippet(product_id, product_title)

        return {
            "qr_url": qr_result.get("qr_data_url", ""),
            "qr_svg": qr_result.get("qr_svg", ""),
            "badge_svg": badge_svg,
            "badge_png_b64": badge_png_b64,
            "verify_url": verify_url,
            "embed_code": embed_code,
        }

    def generate_embed_snippet(self, product_id: str, product_title: str = "") -> dict:
        """生成 HTML/JS 嵌入代码."""
        cert_id = f"cert_{product_id[:12]}"
        verify_url = f"{self.base_url}/verify?cert_id={cert_id}"
        badge_api_url = f"{self.base_url}/api/publish/verified-mark/{product_id}/embed"

        html_snippet = f"""<!-- OriStudio Verified Badge -->
<div id="oristudio-verified-badge" style="
  border: 2px solid #10b981;
  border-radius: 12px;
  padding: 16px;
  max-width: 320px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: oklch(98% 0.005 170);
  text-align: center;
">
  <div style="
    font-size: 14px;
    font-weight: 700;
    color: oklch(40% 0.08 170);
    margin-bottom: 8px;
  ">
    <span style="
      display: inline-block;
      width: 20px;
      height: 20px;
      background: oklch(56% 0.12 170);
      border-radius: 50%;
      color: white;
      line-height: 20px;
      font-size: 12px;
      margin-right: 6px;
    ">&#10003;</span>
    OriStudio Verified 原创认证
  </div>
  <div style="
    font-size: 12px;
    color: oklch(50% 0 0);
    margin-bottom: 6px;
  ">
    作品: {product_title}
  </div>
  <a href="{verify_url}" target="_blank" style="
    display: inline-block;
    font-size: 11px;
    color: oklch(56% 0.12 170);
    text-decoration: underline;
  ">扫描验证原创信息 →</a>
</div>"""

        js_snippet = f"""// OriStudio Verified Badge Widget
(function() {{
  var el = document.createElement('div');
  el.id = 'oristudio-verified-badge';
  el.innerHTML = '{html_snippet.replace("'", "\\'").replace("\n", " ")}';
  var target = document.getElementById('oristudio-badge-container');
  if (target) {{
    target.appendChild(el);
  }}
}})();"""

        return {
            "html": html_snippet,
            "js": js_snippet,
            "verify_url": verify_url,
        }

    def _generate_qr(self, url: str, product_id: str) -> dict:
        """生成 QR 码 (文本 SVG 或 qrcode 库)."""
        if QR_CODE_AVAILABLE:
            return self._generate_qr_pil(url, product_id)

        # 如果没有 qrcode 库，生成一个简单的文本占位 QR 标记
        qr_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <rect width="120" height="120" fill="white" rx="8"/>
  <rect x="10" y="10" width="100" height="100" fill="none" stroke="#10b981" stroke-width="2" rx="4"/>
  <text x="60" y="52" text-anchor="middle" font-size="24" fill="#10b981">QR</text>
  <text x="60" y="78" text-anchor="middle" font-size="14" fill="#064e3b">CODE</text>
  <text x="60" y="102" text-anchor="middle" font-size="8" fill="#6b7280">Verified</text>
</svg>"""

        qr_data_url = f"data:image/svg+xml;base64,{base64.b64encode(qr_svg.encode()).decode()}"

        return {"qr_svg": qr_svg, "qr_data_url": qr_data_url}

    def _generate_qr_pil(self, url: str, product_id: str) -> dict:
        """使用 qrcode 库生成 QR 码."""
        import qrcode as qr_lib
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import SquareModuleDrawer
        from qrcode.image.styles.colormasks import SolidFillColorMask

        qr = qr_lib.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)

        # SVG 格式
        try:
            svg_output = BytesIO()
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=SquareModuleDrawer(),
                color_mask=SolidFillColorMask(
                    front_color=(16, 185, 129),
                    back_color=(255, 255, 255),
                ),
            )
            img.save(svg_output, format="SVG")
            qr_svg = svg_output.getvalue().decode("utf-8")
        except Exception:
            qr_svg = ""

        # Data URL (PNG)
        png_output = BytesIO()
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(png_output, format="PNG")
        qr_data_url = f"data:image/png;base64,{base64.b64encode(png_output.getvalue()).decode()}"

        return {"qr_svg": qr_svg, "qr_data_url": qr_data_url}

    def _generate_badge_svg(self, product_id: str, product_title: str, qr_svg: str) -> str:
        """生成 OriStudio Verified SVG 徽章."""
        title_short = product_title[:20] + "..." if len(product_title) > 20 else product_title

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="200" viewBox="0 0 360 200">
  <defs>
    <linearGradient id="badge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#10b981;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#059669;stop-opacity:1"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="360" height="200" fill="white" rx="16"/>
  <rect x="2" y="2" width="356" height="196" fill="none" stroke="url(#badge-grad)" stroke-width="3" rx="14"/>

  <!-- Left: QR Code area -->
  <rect x="16" y="16" width="88" height="88" fill="#f0fdf4" rx="8" stroke="#10b981" stroke-width="1"/>
  <text x="60" y="42" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#10b981" font-weight="bold">QR</text>
  <text x="60" y="60" text-anchor="middle" font-size="10" font-family="sans-serif" fill="#047857">扫描验证</text>
  <text x="60" y="78" text-anchor="middle" font-size="9" font-family="sans-serif" fill="#6b7280">原创信息</text>

  <!-- Right: Verified badge info -->
  <text x="120" y="42" font-size="16" font-family="sans-serif" font-weight="bold" fill="#047857">✓ OriStudio Verified</text>
  <text x="120" y="62" font-size="12" font-family="sans-serif" fill="#064e3b">原创认证</text>

  <!-- Product info -->
  <rect x="16" y="120" width="328" height="64" fill="#f8fafc" rx="8"/>
  <text x="28" y="142" font-size="11" font-family="sans-serif" fill="#6b7280">作品</text>
  <text x="28" y="160" font-size="13" font-family="sans-serif" font-weight="bold" fill="#1f2937">{title_short}</text>
  <text x="28" y="176" font-size="10" font-family="monospace" fill="#9ca3af">ID: {product_id[:16]}...</text>
</svg>"""

    def _generate_badge_png(self, product_id: str, product_title: str, verify_url: str) -> str:
        """使用 PIL 生成 PNG 徽章 (带透明背景, 可叠加在商品图上)."""
        if not PIL_AVAILABLE:
            # 返回 SVG 作为 data URL 的 fallback
            badge_svg = self._generate_badge_svg(product_id, product_title, "")
            return f"data:image/svg+xml;base64,{base64.b64encode(badge_svg.encode()).decode()}"

        try:
            width, height = 400, 220
            img = Image.new("RGBA", (width, height), (255, 255, 255, 240))
            draw = ImageDraw.Draw(img)

            # 圆角边框
            border_color = (16, 185, 129)  # #10b981
            bg_color = (248, 250, 252, 255)   # slate-50

            # 主体背景
            draw.rounded_rectangle([(4, 4), (width - 4, height - 4)], radius=16, fill=bg_color, outline=border_color, width=3)

            # QR 区域
            draw.rounded_rectangle([(16, 16), (104, 104)], radius=8, fill=(240, 253, 244, 255), outline=(16, 185, 129), width=1)
            draw.text((42, 40), "QR", fill=(16, 185, 129))
            draw.text((30, 58), "扫描验证", fill=(4, 71, 87))
            draw.text((32, 78), "原创信息", fill=(107, 114, 128))

            # Title
            draw.text((120, 30), "✓ OriStudio Verified", fill=(4, 71, 87))
            draw.text((120, 52), "原创认证", fill=(6, 78, 59))

            # Product info box
            draw.rounded_rectangle([(16, 120), (width - 16, 184)], radius=8, fill=(248, 250, 252, 255))
            title_short = product_title[:24] + "..." if len(product_title) > 24 else product_title
            draw.text((28, 130), "作品", fill=(107, 114, 128))
            draw.text((28, 148), title_short, fill=(31, 41, 55))
            draw.text((28, 168), f"ID: {product_id[:16]}...", fill=(156, 163, 175))

            # Save to buffer
            buf = BytesIO()
            img.save(buf, format="PNG")
            return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception:
            badge_svg = self._generate_badge_svg(product_id, product_title, "")
            return f"data:image/svg+xml;base64,{base64.b64encode(badge_svg.encode()).decode()}"


verified_badge_service = VerifiedBadgeService()