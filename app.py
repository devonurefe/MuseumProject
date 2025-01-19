from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import tempfile
import base64
import zipfile
import io
import webbrowser
import threading
import re

# Absolute path kullanarak template_folder'ı belirtelim
template_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Max content length ayarı
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40MB max-limit

ALLOWED_EXTENSIONS = {'pdf'}

# PDF işlemci örneği oluştur
pdf_processor = PDFProcessor()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_year(year):
    """Yıl değerini doğrula"""
    if not year:
        return False, "Voer een geldig jaar in"
    if not re.match(r'^\d{4}$', year):
        return False, "Het jaar moet uit 4 cijfers bestaan (bijvoorbeeld: 2024)"
    return True, ""


def validate_number(number):
    """Sayı değerini doğrula"""
    if not number:
        return False, "Voer een geldig nummer in"
    if not re.match(r'^\d{1,2}$', number):
        return False, "Het nummer moet uit 1 of 2 cijfers bestaan (bijvoorbeeld: 1 of 01)"
    return True, ""


def process_ranges(ranges_str, max_pages):
    """Sayfa aralıklarını işle"""
    if not ranges_str:
        return [[i + 1 for i in range(max_pages)]]

    try:
        ranges = []
        parts = ranges_str.split(',')
        for part in parts:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end or start < 1 or end > max_pages:
                    raise ValueError
                ranges.append(list(range(start, end + 1)))
            else:
                page = int(part)
                if page < 1 or page > max_pages:
                    raise ValueError
                ranges.append([page])
        return ranges
    except ValueError:
        raise ValueError(
            "Ongeldige paginabereiken. Gebruik het formaat: 1-3,4,5-6")


def process_remove_pages(remove_str, max_pages):
    """Silinecek sayfaları işle"""
    if not remove_str:
        return []

    try:
        pages = [int(x.strip()) for x in remove_str.split(',') if x.strip()]
        if any(p < 1 or p > max_pages for p in pages):
            raise ValueError
        return pages
    except ValueError:
        raise ValueError(
            "Ongeldige pagina's om te verwijderen. Gebruik komma's om pagina's te scheiden")


def process_merge_indices(merge_str):
    """Birleştirme indekslerini işle"""
    if not merge_str:
        return None

    try:
        indices = [int(x.strip()) for x in merge_str.split(',') if x.strip()]
        if len(indices) < 2:
            raise ValueError
        return indices
    except ValueError:
        raise ValueError(
            "Ongeldige samenvoegingsindices. Gebruik komma's om artikelen te scheiden")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if 'pdf_file' not in request.files:
                return render_template('index.html', error='Er is geen bestand geselecteerd')

            file = request.files['pdf_file']
            if file.filename == '':
                return render_template('index.html', error='Er is geen bestand geselecteerd')

            if not file.filename.endswith('.pdf'):
                return render_template('index.html', error='Alleen PDF-bestanden zijn toegestaan')

            return upload_file()

        except Exception as e:
            return render_template('index.html', error=f'Verwerkingsfout: {str(e)}')

    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'Er is geen bestand geüpload'}), 400

        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({'error': 'Er is geen bestand geselecteerd'}), 400

        # Yıl ve numara doğrulama
        year = request.form.get('year', '')
        number = request.form.get('number', '')

        year_valid, year_error = validate_year(year)
        if not year_valid:
            return jsonify({'error': year_error}), 400

        number_valid, number_error = validate_number(number)
        if not number_valid:
            return jsonify({'error': number_error}), 400

        if file and allowed_file(file.filename):
            try:
                # Geçici dosya oluştur
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    file.save(temp_file.name)
                    filepath = temp_file.name

                    # PDF okuyucu oluştur ve sayfa sayısını al
                    reader = pdf_processor.get_pdf_reader(filepath)
                    total_pages = len(reader.pages)

                    try:
                        # Form verilerini işle
                        article_ranges = process_ranges(
                            request.form.get('article_ranges', ''), total_pages)
                        remove_pages = process_remove_pages(
                            request.form.get('remove_pages', ''), total_pages)
                        merge_indices = process_merge_indices(
                            request.form.get('merge_ranges', ''))
                    except ValueError as e:
                        return jsonify({'error': str(e)}), 400

                    # PDF'i işle
                    output_files = pdf_processor.process_pdf(
                        input_pdf=filepath,
                        pages_to_remove=remove_pages,
                        article_ranges=article_ranges,
                        merge_article_indices=merge_indices,
                        year=year,
                        number=number
                    )

                    # ZIP dosyası oluştur
                    memory_file = io.BytesIO()
                    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file_type, file_list in output_files.items():
                            for file_path in file_list:
                                arcname = f"output{year}{number}/{file_type}/{os.path.basename(file_path)}"
                                zf.write(file_path, arcname)

                    memory_file.seek(0)
                    zip_data = base64.b64encode(
                        memory_file.getvalue()).decode('utf-8')

                    return jsonify({
                        'success': True,
                        'message': 'Bestand is succesvol verwerkt',
                        'zip_file': {
                            'name': f'output{year}{number}.zip',
                            'data': zip_data
                        }
                    })

            except Exception as e:
                return jsonify({'error': 'Er is een fout opgetreden tijdens de verwerking. Controleer uw invoer en probeer het opnieuw.'}), 500

            finally:
                # Temizlik
                if 'filepath' in locals():
                    try:
                        os.remove(filepath)
                    except:
                        pass
                if 'output_files' in locals():
                    for file_list in output_files.values():
                        for file_path in file_list:
                            try:
                                os.remove(file_path)
                            except:
                                pass

        return jsonify({'error': 'Niet-toegestaan bestandstype'}), 400

    except Exception as e:
        return jsonify({'error': 'Er is een onverwachte fout opgetreden. Probeer het later opnieuw.'}), 500


@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        downloads_folder = os.path.join(
            os.path.expanduser('~'), 'Downloads', 'museumproject')
        directory = os.path.dirname(os.path.join(downloads_folder, filename))
        filename = os.path.basename(filename)

        return send_from_directory(
            directory,
            filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404


def open_browser():
    webbrowser.open("http://127.0.0.1:10000")


if __name__ == '__main__':
    # Tarayıcıyı otomatik aç
    threading.Timer(1, open_browser).start()

    # Flask uygulamasını çalıştır
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
