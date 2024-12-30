from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

ALLOWED_EXTENSIONS = {'pdf'}

# PDF işlemci örneği oluştur
pdf_processor = PDFProcessor()


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
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            filepath = temp_file.name

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

            merge_ranges = None
            merge_article_indices = None

            merge_str = request.form.get('merge_pages', '').strip()
            if merge_str:
                try:
                    page1, page2 = map(int, merge_str.split(','))
                    if article_ranges:
                        merge_article_indices = [page1-1, page2-1]
                    else:
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

            # Downloads klasör yolunu al
            output_path = pdf_processor.get_downloads_folder()

            return jsonify({
                'success': True,
                'message': 'Bestand succesvol verwerkt',
                'outputPath': str(output_path)
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return jsonify({'error': 'Niet-toegestaan bestandstype'}), 400


if __name__ == '__main__':
    app.run(debug=True)
