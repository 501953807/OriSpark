"""指纹检测模块 — 视频/音频/文本指纹."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.monitor import MonitorResult
from app.models.video_fingerprint import VideoFrameFingerprint
from app.schemas.monitor import (
    FingerprintRequest, FingerprintResponse,
    FingerprintCompareRequest, FingerprintCompareResponse,
    VideoFingerprintMatch, VideoFingerprintScanResponse,
    AudioFingerprintGenerateResponse, AudioMatch, AudioScanResponse,
    TextPlagiarismMatch, TextPlagiarismScanResponse,
    DeltaDetectionRequest, DeltaDetectionResult, DeltaDetectionResponse,
)
from app.schemas.common import ApiResponse
from app.services.embedding_service import (
    compute_all_fingerprints, hamming_distance, compute_similarity,
)
from app.services.hasher import compute_sha256

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 15


class FingerprintModule:
    """多模态指纹检测模块."""

    def __init__(self, db: Session):
        self.db = db

    # ---- 视觉指纹 ----

    def compute(self, data: FingerprintRequest) -> ApiResponse:
        """计算并存储作品的感知哈希指纹."""
        work = self.db.query(Work).filter(Work.id == data.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        if not work.file_path or not work.file_path.exists():
            raise HTTPException(status_code=400, detail="作品文件不存在")
        fingerprints = compute_all_fingerprints(work.file_path)
        for fp_type, fp_hash in fingerprints.items():
            existing = self.db.query(VideoFrameFingerprint).filter(
                VideoFrameFingerprint.video_work_id == work.id,
                VideoFrameFingerprint.hash_type == fp_type,
            ).first()
            if existing:
                existing.perceptual_hash = fp_hash
            else:
                self.db.add(VideoFrameFingerprint(
                    video_work_id=work.id,
                    hash_type=fp_type,
                    perceptual_hash=fp_hash,
                    frame_number=0,
                    timestamp=0.0,
                ))
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=FingerprintResponse(
            work_id=work.id,
            fingerprints={k: v[:16] for k, v in fingerprints.items()},
        ))

    def compare(self, data: FingerprintCompareRequest) -> ApiResponse:
        """比较两个作品的指纹相似度."""
        work_a = self.db.query(Work).filter(Work.id == data.work_id_a).first()
        work_b = self.db.query(Work).filter(Work.id == data.work_id_b).first()
        if not work_a or not work_b:
            raise HTTPException(status_code=404, detail="作品不存在")
        fps_a = self.db.query(VideoFrameFingerprint).filter(
            VideoFrameFingerprint.video_work_id == data.work_id_a
        ).all()
        fps_b = self.db.query(VideoFrameFingerprint).filter(
            VideoFrameFingerprint.video_work_id == data.work_id_b
        ).all()
        if not fps_a or not fps_b:
            return ApiResponse(data=FingerprintCompareResponse(similarity=0.0))
        best_distance = float("inf")
        for fp_a, fp_b in zip(fps_a, fps_b):
            dist = hamming_distance(fp_a.perceptual_hash, fp_b.perceptual_hash)
            if dist < best_distance:
                best_distance = dist
        similarity = max(0, 100 - best_distance * 5)
        return ApiResponse(data=FingerprintCompareResponse(similarity=similarity))

    # ---- 视频指纹扫描 ----

    def scan_video(self, task_id: str) -> ApiResponse:
        """Scan for video fingerprint matches."""
        from app.models.monitor import MonitorTask
        task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="监测任务不存在")
        work = self.db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        video_work_ids = self.db.query(VideoFrameFingerprint.video_work_id).distinct().all()
        video_work_ids = [r[0] for r in video_work_ids]
        source_fps = (
            self.db.query(VideoFrameFingerprint)
            .filter(VideoFrameFingerprint.video_work_id == work.id)
            .order_by(VideoFrameFingerprint.frame_number)
            .all()
        )
        matches = []
        total_compared = 0
        for candidate_id in video_work_ids:
            if candidate_id == work.id:
                continue
            candidate_fps = (
                self.db.query(VideoFrameFingerprint)
                .filter(VideoFrameFingerprint.video_work_id == candidate_id)
                .order_by(VideoFrameFingerprint.frame_number)
                .all()
            )
            total_compared += 1
            source_by_type: dict = {}
            for fp in source_fps:
                source_by_type.setdefault(fp.hash_type, []).append(
                    (fp.frame_number, fp.perceptual_hash, fp.timestamp or 0.0)
                )
            candidate_by_type: dict = {}
            for fp in candidate_fps:
                candidate_by_type.setdefault(fp.hash_type, []).append(
                    (fp.frame_number, fp.perceptual_hash, fp.timestamp or 0.0)
                )
            best_distance = float("inf")
            matched_frames = 0
            total_candidate_frames = len(candidate_fps)
            best_hash_type = None
            for hash_type in source_by_type:
                if hash_type not in candidate_by_type:
                    continue
                source_frames = source_by_type[hash_type]
                cand_frames = candidate_by_type[hash_type]
                frame_matches = 0
                for sf in source_frames:
                    for cf in cand_frames:
                        if sf[0] == cf[0]:
                            dist = hamming_distance(sf[1], cf[1])
                            if dist <= MATCH_THRESHOLD:
                                frame_matches += 1
                            if dist < best_distance:
                                best_distance = dist
                if frame_matches > matched_frames:
                    matched_frames = frame_matches
                    best_hash_type = hash_type
            if matched_frames > 0 and best_distance <= MATCH_THRESHOLD:
                candidate_work = self.db.query(Work).filter(Work.id == candidate_id).first()
                if candidate_work:
                    similarity = compute_similarity(
                        source_fps[0].perceptual_hash if source_fps else "",
                        candidate_fps[0].perceptual_hash if candidate_fps else "",
                    ) if source_fps and candidate_fps else 0.0
                    video_match = VideoFingerprintMatch(
                        video_work_id=candidate_id,
                        video_title=candidate_work.title,
                        frame_number=candidate_fps[0].frame_number if candidate_fps else 0,
                        timestamp=candidate_fps[0].timestamp if candidate_fps else None,
                        perceptual_hash=candidate_fps[0].perceptual_hash if candidate_fps else "",
                        hamming_distance=int(best_distance),
                        similarity=similarity,
                        matched_frames=matched_frames,
                        total_frames=total_candidate_frames,
                    )
                    matches.append(video_match)
                    now = datetime.now(timezone.utc)
                    monitor_result = MonitorResult(
                        task_id=task.id,
                        matched_url=f"https://{candidate_work.file_path}",
                        matched_title=f"视频指纹匹配: {candidate_work.title} ({similarity:.1f}% 相似度)",
                        similarity=similarity,
                        found_at=now,
                        status="pending_review",
                        match_type="video_fingerprint",
                        confidence=round(similarity, 2),
                        notes=(
                            f"[Video Fingerprint] Matched {matched_frames}/{total_candidate_frames} "
                            f"frames (threshold <= {MATCH_THRESHOLD} bits). "
                            f"Hash type: {best_hash_type}"
                        ),
                    )
                    self.db.add(monitor_result)
        matches.sort(key=lambda m: m.similarity, reverse=True)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"Video fingerprint scan complete: {len(matches)} matches from {total_compared} works",
            data=VideoFingerprintScanResponse(
                matches=matches,
                total_compared=total_compared,
                match_threshold=MATCH_THRESHOLD,
            ),
        )

    # ---- 音频指纹 ----

    def generate_audio(self, task_id: str) -> ApiResponse:
        """Extract audio metadata and create a spectral fingerprint."""
        from app.models.monitor import MonitorTask
        task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="监测任务不存在")
        work = self.db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        if work.file_type not in ("audio", "video"):
            raise HTTPException(status_code=400, detail="仅支持音频/视频作品")
        sha256 = compute_sha256(str(work.file_path)) if work.file_path else ""
        return ApiResponse(data=AudioFingerprintGenerateResponse(
            work_id=work.id,
            fingerprint_hash=sha256[:32],
            duration=None,
            sample_rate=None,
        ))

    def scan_audio(self, task_id: str, top_n: int = 20) -> ApiResponse:
        """Scan for audio fingerprint matches."""
        from app.models.monitor import MonitorTask
        task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="监测任务不存在")
        work = self.db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        matches = []
        for other_work in self.db.query(Work).filter(
            Work.id != work.id,
            Work.file_type.in_(["audio", "video"]),
        ).limit(top_n).all():
            if other_work.sha256 and work.sha256:
                sim = 100.0 if other_work.sha256[:16] == work.sha256[:16] else 0.0
                if sim > 0:
                    matches.append(AudioMatch(
                        work_id=other_work.id,
                        title=other_work.title,
                        similarity=sim,
                    ))
        return ApiResponse(data=AudioScanResponse(matches=matches))

    def list_audio_matches(self, work_id: Optional[str] = None, min_confidence: float = 0.0) -> ApiResponse:
        """获取音频匹配历史."""
        query = self.db.query(MonitorResult).filter(
            MonitorResult.match_type == "audio_fingerprint",
            MonitorResult.similarity >= min_confidence,
        )
        if work_id:
            task_ids = self.db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)
            query = query.filter(MonitorResult.task_id.in_(task_ids))
        results = query.order_by(MonitorResult.similarity.desc()).limit(50).all()
        return ApiResponse(data=[
            {
                "result_id": r.id,
                "matched_title": r.matched_title or "",
                "similarity": r.similarity,
                "found_at": r.found_at.isoformat() if r.found_at else None,
            }
            for r in results
        ])

    # ---- 文本抄袭检测 ----

    def scan_text_plagiarism(
        self,
        work_ids: list[str] = [],
        top_n: int = 20,
    ) -> ApiResponse:
        """Scan for text plagiarism among works with text content."""
        if work_ids:
            works_to_scan = self.db.query(Work).filter(Work.id.in_(work_ids)).all()
        else:
            works_to_scan = self.db.query(Work).filter(
                Work.status == "active",
                or_(
                    Work.synopsis.isnot(None),
                    Work.description.isnot(None),
                    Work.custom_metadata.isnot(None),
                ),
            ).all()
        if not works_to_scan:
            raise HTTPException(status_code=404, detail="未找到包含文本内容的作品")
        now = datetime.now(timezone.utc)
        all_text_works: list = []
        for w in works_to_scan:
            texts: list = []
            if w.synopsis:
                texts.append(w.synopsis)
            if w.description:
                texts.append(w.description)
            if w.custom_metadata and "text_content" in w.custom_metadata:
                texts.append(str(w.custom_metadata["text_content"]))
            if texts:
                tokens = _tokenize_text(" ".join(texts))
                if tokens:
                    all_text_works.append((w, tokens))
        if not all_text_works:
            raise HTTPException(status_code=400, detail="所选作品不包含可分析的文本内容")
        corpus_size = len(all_text_works)
        tfidf_vectors: dict = {}
        for work_obj, tokens in all_text_works:
            vec = _compute_tfidf_vector(tokens, corpus_size)
            if vec:
                tfidf_vectors[work_obj.id] = vec
        all_matches: list = []
        for scan_work_id in [w.id for w, _ in all_text_works]:
            source_vec = tfidf_vectors.get(scan_work_id)
            if not source_vec:
                continue
            for other_work_id, other_vec in tfidf_vectors.items():
                if other_work_id == scan_work_id:
                    continue
                sim = _cosine_similarity_sparse(source_vec, other_vec)
                if sim > 0.05:
                    all_matches.append((scan_work_id, other_work_id, sim, len(source_vec & other_vec)))
        all_matches.sort(key=lambda x: x[2], reverse=True)
        top_matches = all_matches[:top_n]
        reported: set = set()
        new_results = []
        for source_id, matched_id, sim, shared_terms in top_matches:
            normalized_sim = round(sim * 100, 2)
            if normalized_sim < 10.0:
                continue
            from app.models.monitor import MonitorTask as MT
            task = self.db.query(MT).filter(MT.work_id == source_id).first()
            if not task:
                continue
            match_url = f"text-match://{matched_id}"
            dedup_key = f"{task.id}:{match_url}"
            if dedup_key in reported:
                continue
            reported.add(dedup_key)
            matched_work = self.db.query(Work).filter(Work.id == matched_id).first()
            if not matched_work:
                continue
            result = MonitorResult(
                task_id=task.id,
                matched_url=match_url,
                matched_title=f"文本相似度匹配: {matched_work.title} ({normalized_sim}%)",
                similarity=normalized_sim,
                found_at=now,
                status="pending_review",
                match_type="text_similarity",
                confidence=normalized_sim,
                notes=(
                    f"[Text Plagiarism] shared_terms={shared_terms}, "
                    f"tfidf_cosine={sim:.6f}, normalized={normalized_sim}%"
                ),
            )
            new_results.append(result)
        self.db.add_all(new_results)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        response_matches = []
        for source_id, matched_id, sim, shared_terms in top_matches:
            normalized_sim = round(sim * 100, 2)
            matched_work = self.db.query(Work).filter(Work.id == matched_id).first()
            if not matched_work:
                continue
            response_matches.append(TextPlagiarismMatch(
                matched_work_id=matched_id,
                matched_title=matched_work.title,
                cosine_similarity=round(sim, 6),
                shared_terms=shared_terms,
                match_percentage=normalized_sim,
            ))
        response_matches = response_matches[:top_n]
        return ApiResponse(
            message=f"Text plagiarism scan: {len(response_matches)} matches from {corpus_size} text works",
            data=TextPlagiarismScanResponse(
                matches=response_matches,
                total_compared=corpus_size,
                top_n=top_n,
            ),
        )

    def list_text_matches(
        self,
        work_id: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> ApiResponse:
        """获取文本相似度检测历史记录."""
        from app.models.monitor import MonitorTask as MT
        query = self.db.query(MonitorResult).filter(
            MonitorResult.match_type == "text_similarity",
            MonitorResult.similarity >= min_similarity,
        )
        if work_id:
            task_ids = self.db.query(MT.id).filter(MT.work_id == work_id)
            query = query.filter(MonitorResult.task_id.in_(task_ids))
        results = (
            query.order_by(MonitorResult.similarity.desc())
            .limit(200)
            .all()
        )
        matches = []
        for r in results:
            notes = r.notes or ""
            shared_terms = 0
            cosine_sim = r.similarity / 100.0 if r.similarity else 0.0
            if "shared_terms=" in notes:
                try:
                    shared_terms = int(notes.split("shared_terms=")[1].split(",")[0])
                except (ValueError, IndexError):
                    pass
            matches.append({
                "result_id": r.id,
                "matched_url": r.matched_url.replace("text-match://", ""),
                "matched_title": r.matched_title or "",
                "similarity": r.similarity,
                "cosine_similarity": round(cosine_sim, 6),
                "shared_terms": shared_terms,
                "found_at": r.found_at.isoformat() if r.found_at else None,
                "status": r.status,
            })
        return ApiResponse(
            message=f"Found {len(matches)} text plagiarism matches",
            data=matches,
        )


# ---- 辅助函数（从 monitor_service.py 迁移）----

def _tokenize_text(text: str) -> list[str]:
    """简单分词."""
    import re
    return re.findall(r'\w+', text.lower())


def _compute_tfidf_vector(doc_tokens: list[str], corpus_size: int) -> dict[str, float]:
    """计算 TF-IDF 向量."""
    from collections import Counter
    tf = Counter(doc_tokens)
    total = len(doc_tokens)
    return {token: count / total for token, count in tf.items()}


def _cosine_similarity_sparse(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """计算稀疏向量余弦相似度."""
    import math
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    if not intersection:
        return 0.0
    dot_product = sum(vec_a[k] * vec_b[k] for k in intersection)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
