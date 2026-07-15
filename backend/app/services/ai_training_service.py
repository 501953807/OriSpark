from sqlalchemy.orm import Session

from app.models.ai_training_license import AITrainingLicense, CCProtocol

AI_EXCLUDE_CLAUSE_TEMPLATE = """AI Training Exclusion Clause:
The Licensor expressly prohibits the use of this Work, including any derivatives,
for the purpose of training, fine-tuning, or improving any Artificial Intelligence
or Machine Learning model, including but not limited to generative AI systems.
Any unauthorized use for AI training constitutes a material breach of this agreement."""


def generate_exclude_clause(cc_protocol: CCProtocol) -> str:
    """根据CC协议生成AI训练排除条款."""
    if cc_protocol == CCProtocol.CC0:
        return AI_EXCLUDE_CLAUSE_TEMPLATE
    elif cc_protocol == CCProtocol.CC_BY_NC:
        return AI_EXCLUDE_CLAUSE_TEMPLATE + "\n(Note: CC-BY-NC already restricts commercial use.)"
    return ""


def upsert_ai_license(db: Session, work_id: str, enabled: bool,
                       cc_protocol: CCProtocol = CCProtocol.CC0,
                       price_per_use_cents: int = 5) -> AITrainingLicense:
    license = db.query(AITrainingLicense).filter(
        AITrainingLicense.work_id == work_id
    ).first()
    if not license:
        license = AITrainingLicense(
            work_id=work_id,
            enabled=enabled,
            cc_protocol=cc_protocol,
            price_per_use_cents=price_per_use_cents,
            exclude_ai_training_clause=generate_exclude_clause(cc_protocol) if enabled else None,
        )
        db.add(license)
    else:
        license.enabled = enabled
        license.cc_protocol = cc_protocol
        license.price_per_use_cents = price_per_use_cents
        if enabled:
            license.exclude_ai_training_clause = generate_exclude_clause(cc_protocol)
        else:
            license.exclude_ai_training_clause = None
    db.commit()
    db.refresh(license)
    return license
