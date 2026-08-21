# PyInstaller Specification File for Heti Agent (Lite Tier Distribution)
# Bundles Heti Agent framework, Lite Tier GGUF model, and runtime dependencies

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['d:\\Antigravity'],
    binaries=[],
    datas=[
        ('config/config.yaml', 'config'),
        ('config/permissions.yaml', 'config'),
    ],
    hiddenimports=[
        'psutil',
        'yaml',
        'hashlib',
        'piper',
        'faster_whisper'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HetiAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None
)
