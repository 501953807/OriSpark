"""Video fingerprint service — frame extraction, perceptual hashing, and infringement scanning.

P3: Video creator fingerprint generation and comparison.
Implements: extract_frames (ffmpeg), pHash (DCT), dHash (difference),
             hamming distance, and cross-db scan_for_infringement.

Pure Python / Pillow / subprocess implementation — no ONNX or external ML dependencies.
"""

from __future__ import annotations

import dataclasses
import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional

from PIL import Image


# ============================================================================
# Data classes
# ============================================================================

@dataclasses.dataclass
class MatchResult:
    """Single infringement scan match result."""
    match_id: str
    similarity: float  # 0–100
    matched_frames: int
    first_match_frame: int
    source_url: Optional[str] = None


# ============================================================================
# Helper: FFT/DCT for pHash
# ============================================================================

def _dct_row(row: list[float]) -> list[float]:
    """1-D DCT-II of a single row."""
    n = len(row)
    out: list[float] = []
    for k in range(n):
        s = 0.0
        for j in range(n):
            s += row[j] * math.cos(math.pi * k * (2 * j + 1) / (2 * n))
        out.append(s)
    return out


def _dct2d(matrix: list[list[float]]) -> list[list[float]]:
    """2-D DCT-II (type II) via separable 1-D transforms."""
    tmp = [_dct_row(row) for row in matrix]
    # Transpose
    cols = len(tmp)
    rows = len(tmp[0]) if cols else 0
    transposed: list[list[float]] = [[0.0] * cols for _ in range(rows)]
    for i in range(rows):
        for j in range(cols):
            transposed[i][j] = tmp[j][i]
    return [_dct_row(r) for r in transposed]


def _to_int_list(val: int, width: int = 8) -> list[int]:
    """Convert an integer to a list of 0/1 bits (MSB-first), padded to width."""
    bits = [(val >> i) & 1 for i in range(width - 1, -1, -1)]
    return bits


# ============================================================================
# Core service
# ============================================================================

