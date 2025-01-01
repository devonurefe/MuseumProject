from pdf_processor import PDFProcessor

# Dizinleri belirleyin
upload_dir = "uploads"  # PDF'lerin yükleneceği dizin
output_dir = "output"   # İşlenmiş dosyaların kaydedileceği dizin

# PDFProcessor sınıfını başlatın
processor = PDFProcessor(upload_dir, output_dir)

# Örnek kullanım:
pdf_path = "ornek.pdf"

# Reklamları kaldırmak için (örneğin 2. ve 4. sayfaları kaldırmak için)
pages_to_remove = [1, 3]  # 0-tabanlı indeksleme
no_ads_pdf = processor.remove_ads(pdf_path, pages_to_remove)

# PDF'yi makalelere bölmek için
article_ranges = [[0, 1], [2, 3]]  # Her makale için sayfa aralıkları
articles = processor.split_into_articles(pdf_path, article_ranges)

# Küçük resim oluşturmak için
thumbnail = processor.create_thumbnails(pdf_path)

# Metni çıkarmak için
text_file = processor.extract_text(pdf_path)

# Tüm işlemleri birden yapmak için
result = processor.process_pdf(
    pdf_path,
    pages_to_remove=[1, 3],
    article_ranges=[[0, 1], [2, 3]],
    merge_pages=[0, 1]  # İsteğe bağlı: makaleleri birleştirmek için
)
