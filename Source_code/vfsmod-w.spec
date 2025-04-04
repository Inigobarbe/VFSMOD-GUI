# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\qvfsmod\\Source_code\\vfsmod-w.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\qvfsmod\\Source_code\\ui', 'ui/'), ('C:\\qvfsmod\\Source_code\\resources.py', '.'), ('C:\\qvfsmod\\Source_code\\libraries', 'libraries/'), ('C:\\qvfsmod\\Source_code\\images', 'images/'), ('C:\\qvfsmod\\Source_code\\executables', 'executables/'), ('C:\\qvfsmod\\Source_code\\icon.ico', '.'), ('C:\\qvfsmod\\Source_code\\license.txt', '.'), ('C:\\qvfsmod\\Source_code\\images\\about.png', '.')],
    hiddenimports=['pandas', 'numpy', 'PyQt5.uic', 'PyQt5.QtWidgets', 'multiprocessing', 'multiprocessing.Pool', 'pathlib', 'matplotlib.backends.backend_pdf', 'matplotlib.backends.backend_agg', 'matplotlib.backends.backend_tkagg', 'matplotlib.backends.backend_ps', 'matplotlib.backends.backend_svg', 'matplotlib.pyplot'],
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
    name='vfsmod-w',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\qvfsmod\\Source_code\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='vfsmod-w',
)
