from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor

# Proje kök dizinini belirle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# Klasör yollarını yapılandır
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'input')
app.config['OUTPUT_FOLDER'] = os.path.join(BASE_DIR, 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

ALLOWED_EXTENSIONS = {'pdf'}

# PDF işlemci örneği oluştur
pdf_processor = PDFProcessor(
    upload_dir=app.config['UPLOAD_FOLDER'],
    output_dir=app.config['OUTPUT_FOLDER']
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Geen bestand geüpload'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Geen bestand geselecteerd'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        try:
            # Form verilerini işle
            remove_pages = [int(x.strip()) for x in request.form.get(
                'remove_pages', '').split(',') if x.strip()]

            # Makale aralıklarını işle
            article_ranges = []
            if request.form.get('article_ranges'):
                for range_str in request.form.get('article_ranges').split(','):
                    if '-' in range_str:
                        start, end = map(int, range_str.strip().split('-'))
                        article_ranges.append(list(range(start, end + 1)))

            # Hem sayfa birleştirme hem de makale birleştirme için değişkenler
            merge_ranges = None
            merge_article_indices = None

            # Birleştirilecek sayfaları işle
            merge_str = request.form.get('merge_pages', '').strip()
            if merge_str:
                try:
                    page1, page2 = map(int, merge_str.split(','))
                    if article_ranges:  # Eğer makale aralıkları varsa
                        # Makale indekslerini 0-tabanlı olarak ayarla
                        merge_article_indices = [page1-1, page2-1]
                    else:  # Direkt sayfa birleştirme
                        merge_ranges = [(min(page1, page2), max(page1, page2))]
                except ValueError:
                    return jsonify({'error': 'Ongeldige invoer voor samenvoegen'}), 400

            # PDF'i işle
            outputs = pdf_processor.process_pdf(
                input_pdf=filepath,
                pages_to_remove=remove_pages,
                article_ranges=article_ranges,
                merge_ranges=merge_ranges,
                merge_article_indices=merge_article_indices
            )

            output_base = os.path.dirname(
                outputs['pdf'][0]) if outputs['pdf'] else app.config['OUTPUT_FOLDER']

            return jsonify({
                'success': True,
                'message': 'Bestand succesvol verwerkt',
                'outputPath': os.path.abspath(output_base)
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({'error': 'Niet-toegestaan bestandstype'}), 400


@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        # Güvenli dosya yolu oluştur
        safe_path = os.path.join(
            app.config['OUTPUT_FOLDER'], secure_filename(filename))
        return send_file(safe_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


if __name__ == '__main__':
    # Gerekli klasörleri oluştur
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        os.makedirs(folder, exist_ok=True)

    app.run(debug=True)
