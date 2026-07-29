"""无罪证明 API 路由。

端点:
- POST /api/innocence-proof/build - 构建无罪证明
- GET /api/innocence-proof/{id} - 获取无罪证明详情

用于版权保护场景中的反侵权证据链生成，协助创作者证明其作品的原始创作权。
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.innocence_proof import (
    InnocenceProofCreate, InnocenceProofResponse, InnocenceProofListResponse,
)
from app.models.innocence_proof import InnocenceProof
from app.models.work import Work


router = APIRouter(prefix="/innocence-proof", tags=["innocence_proof"])


def get_innocence_proof_by_id(db: Session, proof_id: str) -> Optional[InnocenceProof]:
    """根据ID查询无罪证明."""
    return db.query(InnocenceProof).filter(InnocenceProof.id == proof_id).first()


@router.post("/build", response_model=ApiResponse)
async def build_innocence_proof(
    data: InnocenceProofCreate,
    db: Session = Depends(get_db),
):
    """
    构建无罪证明。

    创建一个新的无罪证明记录，关联指定作品，并生成初步的证据摘要。
    需要携带 Authorization: Bearer <token> header 进行认证。

    Args:
        data: 包含 work_id、evidence_document_url、summary_text 和 status 的请求体

    Returns:
        ApiResponse: 包含创建的 InnocenceProofResponse 数据

    Raises:
        HTTPException 400: 如果 work_id 无效
        HTTPException 401: 如果缺少或无效的认证凭证
    """
    # 验证作品是否存在
    work = db.query(Work).filter(Work.id == data.work_id).first()
    if not work:
        raise HTTPException(status_code=400, detail="无效的作品ID")

    # 创建无罪证明
    proof = InnocenceProof(
        work_id=data.work_id,
        evidence_document_url=data.evidence_document_url,
        summary_text=data.summary_text,
        status=data.status,
    )

    try:
        db.add(proof)
        db.commit()
        db.refresh(proof)
        return ApiResponse(data=proof, message="无罪证明构建成功")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"构建无罪证明失败: {str(e)}")


@router.get("/{id}", response_model=ApiResponse)
async def get_innocence_proof(
    id: str = Path(..., description="无罪证明ID", min_length=1, max_length=32),
    db: Session = Depends(get_db),
):
    """
    获取指定ID的无罪证明详情。

    Args:
        id: 无罪证明的唯一标识符

    Returns:
        ApiResponse: 包含 InnocenceProofResponse 数据

    Raises:
        HTTPException 404: 如果找不到对应的无罪证明
        HTTPException 401: 如果缺少或无效的认证凭证
    """
    proof = get_innocence_proof_by_id(db, id)
    if not proof:
        raise HTTPException(status_code=404, detail="无罪证明不存在")
    return ApiResponse(data=proof)


@router.get("/", response_model=InnocenceProofListResponse)
async def list_innocence_proofs(
    work_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """
    列出无罪证明列表。

    支持通过 work_id 和 status 进行过滤。

    Args:
        work_id: 按作品ID过滤
        status: 按状态过滤 (pending/completed/reviewed)
        page: 页码 (从1开始)
        page_size: 每页数量
        db: 数据库会话

    Returns:
        InnocenceProofListResponse: 包含分页后的无罪证明列表
    """
    query = db.query(InnocenceProof)

    if work_id:
        query = query.filter(InnocenceProof.work_id == work_id)
    if status:
        query = query.filter(InnocenceProof.status == status)

    total = query.count()
    proofs = query.order_by(InnocenceProof.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return InnocenceProofListResponse(
        items=proofs,
        total=total,
        page=page,
        page_size=page_size,
    )
