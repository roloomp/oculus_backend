from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Patient, PreparationTemplate, PatientPreparation,
    MediaFile, IOLCalculation, SurgeonFeedback, Notification, AuditLog
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'last_name', 'first_name', 'role')
    list_filter = ('role',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'middle_name')}),
        ('Медицинская информация', {'fields': ('role', 'medical_license_number', 'telegram_id')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_date', 'status')
    list_filter = ('status', 'gender')
    search_fields = ('last_name', 'first_name', 'passport_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('last_name', 'first_name', 'middle_name', 'birth_date', 'gender')
        }),
        ('Документы', {
            'fields': ('passport_series', 'passport_number', 'passport_issued_by',
                      'passport_issue_date', 'snils', 'insurance_policy')
        }),
        ('Медицинская информация', {
            'fields': ('diagnosis_icd10', 'diagnosis_text', 'surgery_type',
                      'status', 'surgery_date')
        }),
        ('FHIR данные', {
            'fields': ('fhir_data',),
            'classes': ('wide',),
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(PreparationTemplate)
class PreparationTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'surgery_type', 'required', 'requires_file')
    list_filter = ('surgery_type', 'required')

@admin.register(PatientPreparation)
class PatientPreparationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'template', 'completed', 'completion_date')
    list_filter = ('completed',)

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('patient', 'file', 'created_at')
    list_filter = ('created_at',)

@admin.register(IOLCalculation)
class IOLCalculationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'eye', 'result_diopters', 'formula_used', 'created_at')
    list_filter = ('eye', 'formula_used')

@admin.register(SurgeonFeedback)
class SurgeonFeedbackAdmin(admin.ModelAdmin):
    list_display = ('patient', 'surgeon', 'action_type', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('patient__last_name', 'patient__first_name', 'comment')
    readonly_fields = ('created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'sent', 'created_at')
    list_filter = ('sent',)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'entity_type')
    list_filter = ('entity_type', 'created_at')
    readonly_fields = ('created_at',)