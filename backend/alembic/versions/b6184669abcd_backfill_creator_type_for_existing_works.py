"""backfill_creator_type_for_existing_works

Revision ID: b6184669abcd
Revises: 59697f1647fd
Create Date: 2026-07-02 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b6184669abcd'
down_revision: Union[str, None] = '59697f1647fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Intelligently set creator_type for existing works based on file_type,
    exif_data, and custom_metadata.

    Logic:
      1. image + exif_data has CameraModel  -> photographer
      2. audio                              -> musician
      3. video                              -> video
      4. document + custom_metadata has CAD keywords -> craftsman
      5. document                           -> writer
      6. remaining (design/other/code etc.) -> illustrator
    """
    conn = op.get_bind()

    # 1. Photographer: image with CameraModel in exif_data
    op.execute("""
        UPDATE works
        SET creator_type = 'photographer'
        WHERE file_type = 'image'
          AND exif_data IS NOT NULL
          AND json_extract(exif_data, '$.CameraModel') IS NOT NULL
          AND creator_type = 'illustrator'
    """)

    # 2. Musician: audio files
    op.execute("""
        UPDATE works
        SET creator_type = 'musician'
        WHERE file_type = 'audio'
          AND creator_type = 'illustrator'
    """)

    # 3. Video: video files
    op.execute("""
        UPDATE works
        SET creator_type = 'video'
        WHERE file_type = 'video'
          AND creator_type = 'illustrator'
    """)

    # 4. Craftsman: document files with CAD keywords in custom_metadata
    op.execute("""
        UPDATE works
        SET creator_type = 'craftsman'
        WHERE file_type = 'document'
          AND custom_metadata IS NOT NULL
          AND (
              json_extract(custom_metadata, '$.keywords') IS NOT NULL
              AND (
                  json_extract(custom_metadata, '$.keywords') LIKE '%CAD%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%cad%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%AutoCAD%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%3D Modeling%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%3D建模%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%SolidWorks%'
                  OR json_extract(custom_metadata, '$.keywords') LIKE '%SketchUp%'
              )
          )
          AND creator_type = 'illustrator'
    """)

    # 5. Writer: remaining document files
    op.execute("""
        UPDATE works
        SET creator_type = 'writer'
        WHERE file_type = 'document'
          AND creator_type = 'illustrator'
    """)

    # 6. Designer: design files (already illustrator, keep as-is — no-op)
    #    Code/other: already illustrator (default) — no-op


def downgrade() -> None:
    """Reset all auto-detected creator_types back to 'illustrator'.

    This is intentionally coarse: we cannot perfectly reconstruct the original
    creator_type, so we fall back to the default.
    """
    op.execute("""
        UPDATE works
        SET creator_type = 'illustrator'
        WHERE creator_type IN ('photographer', 'musician', 'video', 'writer', 'craftsman')
    """)
