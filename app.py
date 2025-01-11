from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import tempfile
import base64

# Absolute path kullanarak template_folder'ı belirtelim
template_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)

# Max content length ayarı
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40MB max-limit

ALLOWED_EXTENSIONS = {'pdf'}

# PDF işlemci örneği oluştur
pdf_processor = PDFProcessor()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_uploaded_file(file):
    """Yüklenen dosyayı işle ve sonucu döndür"""
    if file and allowed_file(file.filename):
        return render_template('index.html', success=True)
    return render_template('index.html', error='Niet-toegestaan bestandstype')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if 'pdf_file' not in request.files:
                return render_template('index.html', error='Geen bestand geselecteerd')

            file = request.files['pdf_file']
            if file.filename == '':
                return render_template('index.html', error='Geen bestand geselecteerd')

            if not file.filename.endswith('.pdf'):
                return render_template('index.html', error='Alleen PDF-bestanden zijn toegestaan')

            return upload_file()  # upload_file fonksiyonunu çağır

        except Exception as e:
            return render_template('index.html', error=f'Verwerkingsfout: {str(e)}')

    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'Geen bestand geüpload'}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'Geen bestand geselecteerd'}), 400

    if file and allowed_file(file.filename):
        try:
            # Form verilerini al
            article_ranges_str = request.form.get('article_ranges', '')
            remove_pages_str = request.form.get('remove_pages', '')
            article_ranges = []
            remove_pages = []

            # Silinecek sayfaları işle
            if remove_pages_str:
                remove_pages = [int(x.strip())
                                for x in remove_pages_str.split(',') if x.strip()]

            # Makale aralıklarını işle
            if article_ranges_str:
                ranges = article_ranges_str.split(',')
                for r in ranges:
                    if '-' in r:
                        start, end = map(int, r.split('-'))
                        article_ranges.append(list(range(start, end + 1)))
                    else:
                        article_ranges.append([int(r)])

            year = request.form.get('year')
            number = request.form.get('number', '')

            # Makale birleştirme indekslerini işle
            merge_ranges_str = request.form.get('merge_ranges', '').strip()
            merge_article_indices = None
            if merge_ranges_str:
                try:
                    merge_article_indices = [
                        int(x.strip()) for x in merge_ranges_str.split(',') if x.strip()]
                    if len(merge_article_indices) < 2:
                        raise ValueError("En az iki makale indeksi gerekli")
                except ValueError as e:
                    return jsonify({'error': 'Geçersiz birleştirme indeksleri'}), 400

            # PDF'i geçici dosyaya kaydet
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                file.save(temp_file.name)
                filepath = temp_file.name

            # PDF'i işle
            output_files = pdf_processor.process_pdf(
                input_pdf=filepath,
                pages_to_remove=remove_pages,
                article_ranges=article_ranges,
                merge_article_indices=merge_article_indices,
                year=year,
                number=number
            )

            # Geçici dosyaları base64'e çevir
            file_contents = {}
            for file_type, file_list in output_files.items():
                file_contents[file_type] = []
                for file_path in file_list:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        filename = os.path.basename(file_path)
                        file_contents[file_type].append({
                            'name': filename,
                            'data': base64.b64encode(content).decode('utf-8')
                        })

            return jsonify({
                'success': True,
                'message': 'Bestand succesvol verwerkt',
                'files': file_contents
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Geçici dosyaları temizle
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


# Dosya indirme route'u ekleyelim
@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        # Downloads klasöründen dosyayı al
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
