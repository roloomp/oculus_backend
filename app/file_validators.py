import os
import magic
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from PyPDF2 import PdfReader
from PIL import Image
import hashlib


class FileValidator:
    """Валидатор для загружаемых файлов"""

    ALLOWED_EXTENSIONS = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
        'medical': ['.dcm', '.dicom'],  # Медицинские изображения
    }

    ALLOWED_MEDICAL_FILES = {
        'images': ['jpg', 'jpeg', 'png', 'dcm'],
        'documents': ['pdf', 'doc', 'docx'],
        'max_size_mb': 50
    }

    ALLOWED_MIME_TYPES = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/bmp': ['.bmp'],
        'image/tiff': ['.tiff'],
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'text/plain': ['.txt'],
        'application/rtf': ['.rtf'],
        'application/dicom': ['.dcm'],
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_DIMENSIONS = (5000, 5000)  # Максимальные размеры изображения

    def __init__(self, allowed_types=None, max_size=None):
        self.allowed_types = allowed_types or ['images', 'documents']
        self.max_size = max_size or self.MAX_FILE_SIZE

    def validate_file_extension(self, file):
        """Проверка расширения файла"""
        ext = os.path.splitext(file.name)[1].lower()

        allowed_exts = []
        for file_type in self.allowed_types:
            allowed_exts.extend(self.ALLOWED_EXTENSIONS.get(file_type, []))

        if ext not in allowed_exts:
            raise ValidationError(f'Недопустимое расширение файла. Разрешены: {", ".join(allowed_exts)}')

        return True

    def validate_mime_type(self, file):
        """Проверка MIME типа файла"""
        try:
            file.seek(0)
            mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)

            if mime not in self.ALLOWED_MIME_TYPES:
                raise ValidationError(f'Недопустимый тип файла: {mime}')

            # Проверка соответствия расширения MIME типу
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.ALLOWED_MIME_TYPES[mime]:
                raise ValidationError('Расширение файла не соответствует его содержимому')

            return mime
        except Exception as e:
            raise ValidationError(f'Ошибка проверки типа файла: {e}')

    def validate_file_size(self, file):
        """Проверка размера файла"""
        if file.size > self.max_size:
            raise ValidationError(f'Файл слишком большой. Максимальный размер: {self.max_size // (1024 * 1024)}MB')
        return True

    def validate_image(self, file):
        """Дополнительная валидация изображений"""
        try:
            width, height = get_image_dimensions(file)

            if width > self.MAX_IMAGE_DIMENSIONS[0] or height > self.MAX_IMAGE_DIMENSIONS[1]:
                raise ValidationError(
                    f'Изображение слишком большое. Максимальные размеры: {self.MAX_IMAGE_DIMENSIONS[0]}x{self.MAX_IMAGE_DIMENSIONS[1]}')

            # Проверка целостности изображения
            img = Image.open(file)
            img.verify()
            file.seek(0)

            return True
        except Exception as e:
            raise ValidationError(f'Файл поврежден или не является изображением: {e}')

    def validate_pdf(self, file):
        """Валидация PDF файлов"""
        try:
            pdf = PdfReader(file)
            if len(pdf.pages) == 0:
                raise ValidationError('PDF файл не содержит страниц')
            file.seek(0)
            return True
        except Exception as e:
            raise ValidationError(f'Некорректный PDF файл: {e}')

    def calculate_file_hash(self, file):
        """Вычисление хеша файла для проверки дубликатов"""
        sha256 = hashlib.sha256()
        for chunk in file.chunks():
            sha256.update(chunk)
        return sha256.hexdigest()

    def validate(self, file):
        """Полная валидация файла"""
        errors = []

        try:
            self.validate_file_extension(file)
        except ValidationError as e:
            errors.append(str(e))

        try:
            mime_type = self.validate_mime_type(file)
        except ValidationError as e:
            errors.append(str(e))
            mime_type = None

        try:
            self.validate_file_size(file)
        except ValidationError as e:
            errors.append(str(e))

        # Специфическая валидация по типу
        if mime_type and mime_type.startswith('image/'):
            try:
                self.validate_image(file)
            except ValidationError as e:
                errors.append(str(e))
        elif mime_type == 'application/pdf':
            try:
                self.validate_pdf(file)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            raise ValidationError(errors)

        return {
            'mime_type': mime_type,
            'hash': self.calculate_file_hash(file),
            'size': file.size
        }