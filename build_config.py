# build_config.py
import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_tesseract_path():
    """Sistemdeki Tesseract yolunu belirle"""
    if sys.platform == "win32":
        return r"C:\Program Files\Tesseract-OCR"
    return "/usr/local/bin"  # Mac voor


def get_poppler_path():
    """Sistemdeki Poppler yolunu belirle"""
    if sys.platform == "win32":
        return r"C:\Program Files\poppler-23.11.0\Library\bin"
    return "/usr/local/bin"  # Mac voor


def create_build_folders():
    """Build klasörlerini oluştur"""
    Path("build").mkdir(exist_ok=True)
    Path("dist").mkdir(exist_ok=True)


def copy_dependencies():
    """Bağımlılıkları kopyala"""
    # Tesseract and lang bestanden copy
    tesseract_path = get_tesseract_path()
    if sys.platform == "win32":
        shutil.copytree(tesseract_path, "build/tesseract",
                        dirs_exist_ok=True)

    # Poppler copy
    poppler_path = get_poppler_path()
    if sys.platform == "win32":
        shutil.copytree(poppler_path, "build/poppler",
                        dirs_exist_ok=True)


def create_executable():
    """PyInstaller ile executable oluştur"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('build/tesseract', 'tesseract'),
    ('build/poppler', 'poppler'),
    ('app.ico', '.')  # app.ico
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PyPDF2',
        'pdf2image',
        'pytesseract',
        'werkzeug.middleware.proxy_fix'
    ],
    hookspath=[],
    hooksconfig={},
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
    [],
    exclude_binaries=True,
    name='MuseumPDFTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico'  # Ikon dosyas
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MuseumPDFTool'
)
"""

    with open("museumapp.spec", "w", encoding='utf-8') as f:
        f.write(spec_content)

    # PyInstaller run
    subprocess.run(["pyinstaller", "--noconfirm", "museumapp.spec"])


def create_launcher():
    """Een script voor het starten maken"""
    launcher_content = """import os
import sys

def setup_environment():
    # De toepassingsmap bepalen
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    
    # Pas het pad van de vlakvulling aan
    tesseract_path = os.path.join(base_path, 'tesseract')
    os.environ['PATH'] = tesseract_path + os.pathsep + os.environ.get('PATH', '')
    os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_path, 'tessdata')
    
    # 
    poppler_path = os.path.join(base_path, 'poppler')
    os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')

if __name__ == '__main__':
    setup_environment()
    from app import app
    app.run(debug=False)
"""

    with open("launcher.py", "w", encoding='utf-8') as f:
        f.write(launcher_content)


def main():
    """Hoofdbouwproces"""
    try:
        print("Build işlemi başlıyor...")
        create_build_folders()
        print("Bağımlılıklar kopyalanıyor...")
        copy_dependencies()
        print("Executable oluşturuluyor...")
        create_executable()
        print("Launcher oluşturuluyor...")
        create_launcher()
        print("Build işlemi tamamlandı!")

        # Dist map zip
        shutil.make_archive("MuseumPDFTool", "zip", "dist/MuseumPDFTool")
        print("Zip-bestand gemaakt: MuseumPDFTool.zip")

    except Exception as e:
        print(f"Hata: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
