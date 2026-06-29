"""服务层."""

from app.services.hasher import compute_sha256, compute_md5, verify_hash
from app.services.work_service import detect_file_type, generate_thumbnail, extract_exif, get_image_dimensions, get_all_metadata
from app.services.certificate_service import generate_certificate_pdf
from app.services.search_service import setup_fts5, search_works_fts
from app.services.websocket_manager import manager, ConnectionManager
from app.services.evidence_service import generate_evidence_package, generate_complaint_letter, generate_lawyer_letter
from app.services.c2pa_service import generate_c2pa_manifest, embed_c2pa_metadata, verify_c2pa_metadata
from app.services.auto_tag_service import auto_generate_tags, suggest_tags

__all__ = [
    "compute_sha256", "compute_md5", "verify_hash",
    "detect_file_type", "generate_thumbnail", "extract_exif", "get_image_dimensions", "get_all_metadata",
    "generate_certificate_pdf",
    "setup_fts5", "search_works_fts",
    "manager", "ConnectionManager",
    "generate_evidence_package", "generate_complaint_letter", "generate_lawyer_letter",
    "generate_c2pa_manifest", "embed_c2pa_metadata", "verify_c2pa_metadata",
    "auto_generate_tags", "suggest_tags",
]
