# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Could also use pyinstaller's Entrypoint()
a = Analysis(['launcher.py'],
             pathex=['C:\\Users\\Lunet\\Desktop\\pyr8s'],
             binaries=[],
             datas=[('pyr8s', 'pyr8s')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['matplotlib','tk','tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='launcher',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