class VideoFingerprintService:
    """Video fingerprint computation and matching service.

    Public API:
        extract_frames(video_path, interval) -> list[frame_png_path]
        compute_phash(image_path) -> int
        compute_dhash(image_path) -> int
        hamming_distance(hash1, hash2) -> int
        scan_for_infringement(video_path, threshold) -> list[MatchResult]
    """

    # ------------------------------------------------------------------
    # Frame extraction (ffmpeg subprocess wrapper)
    # ------------------------------------------------------------------

    @staticmethod
    def extract_frames(video_path: str, interval: int = 2) -> list[str]:
        """Extract frames from a video at the given time interval using ffmpeg.

        Returns a list of absolute paths to PNG frame files inside a
        temporary directory.  The caller owns cleanup of the temp dir.
        """
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        probe_cmd = [
            "ffmpeg", "-i", video_path,
            "-map", "0:v:0", "-c:v", "copy",
            "-t", "00:00:01", "-f", "null", "-"
        ]
        result = subprocess.run(
            probe_cmd, capture_output=True, text=True, timeout=30
        )
        duration = None
        for line in (result.stderr or "").splitlines():
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if m:
                h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                duration = h * 3600 + mi * 60 + s
                break

        if duration is None:
            raise ValueError("Cannot determine video duration from ffmpeg probe.")

        if duration <= 0:
            raise ValueError(f"Video has zero duration: {video_path}")

        num_frames = max(1, int(duration / interval))

        tmpdir = tempfile.mkdtemp(prefix="vf_frames_")
        frame_pattern = os.path.join(tmpdir, "frame_%04d.png")
        fps_value = f"1/{interval}"

        cmd = [
            "ffmpeg",
            "-y", "-i", video_path,
            "-vf", f"fps={fps_value},scale=640:-1:flags=lanczos",
            "-frames:v", str(num_frames),
            frame_pattern,
        ]

        try:
            subprocess.run(
                cmd, capture_output=True, text=True, timeout=max(120, duration * 2)
            )
        except subprocess.TimeoutExpired:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise RuntimeError(f"ffmpeg timed out extracting frames from {video_path}")

        frames = sorted(Path(tmpdir).glob("frame_*.png"))
        if not frames:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise RuntimeError(f"No frames extracted from {video_path}")

        return [str(f) for f in frames]

    # ------------------------------------------------------------------
    # Perceptual hashing (pHash — DCT-based)
    # ------------------------------------------------------------------

    @staticmethod
    def compute_phash(image_path: str) -> int:
        """Compute 64-bit perceptual hash using 8x8 DCT low-frequency coefficients.

        Algorithm:
            1. Resize to 8x8, grayscale.
            2. Apply 2-D DCT-II.
            3. Take top-left 8x8 coefficients (low-frequency band).
            4. Compare each coefficient against the median → 1 bit per pixel.
            5. Pack into a 64-bit unsigned integer.
        """
        img = Image.open(image_path).convert("L")
        img = img.resize((8, 8), Image.LANCZOS)
        pixels = [float(v) for v in list(img.getdata())]

        # Build 8x8 matrix
        matrix = [pixels[i * 8:(i + 1) * 8] for i in range(8)]

        # 2-D DCT
        dct = _dct2d(matrix)

        # Median of all 64 coefficients
        flat = sorted(v for row in dct for v in row)
        median = (flat[31] + flat[32]) / 2.0

        # Thresholded bits → integer
        val = 0
        for i, row in enumerate(dct):
            for j, coeff in enumerate(row):
                if coeff > median:
                    val |= 1
                val <<= 1
        # The loop shifts one extra time, so trim to 64 bits
        val &= 0xFFFF_FFFF_FFFF_FFFF
        return val

    # ------------------------------------------------------------------
    # Difference hash (dHash)
    # ------------------------------------------------------------------

    @staticmethod
    def compute_dhash(image_path: str) -> int:
        """Compute 64-bit difference hash on a 9x8 grayscale image.

        Algorithm:
            1. Resize to 9x8, grayscale.
            2. For each row, compare pixel[i] vs pixel[i+1] → 1 bit if left < right.
            3. Pack 8 rows * 8 comparisons = 64 bits.
        """
        img = Image.open(image_path).convert("L")
        img = img.resize((9, 8), Image.LANCZOS)
        pixels = list(img.getdata())

        val = 0
        for row in range(8):
            for col in range(8):
                left = pixels[row * 9 + col]
                right = pixels[row * 9 + col + 1]
                val <<= 1
                if right > left:
                    val |= 1
        return val

    # ------------------------------------------------------------------
    # Hamming distance (bitwise XOR popcount)
    # ------------------------------------------------------------------

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """XOR popcount between two integer hashes."""
        xor = hash1 ^ hash2
        return bin(xor).count("1")

    # ------------------------------------------------------------------
    # Similarity helper
    # ------------------------------------------------------------------

    @staticmethod
    def similarity_for_distance(dist: int, total_bits: int = 64) -> float:
        """Convert hamming distance to a percentage similarity (0-100)."""
        if total_bits == 0:
            return 0.0
        return max(0.0, (1.0 - dist / total_bits) * 100.0)

    # ------------------------------------------------------------------
    # Full infringement scan
    # ------------------------------------------------------------------

    def scan_for_infringement(
        self,
        video_path: str,
        threshold: int = 10,
    ) -> list[MatchResult]:
        """Scan a video against the local fingerprint database for potential matches.

        Steps:
            1. Extract frames from the video file using ffmpeg.
            2. Compute pHash for each frame.
            3. Query VideoFrameFingerprint DB rows whose hash matches
               within the given hamming-distance threshold.
            4. Aggregate per-source results and return sorted MatchResult list.

        Args:
            video_path: Path to the video file to scan.
            threshold: Maximum hamming distance per frame to count as a match.
                       Typical range 8-15; lower = stricter.

        Returns:
            List of MatchResult, sorted by similarity descending.
        """
        # 1. Extract frames
        frame_paths = self.extract_frames(video_path)

        if not frame_paths:
            return []

        # 2. Compute pHash for each frame
        frame_hashes: list[tuple[str, int]] = []
        for idx, fp in enumerate(frame_paths):
            try:
                ph = self.compute_phash(fp)
                frame_hashes.append((fp, ph))
            except OSError:
                continue  # skip unreadable frames

        if not frame_hashes:
            return []

        # 3. Import SQLAlchemy at runtime to avoid circular imports
        from app.database import SessionLocal
        from app.models.video_fingerprint import VideoFrameFingerprint
        from app.models.work import Work

        db = SessionLocal()
        try:
            # Query all stored frame fingerprints in one pass
            all_fps = db.query(VideoFrameFingerprint).all()

            # Group by video_work_id for batch comparison
            groups: dict[str, list[VideoFrameFingerprint]] = {}
            for fp in all_fps:
                groups.setdefault(fp.video_work_id, []).append(fp)

            # Map each frame index → {video_work_id: total_matches}
            source_frame_hits: dict[str, dict[str, list[int]]] = {}

            for local_idx, (_, local_hash) in enumerate(frame_hashes):
                local_bits = local_hash.bit_count() if hasattr(local_hash, "bit_count") else bin(local_hash).count("1")

                for work_id, work_frames in groups.items():
                    matching_frame_numbers: list[int] = []
                    for wf in work_frames:
                        try:
                            stored_int = int(wf.perceptual_hash, 16)
                        except (ValueError, TypeError):
                            continue
                        dist = self.hamming_distance(local_hash, stored_int)
                        if dist <= threshold:
                            matching_frame_numbers.append(wf.frame_number)

                    if matching_frame_numbers:
                        source_frame_hits.setdefault(
                            work_id, {}
                        )[str(local_idx)] = matching_frame_numbers

            # 4. Aggregate per-source results
            results: list[MatchResult] = []
            for work_id, frame_map in source_frame_hits.items():
                matched_frames = len(frame_map)
                all_frame_numbers = []
                for nums in frame_map.values():
                    all_frame_numbers.extend(nums)

                work = db.query(Work).filter(Work.id == work_id).first()
                work_title = work.title if work else work_id

                # Overall similarity: average of per-frame match ratios
                avg_dist_sum = 0.0
                count_pairs = 0
                for fh_idx, fh_hash in frame_hashes:
                    for wid, wf_list in groups.items():
                        if wid != work_id:
                            continue
                        for wf in wf_list:
                            if wf.frame_number in all_frame_numbers:
                                try:
                                    stored_int = int(wf.perceptual_hash, 16)
                                    dist = self.hamming_distance(fh_hash, stored_int)
                                    avg_dist_sum += dist
                                    count_pairs += 1
                                except (ValueError, TypeError):
                                    pass

                overall_similarity = (
                    self.similarity_for_distance(
                        avg_dist_sum / count_pairs if count_pairs else 0, 64
                    )
                    if count_pairs
                    else 0.0
                )

                first_match = min(all_frame_numbers) if all_frame_numbers else 0

                results.append(MatchResult(
                    match_id=str(uuid.uuid4()),
                    similarity=round(overall_similarity, 2),
                    matched_frames=matched_frames,
                    first_match_frame=first_match,
                    source_url=work.file_path if work else None,
                ))

            results.sort(key=lambda r: r.similarity, reverse=True)
            return results

        finally:
            db.close()

    @staticmethod
    def _cleanup_temp_frames(frame_paths: list[str]) -> None:
        """Remove extracted frame files and their parent temp directory."""
        for fp in frame_paths:
            try:
                os.remove(fp)
            except OSError:
                pass
        if frame_paths:
            parent = os.path.dirname(frame_paths[0])
            try:
                shutil.rmtree(parent, ignore_errors=True)
            except OSError:
                pass
