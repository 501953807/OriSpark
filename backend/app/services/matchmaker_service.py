"""智能匹配算法服务."""

import json

from sqlalchemy.orm import Session

from app.models.matchmaking import MatchRequest


def extract_keywords(text: str) -> set:
    """简单关键词提取 — 按中文单字和英文单词分割."""
    if not text:
        return set()
    words = set()
    for char in text:
        if '一' <= char <= '鿿':
            words.add(char)
        elif char.isalnum():
            words.add(char.strip().lower())
    return words


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard 相似度."""
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def compute_match_score(request: MatchRequest, listing_data: dict) -> dict:
    """计算单个挂牌对某需求的匹配度.

    Returns: {"score": float, "matched_fields": dict}
    """
    score = 0.0
    matched_fields: dict = {}

    # 1. 类别匹配 (权重 0.25)
    if request.category and listing_data.get("category"):
        if request.category == listing_data["category"]:
            score += 0.25
            matched_fields["category"] = True
    elif not request.category:
        score += 0.125

    # 2. 创作者类型匹配 (权重 0.20)
    creator_type = listing_data.get("creator_type")
    if creator_type and listing_data.get("request_creator_type"):
        if creator_type == listing_data["request_creator_type"]:
            score += 0.20
            matched_fields["creator_type"] = True

    # 3. 价格区间匹配 (权重 0.30)
    price = listing_data.get("asking_price_yuan")
    budget_min = listing_data.get("budget_min")
    budget_max = listing_data.get("budget_max")
    if price is not None and budget_min is not None and budget_max is not None:
        if budget_min <= price <= budget_max:
            score += 0.30
            matched_fields["price_range"] = True
        elif price < budget_max * 1.2:
            score += 0.15
            matched_fields["price_range"] = "near"
    elif price is not None and not budget_min:
        score += 0.15

    # 4. 关键词相似度 (权重 0.25)
    keywords = extract_keywords(request.description or "")
    tags_raw = request.style_tags or []
    similarity = jaccard_similarity(keywords, set(tags_raw))
    score += 0.25 * similarity
    matched_fields["keywords"] = round(similarity, 3)

    return {
        "score": round(min(score, 1.0), 3),
        "matched_fields": matched_fields,
    }


def auto_match(db: Session, request_id: str) -> list[dict]:
    """自动匹配 — 返回所有 active 挂牌按匹配度排序."""
    from app.models.listing import Listing

    request = db.query(MatchRequest).filter(MatchRequest.id == request_id).first()
    if not request:
        raise ValueError(f"Match request {request_id} not found")

    listings = db.query(Listing).filter(Listing.status == "active").all()

    results = []
    for listing in listings:
        score_data = compute_match_score(request, {
            "category": listing.category if hasattr(listing, 'category') else None,
            "creator_type": getattr(listing, 'creator_type', None),
            "asking_price_yuan": float(listing.asking_price_yuan) if listing.asking_price_yuan else None,
            "budget_min": request.budget_min_yuan,
            "budget_max": request.budget_max_yuan,
            "request_creator_type": request.category,
        })
        if score_data["score"] >= 0.2:
            results.append({
                "listing_id": listing.id,
                "score": score_data["score"],
                "matched_fields": score_data["matched_fields"],
                "title": listing.title,
                "price": float(listing.asking_price_yuan),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


def get_match_score(db: Session, listing_id: str, request_id: str) -> dict:
    """查询单个挂牌对某需求的匹配度."""
    from app.models.listing import Listing

    request = db.query(MatchRequest).filter(MatchRequest.id == request_id).first()
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not request or not listing:
        raise ValueError("Listing or request not found")

    score_data = compute_match_score(request, {
        "category": listing.category if hasattr(listing, 'category') else None,
        "creator_type": getattr(listing, 'creator_type', None),
        "asking_price_yuan": float(listing.asking_price_yuan),
        "budget_min": request.budget_min_yuan,
        "budget_max": request.budget_max_yuan,
        "request_creator_type": request.category,
    })
    return {
        "listing_id": listing_id,
        "request_id": request_id,
        "score": score_data["score"],
        "matched_fields": score_data["matched_fields"],
    }
