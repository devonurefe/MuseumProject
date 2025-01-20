import os
import logging
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import tempfile
from typing import List, Dict, Tuple
from pathlib import Path


class PDFProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.logger = None

    @staticmethod
    def setup_tesseract():
        """Tesseract yapılandırması"""
        import platform

        # Ortam değişkeninden yolu al, yoksa varsayılanı kullan
        tesseract_path = os.getenv('TESSERACT_PATH')

        if not tesseract_path:
            if platform.system() == "Windows":
                tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            else:
                tesseract_path = "/usr/bin/tesseract"

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        if not os.path.isfile(pytesseract.pytesseract.tesseract_cmd):
            raise FileNotFoundError(
                f"Tesseract bulunamadı: {tesseract_path}. Lütfen yükleyin.")

    def create_output_folders(self) -> Path:
        """Geçici klasör oluştur"""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir)

        for folder in ['pdf', 'ocr', 'small', 'large', 'log']:
            (base_path / folder).mkdir(parents=True, exist_ok=True)

        return base_path

    def setup_logging(self, base_path: Path) -> logging.Logger:
        """Logging ayarlarını yapar ve Hollandaca log mesajları ekler"""
        log_file = base_path / 'log' / f"{datetime.now():%Y%m%d_%H%M%S}.log"
        logging.basicConfig(filename=log_file, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger()

        # Hollandaca log mesajları
        logger.info("PDF işleme başladı.")
        logger.info(f"Geçici klasör oluşturuldu: {base_path}")
        logger.info("PDF, OCR, small, large ve log klasörleri oluşturuldu.")

        return logger

    @staticmethod
    def generate_filename(year: str, number: str, range_str: str) -> str:
        """Standart dosya adı oluştur"""
        # range_str içindeki '-' işaretini kaldırıp birleştir
        start, end = range_str.split('-')
        return f"{year}{number.zfill(2)}{start.zfill(2)}{end.zfill(2)}"

    def get_pdf_reader(self, input_pdf: str) -> PdfReader:
        """PDF dosyasını oku ve PdfReader döndür"""
        return PdfReader(input_pdf)

    def process_pdf(self, input_pdf: str, pages_to_remove: List[int] = None,
                    article_ranges: List[List[int]] = None, merge_article_indices: List[int] = None,
                    year: str = None, number: str = None) -> Dict[str, List[str]]:
        try:
            base_path = self.create_output_folders()
            self.logger = self.setup_logging(base_path)
            self.logger.info(
                f"PDF işleme başladı: {os.path.basename(input_pdf)}")

            reader = self.get_pdf_reader(input_pdf)
            total_pages = len(reader.pages)

            if total_pages == 0:
                raise ValueError("PDF dosyası boş veya okunamıyor")

            outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}

            if not article_ranges:
                article_ranges = [[i + 1 for i in range(total_pages)]]
                self.logger.info("Tüm sayfalar işlenecek.")

            validated_ranges = []
            for page_range in article_ranges:
                if all(1 <= p <= total_pages for p in page_range):
                    validated_ranges.append(page_range)
                else:
                    self.logger.warning(
                        f"Geçersiz sayfa aralığı atlandı: {page_range}")
            article_ranges = validated_ranges

            if merge_article_indices:
                article_ranges = self._merge_articles(
                    article_ranges, merge_article_indices)
                self.logger.info("Makaleler birleştirildi.")

            for i, page_range in enumerate(article_ranges, 1):
                writer = PdfWriter()

                for page_num in page_range:
                    if not pages_to_remove or page_num not in pages_to_remove:
                        writer.add_page(reader.pages[page_num - 1])

                range_str = f"{min(page_range)}-{max(page_range)}"
                file_base_name = self.generate_filename(
                    year, number, range_str)

                article_outputs = self._save_outputs(
                    writer, file_base_name, base_path)
                for key in outputs:
                    outputs[key].extend(article_outputs[key])

                self.logger.info(
                    f"Makale {i} işlendi: {file_base_name}")

            self.logger.info("PDF işleme tamamlandı.")
            return outputs

        except Exception as e:
            self.logger.error(f"PDF işleme hatası: {str(e)}")
            raise

    def _merge_articles(self, article_ranges: List[List[int]], merge_indices: List[int]) -> List[List[int]]:
        if not merge_indices or len(merge_indices) < 2:
            return article_ranges

        # Geçerli indeksleri kontrol et (1-tabanlı indeksler)
        valid_indices = sorted(
            [i for i in merge_indices if 1 <= i <= len(article_ranges)])
        if len(valid_indices) < 2:
            return article_ranges

        # Birleştirilecek makaleleri al
        all_pages = []
        merged_indices = set()  # Birleştirilen indeksleri takip et
        for i in valid_indices:
            all_pages.extend(article_ranges[i-1])
            merged_indices.add(i-1)

        # Yeni birleştirilmiş aralık
        merged_range = sorted(all_pages)

        # Sonuç listesini oluştur
        result = []
        for i in range(len(article_ranges)):
            if i == valid_indices[0] - 1:  # İlk birleştirme indeksine geldiğimizde
                result.append(merged_range)
            elif i not in merged_indices:  # Birleştirilmeyen makaleleri ekle
                result.append(article_ranges[i])

        return result

    def _save_outputs(self, writer: PdfWriter, file_base_name: str, base_path: Path) -> Dict[str, List[str]]:
        """PDF, görüntü ve OCR çıktılarını kaydet"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        try:
            pdf_path = base_path / 'pdf' / f"{file_base_name}.pdf"
            with open(pdf_path, 'wb') as pdf_file:
                writer.write(pdf_file)
            outputs['pdf'].append(str(pdf_path))

            images = convert_from_path(pdf_path)
            if images:
                first_image = images[0]

                # Small image (500x700)
                small_path = base_path / 'small' / f"{file_base_name}.jpg"
                small_image = first_image.copy()
                small_image.thumbnail((500, 700))
                small_image.save(str(small_path), 'JPEG')
                outputs['small'].append(str(small_path))

                # Large image (1024x1280)
                large_path = base_path / 'large' / f"{file_base_name}.jpg"
                large_image = first_image.copy()
                large_image.thumbnail((1024, 1280))
                large_image.save(str(large_path), 'JPEG')
                outputs['large'].append(str(large_path))

                # OCR işlemi (tüm sayfalar için)
                ocr_text = ""
                for image in images:
                    try:
                        ocr_text += pytesseract.image_to_string(
                            image, lang='nld') + "\n"
                    except pytesseract.TesseractError:
                        self.logger.warning(
                            "Hollandaca dil paketi bulunamadı. İngilizce kullanılıyor.")
                        ocr_text += pytesseract.image_to_string(
                            image, lang='eng') + "\n"

                # OCR metnini cümlelere ayır
                ocr_text = self._format_ocr_text(ocr_text)

                ocr_path = base_path / 'ocr' / f"{file_base_name}.txt"
                with open(ocr_path, 'w', encoding='utf-8') as ocr_file:
                    ocr_file.write(ocr_text)
                outputs['ocr'].append(str(ocr_path))
        except Exception as e:
            self.logger.error(
                f"Dosya işleme hatası {file_base_name}: {str(e)}")
            raise
        return outputs

    def _format_ocr_text(self, text: str) -> str:
        """OCR metnini cümlelere ayır ve formatla"""
        import re
        # Cümleleri ayır (nokta, ünlem, soru işareti ile bitenler)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        formatted_text = []
        for sentence in sentences:
            # "n.v.t." gibi kısaltmaları kontrol et
            if re.match(r'^[A-Za-z]+\.$', sentence):  # Kısaltmaları kontrol et
                formatted_text.append(sentence)
            else:
                formatted_text.append(sentence + '\n')  # Yeni satıra geç
        return ' '.join(formatted_text)
