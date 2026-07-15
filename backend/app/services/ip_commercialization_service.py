from sqlalchemy.orm import Session

from app.models.ip_commercialization import IPAsset, IPEvaluationStage


def calculate_ip_score(originality: float, demand: float,
                        competition: float, potential: float) -> float:
    """IP综合评分 = 原创性×0.3 + 需求×0.3 + (100-竞争)×0.2 + 变现×0.2."""
    return round(originality * 0.3 + demand * 0.3 + (100 - competition) * 0.2 + potential * 0.2, 1)


def estimate_brand_premium(follower_count: int, engagement_rate: float, category: str) -> float:
    """品牌溢价估算: 输入粉丝量/互动率/领域 → 预估15-40%溢价空间."""
    base = 15.0
    if follower_count > 100000:
        base += 10
    elif follower_count > 10000:
        base += 5
    if engagement_rate > 5.0:
        base += 10
    elif engagement_rate > 2.0:
        base += 5
    return min(round(base, 1), 40.0)


def recommend_trademark_classes(creator_type: str) -> list[str]:
    """按创作者类型推荐商标类别."""
    mapping = {
        "illustrator": ["第9类(数码产品)", "第16类(出版物)", "第25类(服装)"],
        "musician": ["第9类(录音制品)", "第16类(乐谱)", "第41类(娱乐服务)"],
        "photographer": ["第9类(数码照片)", "第16类(印刷品)"],
        "writer": ["第16类(出版物)", "第41类(教育娱乐)"],
        "game_developer": ["第9类(软件)", "第16类(出版物)", "第25类(服装)", "第28类(玩具)"],
    }
    return mapping.get(creator_type, ["第9类", "第16类"])


def create_ip_assessment(db: Session, req: dict) -> IPAsset:
    score = calculate_ip_score(
        req["originality_score"], req["market_demand_score"],
        req["competition_density"], req["monetization_potential"],
    )
    asset = IPAsset(
        work_id=req["work_id"],
        ip_name=req["ip_name"],
        originality_score=req["originality_score"],
        market_demand_score=req["market_demand_score"],
        competition_density=req["competition_density"],
        monetization_potential=req["monetization_potential"],
        overall_score=score,
        trademark_classes=recommend_trademark_classes(req.get("creator_type", "illustrator")),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
