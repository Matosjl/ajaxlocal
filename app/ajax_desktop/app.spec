# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — empacota o Ajax Desktop num .exe portátil.
# Build: pyinstaller ajax_desktop/app.spec

import os

a = Analysis(
    ['desktop_app.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../agent_core', 'agent_core'),
        ('../backend/.env', 'backend'),
    ],
    hiddenimports=[
        'agent_core', 'agent_core.agent', 'agent_core.llm',
        'agent_core.tools', 'agent_core.planner', 'agent_core.guardrails',
        'agent_core.memory', 'agent_core.rag', 'agent_core.observability',
        'customtkinter', 'openai', 'httpx', 'sqlalchemy', 'psycopg2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='ajax',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
