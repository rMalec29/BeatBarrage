# BeatBarrage.spec
# Run with: pyinstaller BeatBarrage.spec

block_cipher = None

a = Analysis(
    ['beat_barrage.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Fonts
        ('PressStart2P-Regular.ttf', '.'),
        # Images
        ('turntable_basic.png', '.'),
        ('turntable_silver.png', '.'),
        ('turntable_gold.png', '.'),
        ('turntable_neon.png', '.'),
        ('turntable_diamond.png', '.'),
    ],
    hiddenimports=[
        'soundcard',
        'numpy',
        'pygame',
        'cryptography',
        'cryptography.fernet',
        'win32gui',
        'win32con',
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
    name='BeatBarrage',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',    # Uncomment and add icon.ico to use a custom icon
)
