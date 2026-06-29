# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
ROOT = Path(__file__).parent / "backend"

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "alembic"), "alembic"),
        (str(ROOT / "alembic.ini"), "."),
    ],
    hiddenimports=[
        "sqlalchemy",
        "sqlalchemy.ext.declarative",
        "pydantic",
        "pydantic_settings",
        "fastapi",
        "uvicorn",
        "reportlab",
        "qrcode",
        "PIL",
        "cryptography",
        "cryptography.fernet",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="OriStudio" + (".exe" if sys.platform == "win32" else ""),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(Path(__file__).parent / "frontend" / "public" / "favicon.svg") if (Path(__file__).parent / "frontend" / "public" / "favicon.svg").exists() else None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="OriStudio.app",
        icon=None,
        bundle_identifier="com.oristudio.app",
        info_plist={
            "CFBundleName": "OriStudio",
            "CFBundleDisplayName": "OriStudio",
            "CFBundleVersion": "0.1.0",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
