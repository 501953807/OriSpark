"""侵权风险预警引擎服务.

Phase 0: 实现四个检测维度
1. 提示词侵权检测 (本地关键词库)
2. 参考图相似度检测 (pHash + 汉明距离近似)
3. LoRA/模型权属检查 (Civitai/HuggingFace API)
4. 商标/Logo 碰撞 (CNIPA 本地库)
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.risk_warning import RiskWarning, HealthMetric
from app.gateway.trademark import TrademarkGateway, MockTrademarkGateway
from app.gateway.model_source import ModelSourceGateway, MockModelSourceGateway


@dataclass
class BurnoutRisk:
    """Burnout 风险评估结果."""
    risk_level: str  # low / medium / high
    score: float
    factors: list = field(default_factory=list)
    recommendation: str = ""


# 内置侵权关键词库 (v1 硬编码，后续可从 dictStore 动态加载)
INFRINGEMENT_KEYWORDS = {
    "trademark": [
        "Hello Kitty", "迪士尼", "Disney", "漫威", "Marvel", "任天堂", "Nintendo",
        "宝可梦", "Pokemon", "原神", "Genshin", "泡泡玛特", "故宫",
        "Nike", "Adidas", "Apple", "Louis Vuitton", "Gucci",
    ],
    "character": [
        "米老鼠", "Mickey Mouse", "孙悟空", "哪吒", "葫芦娃", "黑猫警长",
        "蜘蛛侠", "Batman", "Superman", "皮卡丘",
    ],
    "artist_style": [
        "毕加索风格", "Van Gogh style", "莫奈风格", "草间弥生风格",
    ],
}


@dataclass
class WarningResult:
    """单个检测结果."""
    warning_type: str
    severity: str  # "low" / "medium" / "high"
    title: str
    description: str
    matched_entity: str
    confidence: float  # 0-100
    suggestion: str


class RiskWarningService:
    """风险预警引擎服务."""

    def __init__(self, trademark_gateway: Optional[TrademarkGateway] = None,
                 model_gateway: Optional[ModelSourceGateway] = None):
        self.tm_gateway = trademark_gateway or MockTrademarkGateway()
        self.model_gateway = model_gateway or MockModelSourceGateway()

    def check_prompt(self, prompt: str, work_title: str = "") -> list[WarningResult]:
        """维度 1: 提示词侵权检测."""
        warnings = []
        text = f"{prompt} {work_title}".lower()

        for category, keywords in INFRINGEMENT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    severity = "high" if category == "trademark" else "medium"
                    warnings.append(WarningResult(
                        warning_type=f"prompt_{category}",
                        severity=severity,
                        title=f"检测到{self._cat_label(category)}冲突: '{kw}'",
                        description=f"提示词中包含 '{kw}'，可能涉及{'商标' if category == 'trademark' else '版权'}风险。",
                        matched_entity=kw,
                        confidence=85.0 if category == "trademark" else 60.0,
                        suggestion=self._get_suggestion(category, kw),
                    ))

        return warnings

    def check_reference_image(self, image_hash: str, existing_hashes: list[str]) -> Optional[WarningResult]:
        """维度 2: 参考图相似度检测."""
        if not image_hash or not existing_hashes:
            return None

        max_sim = self._hamming_similarity(image_hash, existing_hashes)
        if max_sim > 80.0:
            return WarningResult(
                warning_type="reference_similar",
                severity="high" if max_sim > 90 else "medium",
                title=f"参考图与现有作品高度相似 ({max_sim:.1f}%)",
                description="参考图与系统中已有作品相似度超过阈值，可能存在抄袭风险。",
                matched_entity=f"similarity:{max_sim:.1f}%",
                confidence=max_sim,
                suggestion="建议更换参考图或大幅修改创作方向。",
            )
        return None

    def check_model(self, model_name: str, source: str = "civitai") -> Optional[WarningResult]:
        """维度 3: LoRA/模型权属检查."""
        info = self.model_gateway.query(model_name, source)
        if not info:
            return WarningResult(
                warning_type="lora_rights",
                severity="medium",
                title=f"模型 '{model_name}' 来源不明",
                description="无法确认该模型的授权状态，建议使用前核实。",
                matched_entity=model_name,
                confidence=50.0,
                suggestion="请在模型来源网站核实授权协议。",
            )

        if not info.allows_commercial:
            return WarningResult(
                warning_type="lora_rights",
                severity="high",
                title=f"模型 '{model_name}' 不允许商用",
                description=f"该模型授权类型为 '{info.license_type}'，{'需要署名' if info.requires_attribution else '不可商用'}。",
                matched_entity=model_name,
                confidence=90.0,
                suggestion="请更换允许商用的模型或获取授权。",
            )

        return None

    async def check_trademark(self, text: str, jurisdiction: str = "cn") -> list[WarningResult]:
        """维度 4: 商标/Logo 碰撞检测."""
        warnings = []
        results = await self.tm_gateway.search(text, jurisdiction=jurisdiction)

        for r in results:
            if r.similarity > 50.0:
                warnings.append(WarningResult(
                    warning_type="trademark_conflict",
                    severity="high" if r.similarity > 80 else "medium",
                    title=f"检测到商标冲突: '{r.mark_name}'",
                    description=f"与{'注册' if r.status == 'registered' else '申请中'}商标 '{r.mark_name}' 相似度 {r.similarity:.1f}%。",
                    matched_entity=r.mark_name,
                    confidence=r.similarity,
                    suggestion=f"建议修改标题/描述，避免使用 '{r.mark_name}' 相关词汇。",
                ))

        return warnings

    async def check_all(self, user_id: str, work_id: Optional[str] = None,
                        prompt: Optional[str] = None,
                        reference_images: Optional[list[str]] = None,
                        model_name: Optional[str] = None,
                        work_title: str = "") -> list[RiskWarning]:
        """统一检测入口 — 编排四个维度."""
        results = []

        # 维度 1: 提示词检测
        if prompt:
            for wr in self.check_prompt(prompt, work_title):
                results.append(self._to_risk_warning(user_id, work_id, wr))

        # 维度 2: 参考图检测
        if reference_images and len(reference_images) > 0:
            ref_hash = reference_images[0]
            # TODO: 从 DB 查同用户已有作品哈希列表
            existing_hashes: list[str] = []
            wr = self.check_reference_image(ref_hash, existing_hashes)
            if wr:
                results.append(self._to_risk_warning(user_id, work_id, wr))

        # 维度 3: 模型权属检查
        if model_name:
            wr = self.check_model(model_name)
            if wr:
                results.append(self._to_risk_warning(user_id, work_id, wr))

        # 维度 4: 商标碰撞 (异步)
        text_to_check = f"{prompt or ''} {work_title}".strip()
        if text_to_check:
            for wr in await self.check_trademark(text_to_check):
                results.append(self._to_risk_warning(user_id, work_id, wr))

        return results

    async def batch_check(self, items: list[dict], user_id: str, db: Session) -> list[dict]:
        """批量侵权检测 — 对多个作品/提示词组合并行检测.

        items: [{"work_id": ..., "prompt": ..., "work_title": ..., "model_name": ...}, ...]
        返回: [{"work_id", "warnings": [...], "status": "ok"|"error"}]
        """
        from app.models.work import Work

        results: list[dict] = []
        service = RiskWarningService()

        for item in items:
            work_id = item.get("work_id") or item.get("workId")
            prompt = item.get("prompt")
            work_title = item.get("work_title") or item.get("workTitle") or ""
            model_name = item.get("model_name") or item.get("modelName")
            reference_images = item.get("reference_images") or item.get("referenceImages")

            try:
                warnings = await service.check_all(
                    user_id=user_id,
                    work_id=work_id,
                    prompt=prompt,
                    reference_images=reference_images,
                    model_name=model_name,
                    work_title=work_title,
                )
                warning_dicts = [
                    {
                        "warning_type": w.warning_type,
                        "severity": w.severity,
                        "title": w.title,
                        "description": w.description,
                        "matched_entity": w.matched_entity,
                        "confidence": w.confidence,
                        "suggestion": w.suggestion,
                    }
                    for w in warnings
                ]
                results.append({
                    "work_id": work_id,
                    "warnings": warning_dicts,
                    "warning_count": len(warning_dicts),
                    "status": "ok",
                })
            except Exception as exc:
                results.append({
                    "work_id": work_id,
                    "warnings": [],
                    "warning_count": 0,
                    "status": "error",
                    "error": str(exc),
                })

        return results

    @staticmethod
    def _to_risk_warning(user_id: str, work_id: Optional[str], wr: WarningResult) -> RiskWarning:
        return RiskWarning(
            user_id=user_id,
            work_id=work_id,
            warning_type=wr.warning_type,
            severity=wr.severity,
            title=wr.title,
            description=wr.description,
            matched_entity=wr.matched_entity,
            confidence=wr.confidence,
            suggestion=wr.suggestion,
        )

    @staticmethod
    def _hamming_similarity(target_hash: str, hashes: list[str]) -> float:
        """计算目标哈希与一组哈希的最大汉明距离相似度 (简化版).

        v1: 使用十六进制字符串的汉明距离近似. 实际应使用感知哈希.
        """
        if not hashes:
            return 0.0

        try:
            target = int(target_hash, 16) if target_hash else 0
        except ValueError:
            return 0.0

        # 假设 64-bit hash
        bit_width = 64
        max_sim = 0.0
        for h in hashes:
            try:
                val = int(h, 16) if h else 0
                xor = target ^ val
                # Count differing bits
                diff_bits = bin(xor).count('1')
                sim = ((bit_width - diff_bits) / bit_width * 100)
                max_sim = max(max_sim, sim)
            except ValueError:
                continue
        return max_sim

    @staticmethod
    def _cat_label(cat: str) -> str:
        labels = {"trademark": "商标", "character": "角色", "artist_style": "艺术家风格"}
        return labels.get(cat, cat)

    @staticmethod
    def _get_suggestion(cat: str, entity: str) -> str:
        suggestions = {
            "trademark": f"建议修改标题/描述，避免使用 '{entity}' 相关词汇。",
            "character": f"建议避免使用角色 '{entity}' 作为创作参考。",
            "artist_style": f"'{entity}' 可能涉及艺术家风格模仿，注意版权风险。",
        }
        return suggestions.get(cat, "建议修改创作方向。")


def detect_burnout_risk(db, user_id: str) -> BurnoutRisk:
    """基于最近 7 天健康数据检测 burnout 风险."""
    today = date.today()
    week_ago = today - timedelta(days=7)

    metrics = db.query(HealthMetric).filter(
        HealthMetric.user_id == user_id,
        HealthMetric.recorded_date >= week_ago,
        HealthMetric.recorded_date <= today,
    ).order_by(HealthMetric.recorded_date.desc()).all()

    factors = []
    score = 0.0

    if not metrics:
        return BurnoutRisk(risk_level="low", score=10, factors=["暂无健康数据"], recommendation="建议开始记录每日工作时长")

    avg_hours = sum(m.daily_work_hours for m in metrics) / len(metrics)
    avg_mood = sum(m.mood_score or 5 for m in metrics) / len(metrics)
    break_rate = sum(1 for m in metrics if m.has_break_taken) / len(metrics)
    total_works = sum(m.works_created for m in metrics)

    if avg_hours > 10:
        factors.append(f"日均工作{avg_hours:.1f}小时（>10h危险线）")
        score += 35
    elif avg_hours > 8:
        factors.append(f"日均工作{avg_hours:.1f}小时（接近饱和）")
        score += 20

    if avg_mood < 4:
        factors.append(f"平均心情{avg_mood:.1f}/10（偏低）")
        score += 25
    elif avg_mood < 6:
        factors.append(f"平均心情{avg_mood:.1f}/10（一般）")
        score += 10

    if break_rate < 0.3:
        factors.append(f"休息时间占比仅{break_rate*100:.0f}%（建议>30%）")
        score += 20

    if total_works == 0 and avg_hours > 4:
        factors.append("工作时长长但产出为0（可能无效加班）")
        score += 20

    score = min(score, 100)

    if score >= 60:
        risk = "high"
        rec = "建议立即休息1-2天，减少每日工作至6小时内，安排运动或社交活动恢复精力。"
    elif score >= 30:
        risk = "medium"
        rec = "注意劳逸结合，确保每天有午休时间，每周至少安排1天完全休息。"
    else:
        risk = "low"
        rec = "当前状态良好，继续保持健康的工作节奏。"

    return BurnoutRisk(
        risk_level=risk,
        score=round(score),
        factors=factors,
        recommendation=rec,
    )
