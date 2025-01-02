import os
import logging
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import tempfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class PDFProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.logger = None

    @staticmethod
    def setup_tesseract():
        """Tesseract yapılandırması"""
        if os.getenv('VERCEL_ENV'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        else:
            pytesseract.pytesseract.tesseract_cmd = os.getenv(
                'TESSERACT_PATH', 'tesseract')

    def get_downloads_folder(self) -> Path:
        """Kullanıcının Downloads klasörünü tespit et"""
        home = Path.home()
        downloads = home / 'Downloads'
        downloads.mkdir(parents=True, exist_ok=True)
        return downloads

    def setup_logging(self, base_path: Path) -> logging.Logger:
        """Logging ayarlarını yapar"""
        log_file = base_path / 'log' / \
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(filename=log_file, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger()
        return logger

    def create_output_folders(self, year: str, number: str) -> Path:
        """Çıktı klasörlerini oluştur ve çıktı klasör adını yıl ve sayi bilgisine göre belirle"""
        downloads = self.get_downloads_folder()
        base_path = downloads / f"output{year}{number}"
        folders = ['pdf', 'ocr', 'small', 'large', 'log']
        for folder in folders:
            folder_path = base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        return base_path

    @staticmethod
    def generate_filename(year: str, number: str, start_page: int, end_page: int) -> str:
        """Standart dosya adı oluştur - istenen formatta"""
        return f"{year}{number.zfill(2)}{str(start_page).zfill(2)}{str(end_page).zfill(2)}"

    def compress_pdf(self, input_pdf: str, output_pdf: str):
        """PDF dosyasını sıkıştır"""
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_pdf, 'wb') as pdf_file:
            writer.write(pdf_file)

    def process_pdf(self, input_pdf: str, pages_to_remove: List[int] = None,
                    article_ranges: List[List[int]] = None,
                    merge_ranges: List[Tuple[int, int]] = None,
                    merge_article_indices: List[int] = None,
                    year: str = None,
                    number: str = None) -> Dict[str, List[str]]:
        """PDF işleme ana metodu"""
        logger = None
        try:
            pdf_name = os.path.splitext(os.path.basename(input_pdf))[
                0].replace('VHK_', '')
            base_path = self.create_output_folders(year, number)
            logger = self.setup_logging(base_path)
            logger.info(f"PDF işleme başladı: {pdf_name}")

            compressed_pdf_path = tempfile.NamedTemporaryFile(
                suffix='.pdf', delete=False).name
            self.compress_pdf(input_pdf, compressed_pdf_path)

            reader = PdfReader(compressed_pdf_path)

            if merge_article_indices and article_ranges:
                article_ranges = self._merge_articles(
                    article_ranges, merge_article_indices, logger)

            if merge_ranges:
                logger.info(
                    f"Sayfa birleştirme aralıkları işleniyor: {merge_ranges}")
                return self._process_with_merges(reader, year, number, merge_ranges, base_path, logger)

            if article_ranges:
                logger.info(f"Makale aralıkları işleniyor: {article_ranges}")
                return self._process_articles(reader, year, number, article_ranges, pages_to_remove or [], base_path, logger)

            logger.info("Tekli sayfalar işleniyor")
            return self._process_single_pages(reader, year, number, base_path, logger, pages_to_remove or [])

        except Exception as e:
            if logger:
                logger.error(f"PDF işleme hatası: {str(e)}")
            raise

    def _merge_articles(self, article_ranges: List[List[int]], merge_indices: List[int], logger: logging.Logger) -> List[List[int]]:
        """Makale aralıklarını birleştir"""
        try:
            if len(merge_indices) != 2:
                raise ValueError(
                    "Tam olarak 2 makale indeksi belirtilmelidir.")
            idx1, idx2 = merge_indices
            if not (0 <= idx1 < len(article_ranges) and 0 <= idx2 < len(article_ranges)):
                raise ValueError("Geçersiz makale indeksleri.")
            range1 = article_ranges[idx1]
            range2 = article_ranges[idx2]
            merged_range = list(
                range(min(range1[0], range2[0]), max(range1[-1], range2[-1]) + 1))
            new_ranges = [range_item for i, range_item in enumerate(
                article_ranges) if i not in merge_indices]
            new_ranges.append(merged_range)
            logger.info(
                f"Makaleler birleştirildi: {merge_indices} -> {merged_range}")
            return new_ranges
        except Exception as e:
            logger.error(f"Makale birleştirme hatası: {str(e)}")
            raise

    def _process_with_merges(self, reader: PdfReader, year: str, number: str,
                             merge_ranges: List[Tuple[int, int]], base_path: Path,
                             logger: logging.Logger) -> Dict[str, List[str]]:
        """Birleştirme aralıklarını işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        processed_pages = set()
        for start_page, end_page in merge_ranges:
            if not (1 <= start_page <= len(reader.pages) and 1 <= end_page <= len(reader.pages)):
                logger.warning(
                    f"Geçersiz sayfa aralığı: {start_page}-{end_page}")
                continue
            writer = PdfWriter()
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])
                processed_pages.add(page_num + 1)
            file_base_name = self.generate_filename(
                year, number, start_page, end_page)
            merge_outputs = self._save_outputs(
                writer, file_base_name, base_path, logger)
            for key in outputs:
                outputs[key].extend(merge_outputs[key])

        for page_num in range(len(reader.pages)):
            actual_page = page_num + 1
            if actual_page not in processed_pages:
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                file_base_name = self.generate_filename(
                    year, number, actual_page, actual_page)
                page_outputs = self._save_outputs(
                    writer, file_base_name, base_path, logger)
                for key in outputs:
                    outputs[key].extend(page_outputs[key])

        return outputs

    def _save_outputs(self, writer: PdfWriter, file_base_name: str,
                      base_path: Path, logger: logging.Logger) -> Dict[str, List[str]]:
        """PDF, görüntü ve OCR çıktılarını kaydet"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        temp_path = None
        try:
            pdf_path = base_path / 'pdf' / f"{file_base_name}.pdf"
            with open(pdf_path, 'wb') as pdf_file:
                writer.write(pdf_file)
            outputs['pdf'].append(str(pdf_path))

            temp_path = tempfile.NamedTemporaryFile(
                suffix='.pdf', delete=False).name
            writer.write(open(temp_path, 'wb'))
            images = convert_from_path(temp_path)
            if images:
                first_image = images[0]
                small_path = base_path / 'small' / f"{file_base_name}.jpg"
                small_image = first_image.copy()
                small_image.thumbnail((800, 800))
                small_image.save(str(small_path), 'JPEG')
                outputs['small'].append(str(small_path))
                large_path = base_path / 'large' / f"{file_base_name}.jpg"
                first_image.save(str(large_path), 'JPEG')
                outputs['large'].append(str(large_path))
                ocr_text = pytesseract.image_to_string(
                    first_image, lang='nld')  # Hollandaca
                ocr_path = base_path / 'ocr' / f"{file_base_name}.txt"
                with open(ocr_path, 'w', encoding='utf-8') as ocr_file:
                    ocr_file.write(ocr_text)
                outputs['ocr'].append(str(ocr_path))
        except Exception as e:
            logger.error(f"Dosya işleme hatası {file_base_name}: {str(e)}")
            raise
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(
                        f"Geçici dosya silinemedi: {temp_path}: {str(e)}")
        return outputs

    def _process_articles(self, reader: PdfReader, year: str, number: str,
                          article_ranges: List[List[int]], pages_to_remove: List[int],
                          base_path: Path, logger: logging.Logger) -> Dict[str, List[str]]:
        """Makale aralıklarını işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        for article_pages in article_ranges:
            start_page = min(article_pages)
            end_page = max(article_pages)
            file_base_name = self.generate_filename(
                year, number, start_page, end_page)
            writer = PdfWriter()
            for page_num in article_pages:
                if page_num not in pages_to_remove:
                    writer.add_page(reader.pages[page_num - 1])
            article_outputs = self._save_outputs(
                writer, file_base_name, base_path, logger)
            for key in outputs:
                outputs[key].extend(article_outputs[key])
        return outputs

    def _process_single_pages(self, reader: PdfReader, year: str, number: str,
                              base_path: Path, logger: logging.Logger,
                              pages_to_remove: List[int]) -> Dict[str, List[str]]:
        """Tek sayfaları işle"""
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        for page_num in range(len(reader.pages)):
            if page_num + 1 not in pages_to_remove:
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                file_base_name = self.generate_filename(
                    year, number, page_num + 1, page_num + 1)
                page_outputs = self._save_outputs(
                    writer, file_base_name, base_path, logger)
                for key in outputs:
                    outputs[key].extend(page_outputs[key])
        return outputs
