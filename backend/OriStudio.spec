# -*- mode: python ; coding: utf-8 -*-
"""OriStudio PyInstaller spec — P3.6.1.

Builds a standalone macOS .app bundle and Windows .exe.

Usage:
  macOS:   pyinstaller OriStudio.spec
  Windows: pyinstaller OriStudio.spec
  Clean:   pyinstaller --clean OriStudio.spec

Requires:
  pip install pyinstaller
"""

import os
import sys
from pathlib import Path

_IS_MACOS = sys.platform == "darwin"
_IS_WINDOWS = sys.platform == "win32"

_block_cipher = None

# ── Project root ───────────────────────────────────────────────
_root = Path(SPECPATH) if "SPECPATH" in dir() else Path(__file__).parent

# ── Datas: non-code assets to bundle ───────────────────────────
added_files = []
if (_root / ".env").exists():
    added_files.append((str(_root / ".env"), "."))
if (_root / "alembic.ini").exists():
    added_files.append((str(_root / "alembic.ini"), "."))
if (_root / "alembic").is_dir():
    added_files.append((str(_root / "alembic"), "alembic"))
if (_root / "app" / "templates").is_dir():
    added_files.append((str(_root / "app" / "templates"), "app/templates"))

# ── Hidden imports (dynamic / lazy modules) ────────────────────
hidden_imports = [
    "sqlalchemy.sql.default_comparator",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "cryptography",
    "cryptography.hazmat.backends.openssl",
    "PIL",
    "PIL.Image",
    "qrcode",
    "qrcode.image.pil",
    "psutil",
    "requests",
    "urllib3",
    "multiprocessing",
    "email.mime.text",
    "email.mime.multipart",
    "json",
    "csv",
    "hashlib",
    "secrets",
    "pathlib",
    "asyncio",
    "uuid",
    "logging",
    "smtplib",
    "email",
]

# ── Excluded modules (shrink bundle) ───────────────────────────
excludes = [
    "tkinter",
    "test",
    "unittest",
    "pytest",
    "setuptools",
    "pip",
    "wheel",
    "distutils",
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "tensorflow",
    "torch",
    "jedi",
    "IPython",
]

# ── App metadata ───────────────────────────────────────────────
APP_NAME = "OriStudio"
APP_ICON = None

for icon_candidate in [
    _root / "assets" / "icon.icns",
    _root / "assets" / "icon.ico",
    _root / "assets" / "icon.png",
    _root / "favicon.ico",
]:
    if icon_candidate.exists():
        APP_ICON = str(icon_candidate)
        break

# ── Analysis ───────────────────────────────────────────────────
a = Analysis(
    [str(_root / "app" / "main.py")],
    pathex=[str(_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

# ── macOS .app bundle ──────────────────────────────────────────
if _IS_MACOS:
    app = BUNDLE(
        a,
        name=APP_NAME,
        icon=APP_ICON,
        bundle_identifier="com.oristudio.app",
        version="0.1.0",
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": "OriStudio",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0.0",
            "CFBundleIdentifier": "com.oristudio.app",
            "NSHumanReadableCopyright": "Copyright 2025 OriStudio. All rights reserved.",
        },
    )
else:
    app = None

# ── Single-file EXE (macOS CLI + Windows) ──────────────────────
exe = EXE(
    a,
    name=APP_NAME,
    icon=APP_ICON,
    console=True,
)

# ── Windows: COLLECT into directory bundle ─────────────────────
if _IS_WINDOWS:
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
else:
    coll = None
