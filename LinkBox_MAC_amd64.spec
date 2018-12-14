# -*- mode: python -*-
import os
cwd = os.getcwd()

block_cipher = None


a = Analysis(['LinkBox.py'],
             pathex=[cwd],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
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
          name='LinkBox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='icon.icns')
app = BUNDLE(exe,
             name='LinkBox.app',
             icon='icon.icns',
             bundle_identifier='LinkBox')
