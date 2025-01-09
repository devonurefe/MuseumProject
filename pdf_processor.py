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

    def create_output_folders(self, year: str, number: str) -> Path:
        """Kullanıcının Downloads klasöründe çıktı klasörlerini oluştur"""
        downloads_folder = Path.home() / 'Downloads' / 'museumproject'
        # Downloads klasörünü oluştur
        downloads_folder.mkdir(parents=True, exist_ok=True)
        base_path = downloads_folder / f'output{year}{number}'
        # Output klasörünü oluştur
        base_path.mkdir(parents=True, exist_ok=True)

        for folder in ['pdf', 'ocr', 'small', 'large', 'log']:
            (base_path / folder).mkdir(parents=True,
                                       exist_ok=True)  # Alt klasörleri oluştur

        return base_path

    def setup_logging(self, base_path: Path) -> logging.Logger:
        """Logging ayarlarını yapar"""
        log_file = base_path / 'log' / f"{datetime.now():%Y%m%d_%H%M%S}.log"
        logging.basicConfig(filename=log_file, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger()

    @staticmethod
    def generate_filename(year: str, number: str, start_page: int, end_page: int) -> str:
        """Standart dosya adı oluştur"""
        return f"{year}{number.zfill(2)}{str(start_page).zfill(2)}{str(end_page).zfill(2)}"

    def compress_pdf(self, input_pdf: str) -> str:
        """PDF dosyasını sıkıştır"""
        output_pdf = tempfile.NamedTemporaryFile(
            suffix='.pdf', delete=False).name
        writer = PdfWriter()
        for page in PdfReader(input_pdf).pages:
            writer.add_page(page)
        with open(output_pdf, 'wb') as pdf_file:
            writer.write(pdf_file)
        return output_pdf

    def process_pdf(self, input_pdf: str, pages_to_remove: List[int] = None,
                    article_ranges: List[List[int]] = None, merge_ranges: List[Tuple[int, int]] = None,
                    merge_article_indices: List[int] = None, year: str = None, number: str = None) -> Dict[str, List[str]]:
        """PDF işleme ana metodu"""
        try:
            base_path = self.create_output_folders(year, number)
            self.logger = self.setup_logging(base_path)
            self.logger.info(
                f"PDF işleme başladı: {os.path.basename(input_pdf)}")

            compressed_pdf_path = self.compress_pdf(input_pdf)
            reader = PdfReader(compressed_pdf_path)

            if merge_article_indices and article_ranges:
                article_ranges = self._merge_articles(
                    article_ranges, merge_article_indices)

            if merge_ranges:
                return self._process_with_merges(reader, year, number, merge_ranges, base_path)

            if article_ranges:
                return self._process_articles(reader, year, number, article_ranges, pages_to_remove or [], base_path)

            return self._process_single_pages(reader, year, number, pages_to_remove or [], base_path)

        except Exception as e:
            self.logger.error(f"PDF işleme hatası: {str(e)}")
            raise

    def _merge_articles(self, article_ranges: List[List[int]], merge_indices: List[int]) -> List[List[int]]:
        """Makale aralıklarını birleştir"""
        idx1, idx2 = merge_indices
        merged_range = list(range(min(article_ranges[idx1][0], article_ranges[idx2][0]),
                                  max(article_ranges[idx1][-1], article_ranges[idx2][-1]) + 1))
        return [range_item for i, range_item in enumerate(article_ranges) if i not in merge_indices] + [merged_range]

    def _process_with_merges(self, reader: PdfReader, year: str, number: str,
                             merge_ranges: List[Tuple[int, int]], base_path: Path) -> Dict[str, List[str]]:
        """Birleştirme aralıklarını işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        processed_pages = set()

        for start_page, end_page in merge_ranges:
            if 1 <= start_page <= len(reader.pages) and 1 <= end_page <= len(reader.pages):
                writer = PdfWriter()
                for page_num in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[page_num])
                    processed_pages.add(page_num + 1)

                file_base_name = self.generate_filename(
                    year, number, start_page, end_page)
                outputs.update(self._save_outputs(
                    writer, file_base_name, base_path))

        for page_num in range(len(reader.pages)):
            if (page_num + 1) not in processed_pages:
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                file_base_name = self.generate_filename(
                    year, number, page_num + 1, page_num + 1)
                outputs.update(self._save_outputs(
                    writer, file_base_name, base_path))

        return outputs

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
                small_path = base_path / 'small' / f"{file_base_name}.jpg"
                first_image.thumbnail((800, 800))
                first_image.save(str(small_path), 'JPEG')
                outputs['small'].append(str(small_path))

                large_path = base_path / 'large' / f"{file_base_name}.jpg"
                first_image.save(str(large_path), 'JPEG')
                outputs['large'].append(str(large_path))

                ocr_text = pytesseract.image_to_string(first_image, lang='nld')
                ocr_path = base_path / 'ocr' / f"{file_base_name}.txt"
                with open(ocr_path, 'w', encoding='utf-8') as ocr_file:
                    ocr_file.write(ocr_text)
                outputs['ocr'].append(str(ocr_path))
        except Exception as e:
            self.logger.error(
                f"Dosya işleme hatası {file_base_name}: {str(e)}")
            raise
        return outputs

    def _process_articles(self, reader: PdfReader, year: str, number: str,
                          article_ranges: List[List[int]], pages_to_remove: List[int],
                          base_path: Path) -> Dict[str, List[str]]:
        """Makale aralıklarını işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        for article_pages in article_ranges:
            writer = PdfWriter()
            for page_num in article_pages:
                if page_num not in pages_to_remove:
                    writer.add_page(reader.pages[page_num - 1])
            file_base_name = self.generate_filename(
                year, number, min(article_pages), max(article_pages))
            outputs.update(self._save_outputs(
                writer, file_base_name, base_path))
        return outputs

    def _process_single_pages(self, reader: PdfReader, year: str, number: str,
                              pages_to_remove: List[int], base_path: Path) -> Dict[str, List[str]]:
        """Tek sayfaları işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        for page_num in range(len(reader.pages)):
            if (page_num + 1) not in pages_to_remove:
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                file_base_name = self.generate_filename(
                    year, number, page_num + 1, page_num + 1)
                outputs.update(self._save_outputs(
                    writer, file_base_name, base_path))
        return outputs
