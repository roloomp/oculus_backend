import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')

        return self.create_user(email, password, **extra_fields)

    def create_doctor(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'district_doctor')
        return self.create_user(email, password, **extra_fields)

    def create_surgeon(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'surgeon')
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Убираем поле username
    email = models.EmailField(unique=True)

    middle_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=30, choices=[
        ('district_doctor', 'Участковый врач'),
        ('surgeon', 'Хирург'),
        ('patient', 'Пациент'),
        ('admin', 'Администратор'),
    ], default='patient')
    medical_license_number = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.BigIntegerField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        """Полное имя пользователя"""
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ], blank=True, null=True)

    passport_series = models.CharField(max_length=10, blank=True, null=True)
    passport_number = models.CharField(max_length=20, blank=True, null=True)
    passport_issued_by = models.TextField(blank=True, null=True)
    passport_issue_date = models.DateField(blank=True, null=True)
    snils = models.CharField(max_length=20, blank=True, null=True)
    insurance_policy = models.CharField(max_length=50, blank=True, null=True)

    diagnosis_icd10 = models.CharField(max_length=20, blank=True, null=True)
    diagnosis_text = models.TextField(blank=True, null=True)
    surgery_type = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('red', 'Красный'),
        ('yellow', 'Желтый'),
        ('green', 'Зеленый'),
        ('blue', 'Синий'),
    ], default='red')
    surgery_date = models.DateField(blank=True, null=True)

    fhir_data = models.JSONField(blank=True, null=True, verbose_name='FHIR данные')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patients'

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class PreparationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    surgery_type = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    requires_file = models.BooleanField(default=False)
    required = models.BooleanField(default=True)

    class Meta:
        db_table = 'preparation_templates'

    def __str__(self):
        return self.title


class PatientPreparation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    template = models.ForeignKey(PreparationTemplate, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completion_date = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'patient_preparation'

    def __str__(self):
        return f"{self.patient} - {self.template}"


class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='media_files')
    preparation = models.ForeignKey(PatientPreparation, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='files')

    file = models.FileField(upload_to='patient_files/%Y/%m/%d/')
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=100, blank=True)  # MIME type
    file_size = models.BigIntegerField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Проверен ли документ
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='verified_files')
    verified_at = models.DateTimeField(blank=True, null=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'media_files'
        ordering = ['-created_at']

    def __str__(self):
        return f"Файл для {self.patient} - {self.file_name or self.file.name}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_name:
            self.file_name = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class IOLCalculation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    eye = models.CharField(max_length=10, choices=[
        ('right', 'Правый'),
        ('left', 'Левый'),
    ])

    k1 = models.DecimalField(max_digits=5, decimal_places=2)
    k2 = models.DecimalField(max_digits=5, decimal_places=2)
    acd = models.DecimalField(max_digits=5, decimal_places=2)
    axial_length = models.DecimalField(max_digits=5, decimal_places=2)

    formula_used = models.CharField(max_length=50, choices=[
        ('srk_t', 'SRK/T'),
        ('holladay', 'Holladay'),
        ('hoffer_q', 'Hoffer Q'),
        ('haigis', 'Haigis'),
        ('barrett', 'Barrett'),
    ])
    result_diopters = models.DecimalField(max_digits=6, decimal_places=2)

    calculated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'iol_calculations'

    def __str__(self):
        return f"{self.patient} - {self.result_diopters} D"


class SurgeonFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    surgeon = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    status_after = models.CharField(max_length=20, choices=[
        ('success', 'Успешно'),
        ('complications', 'С осложнениями'),
        ('postponed', 'Отложено'),
        ('cancelled', 'Отменено'),
    ], blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'surgeon_feedback'

    def __str__(self):
        return f"{self.patient} - {self.created_at.date()}"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return self.message[:50]


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.TextField(blank=True, null=True)
    entity_type = models.CharField(max_length=50, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_logs'

    def __str__(self):
        return f"{self.created_at} - {self.action}"