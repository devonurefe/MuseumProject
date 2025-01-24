from concurrent.futures import ThreadPoolExecutor
import os
import logging
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import tempfile
from typing import List, Dict
from pathlib import Path
from PIL import Image
import re


class PDFProcessor:
    def __init__(self, max_workers=None):
        self.setup_tesseract()
        self.logger = None
        self.max_workers = max_workers or (os.cpu_count() or 1)

    @staticmethod
    def setup_tesseract():
        """Tesseract konfiguratie"""
        import platform

        tesseract_path = os.getenv('TESSERACT_PATH')

        if not tesseract_path:
            if platform.system() == "Windows":
                tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            else:
                tesseract_path = "/usr/bin/tesseract"

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

        if not os.path.isfile(pytesseract.pytesseract.tesseract_cmd):
            raise FileNotFoundError(
                f"Tesseract niet gevonden: {tesseract_path}. Installeer Tesseract.")

    def create_output_folders(self) -> Path:
        """Maak tijdelijke uitvoermappen"""
        temp_dir = tempfile.mkdtemp()
        base_path = Path(temp_dir)

        for folder in ['pdf', 'ocr', 'small', 'large', 'log']:
            (base_path / folder).mkdir(parents=True, exist_ok=True)

        return base_path

    def setup_logging(self, base_path: Path) -> logging.Logger:
        """Logging configuratie"""
        log_file = base_path / 'log' / f"{datetime.now():%Y%m%d_%H%M%S}.log"
        logging.basicConfig(filename=log_file, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger()

        logger.info("PDF verwerking gestart.")
        logger.info(f"Tijdelijke map aangemaakt: {base_path}")

        return logger

    @staticmethod
    def generate_filename(year: str, number: str, range_str: str) -> str:
        """Genereer bestandsnaam"""
        start, end = range_str.split('-')
        return f"{year}{number.zfill(2)}{start.zfill(2)}{end.zfill(2)}"

    def get_pdf_reader(self, input_pdf: str) -> PdfReader:
        """Lees PDF-bestand"""
        return PdfReader(input_pdf)

    def process_pdf(self, input_pdf: str, pages_to_remove: List[int] = None,
                    article_ranges: List[List[int]] = None, merge_article_indices: List[int] = None,
                    year: str = None, number: str = None) -> Dict[str, List[str]]:
        try:
            base_path = self.create_output_folders()
            self.logger = self.setup_logging(base_path)
            self.logger.info(
                f"PDF verwerking gestart: {os.path.basename(input_pdf)}")

            reader = self.get_pdf_reader(input_pdf)
            total_pages = len(reader.pages)

            if total_pages == 0:
                raise ValueError(
                    "PDF-bestand is leeg of kan niet worden gelezen")

            outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}

            if not article_ranges:
                article_ranges = [[i + 1 for i in range(total_pages)]]

            if merge_article_indices:
                article_ranges = self._merge_articles(
                    article_ranges, merge_article_indices)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for page_range in article_ranges:
                    futures.append(executor.submit(
                        self._process_single_range,
                        reader,
                        page_range,
                        pages_to_remove,
                        base_path,
                        year,
                        number
                    ))

                for future in futures:
                    try:
                        result = future.result()
                        for key, value in result.items():
                            outputs[key].extend(value)
                    except Exception as e:
                        self.logger.error(f"Fout: {e}")

            self.logger.info("PDF verwerking voltooid.")
            return outputs

        except Exception as e:
            if self.logger:
                self.logger.error(f"PDF verwerkingsfout: {str(e)}")
            raise

    def _process_single_range(self, reader, page_range, pages_to_remove, base_path, year, number):
        writer = PdfWriter()
        for page_num in page_range:
            if not pages_to_remove or page_num not in pages_to_remove:
                writer.add_page(reader.pages[page_num - 1])

        range_str = f"{min(page_range)}-{max(page_range)}"
        file_base_name = self.generate_filename(year, number, range_str)

        return self._save_outputs(writer, file_base_name, base_path)

    def _save_outputs(self, writer: PdfWriter, file_base_name: str, base_path: Path) -> Dict[str, List[str]]:
        outputs = {'pdf': [], 'small': [], 'large': [], 'ocr': []}
        try:
            pdf_path = base_path / 'pdf' / f"{file_base_name}.pdf"
            with open(pdf_path, 'wb') as pdf_file:
                writer.write(pdf_file)
            outputs['pdf'].append(str(pdf_path))

            images = convert_from_path(pdf_path, first_page=1, last_page=1)
            if images:
                first_image = images[0]

                small_path = base_path / 'small' / f"{file_base_name}.jpg"
                large_path = base_path / 'large' / f"{file_base_name}.jpg"

                self._save_optimized_image(first_image, small_path, (500, 700))
                self._save_optimized_image(
                    first_image, large_path, (1024, 1280))

                outputs['small'].append(str(small_path))
                outputs['large'].append(str(large_path))

            # OCR işlemi (sadece metin içeren sayfalar için)
            ocr_text = self._perform_ocr_from_pdf(pdf_path)
            ocr_path = base_path / 'ocr' / f"{file_base_name}.txt"
            with open(ocr_path, 'w', encoding='utf-8') as ocr_file:
                ocr_file.write(ocr_text)
            outputs['ocr'].append(str(ocr_path))

        except Exception as e:
            self.logger.error(
                f"Fout bij het opslaan van bestanden {file_base_name}: {str(e)}")
            raise

        return outputs

    def _save_optimized_image(self, image, path, max_size):
        img = image.copy()
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(path, optimize=True, quality=85)

    def _perform_ocr_from_pdf(self, pdf_path: str) -> str:
        """Voer OCR uit op de tekst in de PDF (zonder afbeeldingen te converteren)"""
        reader = PdfReader(pdf_path)
        ocr_text = ""
        for page in reader.pages:
            ocr_text += page.extract_text() or ""
        return ocr_text

    def _merge_articles(self, article_ranges: List[List[int]], merge_indices: List[int]) -> List[List[int]]:
        if not merge_indices or len(merge_indices) < 2:
            return article_ranges

        valid_indices = sorted(
            [i for i in merge_indices if 1 <= i <= len(article_ranges)])
        if len(valid_indices) < 2:
            return article_ranges

        all_pages = []
        merged_indices = set()
        for i in valid_indices:
            all_pages.extend(article_ranges[i-1])
            merged_indices.add(i-1)

        merged_range = sorted(all_pages)

        result = []
        for i in range(len(article_ranges)):
            if i == valid_indices[0] - 1:
                result.append(merged_range)
            elif i not in merged_indices:
                result.append(article_ranges[i])

        return result
