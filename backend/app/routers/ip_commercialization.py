from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.services.ip_commercialization_service import create_ip_assessment, estimate_brand_premium
from app.services.contract_generator import generate_contract_text

router = APIRouter(prefix="/ip-commercialization", tags=["ip-commercialization"])


@router.post("/assess", response_model=dict)
def post_ip_assessment(data: dict, db: Session = Depends(get_db)):
    asset = create_ip_assessment(db, data)
    return {"id": asset.id, "overall_score": asset.overall_score}


@router.post("/brand-premium")
def calc_brand_premium(follower_count: int, engagement_rate: float, category: str):
    premium = estimate_brand_premium(follower_count, engagement_rate, category)
    return {"estimated_premium_percent": premium}


# ============================================================================
# v2: 授权合同与到期提醒
# ============================================================================


@router.get("/licenses/{license_id}/contract")
def get_license_contract(license_id: str, db: Session = Depends(get_db)):
    """生成/预览授权合同."""
    from app.models.ip_commercialization import IpLicense
    license = db.query(IpLicense).filter(IpLicense.id == license_id).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    contract_text = generate_contract_text({
        "licensor_name": "授权方",
        "licensee_name": "被授权方",
        "work_title": getattr(license, 'work_title', "作品"),
        "license_type": getattr(license, 'license_type', "非独占"),
        "territory": getattr(license, 'territory', "中国大陆"),
        "start_date": license.start_date.strftime("%Y-%m-%d") if hasattr(license, 'start_date') and license.start_date else "",
        "end_date": license.end_date.strftime("%Y-%m-%d") if hasattr(license, 'end_date') and license.end_date else "",
        "channels": getattr(license, 'channels_json', ["网络"]) or ["网络"],
        "payment_type": getattr(license, 'payment_type', "一次性"),
        "amount_yuan": float(getattr(license, 'amount_yuan', 0) or 0),
    })
    return {"contract_text": contract_text}


@router.get("/expiring-soon")
def get_expiring_licenses(days: int = 30, db: Session = Depends(get_db)):
    """即将到期的授权列表."""
    from app.models.ip_commercialization import IpLicense

    cutoff = datetime.utcnow() + timedelta(days=days)
    licenses = db.query(IpLicense).filter(
        IpLicense.status == "active",
    ).all()

    result = []
    for lic in licenses:
        end_date = getattr(lic, 'end_date', None)
        if end_date and end_date <= cutoff:
            days_remaining = (end_date - datetime.utcnow()).days
            result.append({
                "id": lic.id,
                "work_title": getattr(lic, 'work_title', ""),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining,
            })

    result.sort(key=lambda x: x["days_remaining"])
    return {"licenses": result}


@router.post("/licenses/{license_id}/renew")
def renew_license(license_id: str, new_end_date: str, db: Session = Depends(get_db)):
    """续约授权."""
    from app.models.ip_commercialization import IpLicense
    license = db.query(IpLicense).filter(IpLicense.id == license_id).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")

    try:
        license.end_date = datetime.fromisoformat(new_end_date)
    except ValueError:
        license.end_date = datetime.strptime(new_end_date, "%Y-%m-%d")
    license.status = "active"
    db.commit()
    db.refresh(license)
    return {"id": license.id, "end_date": license.end_date.isoformat()}
