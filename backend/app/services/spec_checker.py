"""Design specification checker — validates design files against product requirements.

P1.5.3-P1.5.4: Validates DPI, dimensions, color mode, bleed, format requirements,
and returns pass/warning/error with actionable suggestions.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SpecCheckResult:
    """Single check result."""
    check: str           # dpi / dimensions / color_mode / format / bleed / transparency
    status: str          # pass / warning / error
    message: str
    suggestion: str = ""


@dataclass
class SpecValidationReport:
    """Aggregate validation report for a design-product pair."""
    product_category_id: str
    product_name: str
    overall_status: str  # pass / warning / error
    checks: list[SpecCheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.overall_status != "error"

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warning")


def _overall_status(checks: list[SpecCheckResult]) -> str:
    """Determine overall status from individual checks."""
    has_error = any(c.status == "error" for c in checks)
    has_warning = any(c.status == "warning" for c in checks)
    if has_error:
        return "error"
    if has_warning:
        return "warning"
    return "pass"


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------
def validate_design_spec(
    category_template: dict,
    *,
    dpi: Optional[int] = None,
    width_px: Optional[int] = None,
    height_px: Optional[int] = None,
    color_mode: Optional[str] = None,
    file_format: Optional[str] = None,
    has_transparency: Optional[bool] = None,
) -> SpecValidationReport:
    """Validate a design against product category requirements.

    Args:
        category_template: Product category dict from seed_data.PRODUCT_CATEGORIES
        dpi: Actual DPI of the design (optional)
        width_px: Actual width in pixels (optional)
        height_px: Actual height in pixels (optional)
        color_mode: 'sRGB', 'CMYK', or None if unknown
        file_format: 'PNG', 'JPEG', 'PDF', 'AI/PDF', etc.
        has_transparency: Whether the design has transparent areas

    Returns:
        SpecValidationReport with all checks and suggestions
    """
    checks: list[SpecCheckResult] = []

    required_dpi = category_template.get("dpi_requirement", 300)
    required_color = category_template.get("color_mode", "sRGB")
    required_format = category_template.get("file_format", "PNG")
    required_transparent = category_template.get("transparent_bg", False)
    size_spec = category_template.get("size_spec", {})
    target_w_mm = size_spec.get("width_mm", 0)
    target_h_mm = size_spec.get("height_mm", 0)
    bleed_mm = size_spec.get("bleed_mm", 0)

    # 1. DPI check
    if required_dpi > 0:
        if dpi is None:
            checks.append(SpecCheckResult(
                check="dpi",
                status="warning",
                message=f"无法检测 DPI — 要求 ≥ {required_dpi} DPI",
                suggestion=f"请确保设计稿分辨率 ≥ {required_dpi} DPI。当前尺寸下需要至少 {_min_pixels(target_w_mm, target_h_mm, required_dpi)}",
            ))
        elif dpi < required_dpi * 0.8:
            checks.append(SpecCheckResult(
                check="dpi",
                status="error",
                message=f"DPI 不足: 当前 {dpi} DPI, 要求 ≥ {required_dpi} DPI",
                suggestion=f"需要至少 {required_dpi} DPI。建议重新导出或使用更高分辨率的源文件，"
                           f"目标像素尺寸: {_min_pixels(target_w_mm, target_h_mm, required_dpi)}",
            ))
        elif dpi < required_dpi:
            checks.append(SpecCheckResult(
                check="dpi",
                status="warning",
                message=f"DPI 略低: 当前 {dpi} DPI, 建议 ≥ {required_dpi} DPI",
                suggestion=f"当前可接受但非最优。建议提升到 {required_dpi} DPI. "
                           f"目标像素: {_min_pixels(target_w_mm, target_h_mm, required_dpi)}",
            ))
        else:
            checks.append(SpecCheckResult(
                check="dpi",
                status="pass",
                message=f"DPI 合格: {dpi} DPI (要求 ≥ {required_dpi})",
            ))

    # 2. Dimensions check (mm -> px conversion)
    if target_w_mm > 0 and target_h_mm > 0:
        effective_dpi = dpi if dpi and dpi > 0 else 300
        required_w = _mm_to_px(target_w_mm + bleed_mm * 2, effective_dpi)
        required_h = _mm_to_px(target_h_mm + bleed_mm * 2, effective_dpi)

        if width_px is not None and height_px is not None:
            ratio_ok = True
            if width_px < required_w * 0.9:
                ratio_ok = False
            if height_px < required_h * 0.9:
                ratio_ok = False

            if ratio_ok:
                checks.append(SpecCheckResult(
                    check="dimensions",
                    status="pass",
                    message=f"尺寸合格: {width_px}x{height_px}px (需要 ≥ {required_w}x{required_h}px @{effective_dpi}DPI, "
                            f"印刷尺寸 {target_w_mm}x{target_h_mm}mm + {bleed_mm}mm 出血)",
                ))
            else:
                checks.append(SpecCheckResult(
                    check="dimensions",
                    status="error",
                    message=f"尺寸不足: 当前 {width_px}x{height_px}px, "
                            f"需要 ≥ {required_w}x{required_h}px (@{effective_dpi}DPI, "
                            f"{target_w_mm}x{target_h_mm}mm + {bleed_mm}mm 出血)",
                    suggestion=f"请使用至少 {required_w}x{required_h}px 的设计稿。"
                               f"当前像素比例对应约 {_px_to_mm(width_px, effective_dpi):.0f}x{_px_to_mm(height_px, effective_dpi):.0f}mm",
                ))
        else:
            # Can't check dimensions, just warn
            checks.append(SpecCheckResult(
                check="dimensions",
                status="warning",
                message="无法检测尺寸 — 未提供像素尺寸",
                suggestion=f"请确认设计稿尺寸满足 {target_w_mm}x{target_h_mm}mm (印刷区域) + {bleed_mm}mm 出血, "
                           f"需要 ≥ {_min_pixels(target_w_mm, target_h_mm, effective_dpi)}",
            ))

    # 3. Color mode check
    if required_color not in ("N/A", ""):
        if color_mode is None:
            checks.append(SpecCheckResult(
                check="color_mode",
                status="warning",
                message=f"无法检测色彩模式 — 要求 {required_color}",
                suggestion=f"请确认色彩模式为 {required_color}。" +
                           ("注意: CMYK 用于印刷, RGB 用于POD打印。Printful等平台通常要求 sRGB。" if required_color == "sRGB" else ""),
            ))
        elif color_mode.upper() != required_color.upper():
            severity = "error" if required_color == "CMYK" else "warning"
            checks.append(SpecCheckResult(
                check="color_mode",
                status=severity,
                message=f"色彩模式不匹配: 当前 {color_mode}, 要求 {required_color}",
                suggestion=f"请将设计稿转换为 {required_color} 色彩模式。" +
                           (f" CMYK 是印刷标准; {color_mode} 可能导致色差。" if required_color == "CMYK" else
                            f" {required_color} 是 POD 平台标准格式。"),
            ))
        else:
            checks.append(SpecCheckResult(
                check="color_mode",
                status="pass",
                message=f"色彩模式合格: {color_mode} (要求 {required_color})",
            ))

    # 4. File format check
    if required_format not in ("N/A", ""):
        if file_format is None:
            checks.append(SpecCheckResult(
                check="format",
                status="warning",
                message=f"无法检测文件格式 — 要求 {required_format}",
                suggestion=f"请确保文件格式为 {required_format}。",
            ))
        elif file_format.upper() != required_format.upper() and required_format != "AI/PDF":
            if required_format == "PNG" and file_format.upper() in ("JPEG", "JPG"):
                checks.append(SpecCheckResult(
                    check="format",
                    status="error",
                    message=f"文件格式错误: 当前 {file_format}, 要求 {required_format}",
                    suggestion=f"POD 平台通常要求 PNG (支持透明)。JPEG 不含透明度且是有损压缩。请导出为 PNG 格式。",
                ))
            else:
                checks.append(SpecCheckResult(
                    check="format",
                    status="warning",
                    message=f"文件格式: 当前 {file_format}, 建议 {required_format}",
                    suggestion=f"推荐使用 {required_format} 格式以确保最佳兼容性。",
                ))
        else:
            checks.append(SpecCheckResult(
                check="format",
                status="pass",
                message=f"文件格式合格: {file_format} (要求 {required_format})",
            ))

    # 5. Transparency check
    if required_transparent:
        if has_transparency is None:
            checks.append(SpecCheckResult(
                check="transparency",
                status="warning",
                message="无法检测透明背景 — 此品类要求透明背景",
                suggestion="请在导出时确保背景已去除(透明 PNG)，否则产品上会出现白色/黑色背景框。",
            ))
        elif not has_transparency:
            checks.append(SpecCheckResult(
                check="transparency",
                status="error",
                message="缺少透明背景 — 此品类要求设计稿背景透明",
                suggestion="请去除背景并导出为含透明通道的 PNG 格式。大多数设计软件(Phtoshop/Procreate/Illustrator)支持导出透明 PNG。",
            ))
        else:
            checks.append(SpecCheckResult(
                check="transparency",
                status="pass",
                message="透明背景: OK",
            ))

    # 6. Bleed check (informational)
    if bleed_mm > 0:
        if width_px is not None and height_px is not None and dpi is not None and dpi > 0:
            w_without_bleed = _mm_to_px(target_w_mm, dpi)
            h_without_bleed = _mm_to_px(target_h_mm, dpi)
            # Simple check: image should be larger than print area without bleed
            if width_px >= _mm_to_px(target_w_mm + bleed_mm, dpi):
                checks.append(SpecCheckResult(
                    check="bleed",
                    status="pass",
                    message=f"出血区域满足: {bleed_mm}mm 四周",
                ))
            else:
                checks.append(SpecCheckResult(
                    check="bleed",
                    status="warning",
                    message=f"出血区域可能不足: 需要 {bleed_mm}mm 四周出血",
                    suggestion=f"建议添加 {bleed_mm}mm 出血区域，设计稿总尺寸应至少为 "
                               f"{target_w_mm + bleed_mm*2:.0f}x{target_h_mm + bleed_mm*2:.0f}mm",
                ))
        else:
            checks.append(SpecCheckResult(
                check="bleed",
                status="warning",
                message=f"无法检测出血 — 需要 {bleed_mm}mm 四周出血",
                suggestion=f"请确保在印刷区域({target_w_mm}x{target_h_mm}mm)外额外添加 {bleed_mm}mm 出血。",
            ))

    overall = _overall_status(checks)
    return SpecValidationReport(
        product_category_id=category_template.get("id", ""),
        product_name=category_template.get("name_zh", ""),
        overall_status=overall,
        checks=checks,
    )


def validate_for_multiple_categories(
    design_spec: dict,
    category_templates: list[dict],
) -> list[SpecValidationReport]:
    """Validate one design against multiple product categories.

    Args:
        design_spec: dict with keys: dpi, width_px, height_px, color_mode, file_format, has_transparency
        category_templates: list of product category dicts from seed_data

    Returns:
        list of SpecValidationReport, one per category
    """
    reports = []
    for cat in category_templates:
        report = validate_design_spec(cat, **design_spec)
        reports.append(report)
    return reports


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------
def _mm_to_px(mm: float, dpi: int) -> int:
    """Convert mm to pixels at given DPI."""
    return int(mm / 25.4 * dpi)


def _px_to_mm(px: int, dpi: int) -> float:
    """Convert pixels to mm at given DPI."""
    if dpi == 0:
        return 0
    return px / dpi * 25.4


def _min_pixels(w_mm: float, h_mm: float, dpi: int) -> str:
    """Human-readable minimum pixel requirement."""
    if dpi <= 0:
        return "N/A"
    return f"{_mm_to_px(w_mm, dpi)}x{_mm_to_px(h_mm, dpi)}px"


# ---------------------------------------------------------------------------
# Compatibility recommendation
# ---------------------------------------------------------------------------

@dataclass
class CompatibleTemplateResult:
    """Single compatible template result."""
    template_id: str
    name_zh: str
    name_en: str
    material_category: str
    compatibility_score: float
    spec_result: str  # pass / warning / error
    error_count: int
    warning_count: int
    min_required_px: str
    current_meets: bool


def get_compatible_templates(
    design_spec: dict,
    all_categories: list[dict],
    *,
    exclude_category_id: str | None = None,
    limit: int = 20,
) -> list[CompatibleTemplateResult]:
    """Given a design spec, find all product templates it can/warns/errors on.

    This is the core of the "compatible product recommendation" feature.
    When a design fails spec on one template (e.g., hat 150x50mm), this function
    scans ALL templates and returns which ones pass or warn.

    Args:
        design_spec: dict with keys: dpi, width_px, height_px, color_mode, file_format, has_transparency
        all_categories: full PRODUCT_CATEGORIES list from seed_data
        exclude_category_id: optional category to exclude (e.g., the one that just failed)
        limit: max results to return

    Returns:
        list of CompatibleTemplateResult sorted by compatibility_score descending
    """
    results: list[CompatibleTemplateResult] = []

    for cat in all_categories:
        if exclude_category_id and cat["id"] == exclude_category_id:
            continue

        report = validate_design_spec(cat, **design_spec)
        size_spec = cat.get("size_spec", {})
        target_w = size_spec.get("width_mm", 0)
        target_h = size_spec.get("height_mm", 0)
        eff_dpi = report.checks[0].message.split(":")[-1].strip() if report.checks else "300"
        try:
            eff_dpi_val = int(eff_dpi.split()[0]) if ":" in str(report.checks[0].message) else 300
        except (ValueError, IndexError):
            eff_dpi_val = 300

        min_px = _min_pixels(target_w, target_h, eff_dpi_val) if target_w > 0 and target_h > 0 else "N/A"

        # Calculate compatibility score
        if report.overall_status == "pass":
            score = 1.0
        elif report.overall_status == "warning":
            score = 0.7
        else:
            score = 0.0

        # Bonus: closer to requirements = higher score
        if report.overall_status == "warning":
            # Check how close it is to passing
            for check in report.checks:
                if check.status == "warning" and check.check == "dimensions":
                    # Extract current vs required from message
                    msg = check.message
                    if "当前" in msg and "需要" in msg:
                        try:
                            parts = msg.split("当前 ")[1].split("px")[0].split("x")
                            req_parts = msg.split("需要 ")[1].split("px")[0].split("x")
                            if len(parts) == 2 and len(req_parts) == 2:
                                curr_area = int(parts[0]) * int(parts[1])
                                req_area = int(req_parts[0]) * int(req_parts[1])
                                if req_area > 0:
                                    score = 0.7 * min(1.0, curr_area / req_area) + 0.3
                        except (ValueError, IndexError):
                            pass

        current_meets = report.overall_status in ("pass", "warning")

        results.append(CompatibleTemplateResult(
            template_id=cat["id"],
            name_zh=cat["name_zh"],
            name_en=cat["name_en"],
            material_category=cat["material_category"],
            compatibility_score=round(score, 2),
            spec_result=report.overall_status,
            error_count=report.error_count,
            warning_count=report.warning_count,
            min_required_px=min_px,
            current_meets=current_meets,
        ))

    # Sort by score desc, then by error_count asc
    results.sort(key=lambda r: (-r.compatibility_score, r.error_count))
    return results[:limit]


def compute_remediation_suggestions(
    design_spec: dict,
    category_template: dict,
) -> list[dict]:
    """Compute actionable remediation suggestions for a failed spec check.

    Returns a list of suggestion dicts that the frontend can display:
    [{"type": "resize", "description": "...", "current": "...", "required": "..."}, ...]
    """
    suggestions: list[dict] = []
    report = validate_design_spec(category_template, **design_spec)

    for check in report.checks:
        if check.status == "error":
            if check.check == "dimensions":
                # Extract current and required from message
                msg = check.message
                suggestion = {"type": "resize", "field": "dimensions"}
                if "当前" in msg and "需要" in msg:
                    suggestion["current"] = msg.split("当前 ")[1].split(",")[0].strip()
                    suggestion["required"] = msg.split("需要 ")[1].split(" (@")[0].strip()
                    try:
                        curr_parts = suggestion["current"].split("x")
                        req_parts = suggestion["required"].split("x")
                        if len(curr_parts) == 2 and len(req_parts) == 2:
                            curr_area = int(curr_parts[0]) * int(curr_parts[1])
                            req_area = int(req_parts[0]) * int(req_parts[1])
                            if req_area > 0 and curr_area > 0:
                                scale = max(
                                    int(req_parts[0]) / int(curr_parts[0]),
                                    int(req_parts[1]) / int(curr_parts[1]),
                                )
                                suggestion["scale_factor"] = f"{scale:.0f}x"
                    except (ValueError, IndexError):
                        pass
                suggestion["description"] = check.suggestion or check.message
                suggestions.append(suggestion)

            elif check.check == "dpi":
                msg = check.message
                suggestion = {"type": "dpi", "field": "dpi"}
                if "当前" in msg and "要求" in msg:
                    parts = msg.split(": ")
                    if len(parts) >= 2:
                        suggestion["current"] = parts[-1].split(" ")[0]
                        req_parts = parts[0].split("≥ ")
                        if len(req_parts) >= 2:
                            suggestion["required"] = req_parts[1].split(" ")[0]
                suggestion["description"] = check.suggestion or check.message
                suggestions.append(suggestion)

            elif check.check == "color_mode":
                msg = check.message
                suggestion = {"type": "color_mode", "field": "color_mode"}
                if "当前" in msg and "要求" in msg:
                    parts = msg.split(": ")
                    if len(parts) >= 2:
                        suggestion["current"] = parts[-1].split(",")[0].strip()
                        suggestion["required"] = msg.split("要求 ")[-1].strip()
                suggestion["description"] = check.suggestion or check.message
                suggestions.append(suggestion)

            elif check.check == "format":
                msg = check.message
                suggestion = {"type": "format", "field": "file_format"}
                if "当前" in msg and "要求" in msg:
                    parts = msg.split(": ")
                    if len(parts) >= 2:
                        suggestion["current"] = parts[-1].split(",")[0].strip()
                        suggestion["required"] = msg.split("要求 ")[-1].strip()
                suggestion["description"] = check.suggestion or check.message
                suggestions.append(suggestion)

            elif check.check == "transparency":
                suggestion = {
                    "type": "transparency",
                    "field": "transparent_bg",
                    "description": "请去除背景并导出为含透明通道的 PNG 格式。",
                    "current": "无透明背景",
                    "required": "透明背景",
                }
                suggestions.append(suggestion)

    return suggestions
