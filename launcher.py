import os
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
