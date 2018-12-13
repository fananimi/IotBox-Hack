# -*- mode: python -*-

block_cipher = None


a = Analysis(['LinkBox.py'],
             pathex=['/home/fananimi/Desktop/linkbox-bin'],
             binaries=[('/usr/lib/i386-linux-gnu/qt4/plugins/systemtrayicon/libsni-qt.so', 'qt4_plugins/systemtrayicon')],
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
          console=False )
