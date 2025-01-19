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
    return "/usr/local/bin"  # Mac için varsayılan


def get_poppler_path():
    """Sistemdeki Poppler yolunu belirle"""
    if sys.platform == "win32":
        return r"C:\Program Files\poppler-23.11.0\Library\bin"
    return "/usr/local/bin"  # Mac için varsayılan


def create_build_folders():
    """Build klasörlerini oluştur"""
    Path("build").mkdir(exist_ok=True)
    Path("dist").mkdir(exist_ok=True)


def copy_dependencies():
    """Bağımlılıkları kopyala"""
    # Tesseract ve dil dosyalarını kopyala
    tesseract_path = get_tesseract_path()
    if sys.platform == "win32":
        shutil.copytree(tesseract_path, "build/tesseract",
                        dirs_exist_ok=True)

    # Poppler dosyalarını kopyala
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
    ('build/poppler', 'poppler')
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
    entitlements_file=None
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

    with open("museumapp.spec", "w") as f:
        f.write(spec_content)

    # PyInstaller'ı çalıştır
    subprocess.run(["pyinstaller", "--noconfirm", "museumapp.spec"])


def create_launcher():
    """Başlatıcı script oluştur"""
    launcher_content = """import os
import sys

def setup_environment():
    # Uygulama dizinini belirle
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    
    # Tesseract yolunu ayarla
    tesseract_path = os.path.join(base_path, 'tesseract')
    os.environ['PATH'] = tesseract_path + os.pathsep + os.environ.get('PATH', '')
    os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_path, 'tessdata')
    
    # Poppler yolunu ayarla
    poppler_path = os.path.join(base_path, 'poppler')
    os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')

if __name__ == '__main__':
    setup_environment()
    from app import app
    app.run(debug=False)
"""

    with open("launcher.py", "w") as f:
        f.write(launcher_content)


def main():
    """Ana build işlemi"""
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

        # Dist klasörünü zip'le
        shutil.make_archive("MuseumPDFTool", "zip", "dist/MuseumPDFTool")
        print("Zip dosyası oluşturuldu: MuseumPDFTool.zip")

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
