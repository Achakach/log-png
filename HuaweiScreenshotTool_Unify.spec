# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['HuaweiScreenshotTool_Unify/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Unified launcher is a pure subprocess spawner; each sibling EXE bundles its own
        # templates, configs, and data files. No datas needed here.
    ],
    hiddenimports=[
        'pythoncom',
        'pywintypes',
        'win32com.client',
        'HuaweiScreenshotTool_Unify',
        'HuaweiScreenshotTool_Unify.commands',
        'HuaweiScreenshotTool_Unify.commands.process',
        'HuaweiScreenshotTool_Unify.commands.word',
        'HuaweiScreenshotTool_Unify.commands.excel',
        'HuaweiScreenshotTool_Unify.commands.extract',
        'HuaweiScreenshotTool_Unify.commands.stats',
        'HuaweiScreenshotTool_Unify.commands.gui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='huawei-tool',
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
)
