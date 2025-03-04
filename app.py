from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import threading
import re
import tempfile
import base64
import zipfile
import io
import webbrowser
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor

# Stel de template- en statische mappen in
app = Flask(
    __name__,
    template_folder=os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'templates')),
    static_folder=os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'static'))
)

# Max content length
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40MB max-limit

ALLOWED_EXTENSIONS = {'pdf'}

# PDF voorbeeld
pdf_processor = PDFProcessor(max_workers=os.cpu_count() or 1)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_year(year):
    """Jaarwaarde controleren"""
    if not year:
        return False, "Voer een geldig jaar in"
    if not re.match(r'^\d{4}$', year):
        return False, "Het jaar moet uit 4 cijfers bestaan (bijvoorbeeld: 2024)"
    return True, ""


def validate_number(number):
    """Valideer de getalwaarde"""
    if not number:
        return False, "Voer een geldig nummer in"
    if not re.match(r'^\d{1,2}$', number):
        return False, "Het nummer moet uit 1 of 2 cijfers bestaan (bijvoorbeeld: 1 of 01)"
    return True, ""


def process_ranges(ranges_str, max_pages):
    """Paginabereiken verwerken"""
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
    """Te verwijderen procespagina's"""
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
    """Samengevoegde indexen verwerken"""
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

        # Year and number validation
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
                # Temporary file creation
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    file.save(temp_file.name)
                    filepath = temp_file.name

                    # PDF reader and page count
                    reader = pdf_processor.get_pdf_reader(filepath)
                    total_pages = len(reader.pages)

                    try:
                        # Process form data
                        article_ranges = process_ranges(
                            request.form.get('article_ranges', ''), total_pages)
                        remove_pages = process_remove_pages(
                            request.form.get('remove_pages', ''), total_pages)
                        merge_indices = process_merge_indices(
                            request.form.get('merge_ranges', ''))
                    except ValueError as e:
                        return jsonify({'error': str(e)}), 400

                    # PDF Processing
                    output_files = pdf_processor.process_pdf(
                        input_pdf=filepath,
                        pages_to_remove=remove_pages,
                        article_ranges=article_ranges,
                        merge_article_indices=merge_indices,
                        year=year,
                        number=number
                    )

                    # ZIP files
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
                        },
                        'sound': 'notification.mp3'
                    })

            except Exception as e:
                return jsonify({'error': f'Verwerkingsfout: {str(e)}'}), 500

            finally:
                # Cleanup
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
        return jsonify({'error': f'Onverwachte fout: {str(e)}'}), 500


def open_browser():
    """Open de standaardbrowser naar de webapp."""
    webbrowser.open(f'http://127.0.0.1:{port}')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10010))
    if os.environ.get('RENDER') is None:
        threading.Timer(1, open_browser).start()

    app.run(host='0.0.0.0', port=port)
