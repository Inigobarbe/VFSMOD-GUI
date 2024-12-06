# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['pandas', 'numpy', 'PyQt5.uic', 'PyQt5.QtWidgets', 'multiprocessing', 'multiprocessing.Pool']
hiddenimports += collect_submodules('')


a = Analysis(
    ['C:\\qvfsmod\\Qvfsmod.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\qvfsmod\\ui', 'ui/'), ('C:\\qvfsmod\\resources.py', '.'), ('C:\\qvfsmod\\libraries', 'libraries/'), ('C:\\qvfsmod\\images', 'images/'), ('C:\\qvfsmod\\executables', 'executables/')],
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='Qvfsmod',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Qvfsmod',
)
