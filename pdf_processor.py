import os
from datetime import datetime
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
import logging
import tempfile
from typing import List, Dict, Optional, Tuple, Union


class PDFProcessor:
    def __init__(self, upload_dir: str, output_dir: str):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.setup_tesseract()

    @staticmethod
    def setup_tesseract():
        """Tesseract yapılandırması"""
        if os.getenv('VERCEL_ENV'):
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        else:
            pytesseract.pytesseract.tesseract_cmd = os.getenv(
                'TESSERACT_PATH', 'tesseract')

    def setup_logging(self, base_output_path: str) -> logging.Logger:
        """Logging yapılandırması"""
        log_dir = os.path.join(base_output_path, 'log')
        os.makedirs(log_dir, exist_ok=True)

        log_filename = f"log-{datetime.now().strftime('%y%m%d')}.txt"
        log_path = os.path.join(log_dir, log_filename)

        logging.basicConfig(
            filename=log_path,
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger()

    def create_output_folders(self, output_name: str) -> str:
        """Çıktı klasörlerini oluştur"""
        base_path = os.path.join(self.output_dir, f"output_{output_name}")
        folders = ['pdf', 'ocr', 'small', 'large', 'log']

        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)

        return base_path

    @staticmethod
    def generate_filename(year: str, number: str, start_page: int, end_page: int) -> str:
        """Standart dosya adı oluştur"""
        return f"{year}{str(number).zfill(2)}{str(start_page).zfill(2)}{str(end_page).zfill(2)}"

    def process_pdf(self, input_pdf: str, pages_to_remove: List[int] = None,
                    article_ranges: List[List[int]] = None,
                    merge_ranges: List[Tuple[int, int]] = None,
                    merge_article_indices: List[int] = None) -> Dict[str, List[str]]:
        """
        PDF işleme ana metodu
        article_ranges: Makale sayfa aralıkları [[1,3], [4,6], ...]
        merge_ranges: Direkt sayfa birleştirme [(1,3), (4,6), ...]
        merge_article_indices: Birleştirilecek makale indeksleri [0,2] gibi
        """
        try:
            pdf_name = os.path.splitext(os.path.basename(input_pdf))[
                0].replace('VHK_', '')
            year, number = pdf_name.split('-')
            base_path = self.create_output_folders(pdf_name)
            logger = self.setup_logging(base_path)

            logger.info(f"PDF işleme başladı: {pdf_name}")
            reader = PdfReader(input_pdf)

            # Makale birleştirme işlemini yap
            if merge_article_indices and article_ranges:
                article_ranges = self._merge_articles(
                    article_ranges, merge_article_indices, logger)

            # Sayfa birleştirme varsa işle
            if merge_ranges:
                logger.info(f"Sayfa birleştirme aralıkları işleniyor: {
                            merge_ranges}")
                return self._process_with_merges(reader, year, number, merge_ranges, base_path, logger)

            # Makale aralıkları varsa işle
            if article_ranges:
                logger.info(f"Makale aralıkları işleniyor: {article_ranges}")
                return self._process_articles(reader, year, number, article_ranges, pages_to_remove or [], base_path, logger)

            # Normal sayfa işleme
            logger.info("Tekli sayfalar işleniyor")
            return self._process_single_pages(reader, year, number, base_path, logger, pages_to_remove or [])

        except Exception as e:
            if logger:
                logger.error(f"PDF işleme hatası: {str(e)}")
            raise

    def _merge_articles(self, article_ranges: List[List[int]],
                        merge_indices: List[int],
                        logger: logging.Logger) -> List[List[int]]:
        """Makale aralıklarını birleştir"""
        try:
            if len(merge_indices) != 2:
                raise ValueError("Tam olarak 2 makale indeksi belirtilmelidir")

            idx1, idx2 = merge_indices
            if not (0 <= idx1 < len(article_ranges) and 0 <= idx2 < len(article_ranges)):
                raise ValueError("Geçersiz makale indeksleri")

            # Birleştirilecek aralıkları al
            range1 = article_ranges[idx1]
            range2 = article_ranges[idx2]

            # Yeni birleştirilmiş aralık
            merged_range = list(
                range(min(range1[0], range2[0]), max(range1[-1], range2[-1]) + 1))

            # Orijinal listeyi güncelle
            new_ranges = []
            for i, range_item in enumerate(article_ranges):
                if i not in merge_indices:
                    new_ranges.append(range_item)
                elif i == min(merge_indices):
                    new_ranges.append(merged_range)

            logger.info(f"Makaleler birleştirildi: {
                        merge_indices} -> {merged_range}")
            return new_ranges

        except Exception as e:
            logger.error(f"Makale birleştirme hatası: {str(e)}")
            raise

    def _process_with_merges(self, reader: PdfReader, year: str, number: str,
                             merge_ranges: List[Tuple[int, int]], base_path: str,
                             logger: logging.Logger) -> Dict[str, List[str]]:
        """Birleştirme aralıklarını işle"""
        outputs = {
            'pdf': [],
            'small': [],
            'large': [],
            'ocr': []
        }

        processed_pages = set()

        # Birleştirilecek aralıkları işle
        for start_page, end_page in merge_ranges:
            if not (1 <= start_page <= len(reader.pages) and 1 <= end_page <= len(reader.pages)):
                logger.warning(f"Geçersiz sayfa aralığı: {
                               start_page}-{end_page}")
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

        # Birleştirilmemiş sayfaları işle
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

    def _process_articles(self, reader: PdfReader, year: str, number: str,
                          article_ranges: List[List[int]], pages_to_remove: List[int],
                          base_path: str, logger: logging.Logger) -> Dict[str, List[str]]:
        """Makale aralıklarını işle"""
        outputs = {
            'pdf': [],
            'small': [],
            'large': [],
            'ocr': []
        }

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
                              base_path: str, logger: logging.Logger,
                              pages_to_remove: List[int]) -> Dict[str, List[str]]:
        """Tek sayfaları işle"""
        outputs = {
            'pdf': [],
            'small': [],
            'large': [],
            'ocr': []
        }

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

    def _save_outputs(self, writer: PdfWriter, file_base_name: str,
                      base_path: str, logger: logging.Logger) -> Dict[str, List[str]]:
        """PDF, görüntü ve OCR çıktılarını kaydet"""
        outputs = {
            'pdf': [],
            'small': [],
            'large': [],
            'ocr': []
        }

        temp_path = None
        try:
            # PDF kaydet
            pdf_path = os.path.join(base_path, 'pdf', f"{file_base_name}.pdf")
            with open(pdf_path, 'wb') as pdf_file:
                writer.write(pdf_file)
            outputs['pdf'].append(pdf_path)

            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                writer.write(temp_pdf)
                temp_path = temp_pdf.name

            # PDF'i görüntüye dönüştür
            images = convert_from_path(temp_path)
            if images:
                first_image = images[0]

                # Küçük resim kaydet
                small_path = os.path.join(
                    base_path, 'small', f"{file_base_name}.jpg")
                small_image = first_image.copy()
                small_image.thumbnail((800, 800))
                small_image.save(small_path, 'JPEG')
                outputs['small'].append(small_path)

                # Büyük resim kaydet
                large_path = os.path.join(
                    base_path, 'large', f"{file_base_name}.jpg")
                first_image.save(large_path, 'JPEG')
                outputs['large'].append(large_path)

                # OCR işle
                ocr_text = pytesseract.image_to_string(first_image, lang='nld')
                ocr_path = os.path.join(base_path, 'ocr', f"{
                                        file_base_name}.txt")
                with open(ocr_path, 'w', encoding='utf-8') as ocr_file:
                    ocr_file.write(ocr_text)
                outputs['ocr'].append(ocr_path)

        except Exception as e:
            logger.error(f"Dosya işleme hatası {file_base_name}: {str(e)}")
            raise

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Geçici dosya silinemedi {
                                   temp_path}: {str(e)}")

        return outputs


# Kullanım örneği:
if __name__ == "__main__":
    processor = PDFProcessor("uploads", "outputs")

    # Birleştirme örneği:
    try:
        result = processor.process_pdf(
            input_pdf="VHK_2008-4.pdf",
            pages_to_remove=[3, 6, 9, 22],
            article_ranges=[[1, 3], [3, 7], [8, 11], [12, 15],
                            [16, 19], [20, 24], [25, 30], [30, 36]],
            merge_ranges=[(3, 5)]  # Birleştirilecek sayfa aralıkları
        )
        print("İşlem başarılı:", result)
    except Exception as e:
        print("Hata:", str(e))
