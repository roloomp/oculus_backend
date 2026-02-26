from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Patient, IOLCalculation, SurgeonFeedback, AuditLog

User = get_user_model()


def log_model_change(instance, created=False, deleted=False):
    model_name = instance._meta.model_name
    user = getattr(instance, 'created_by', None) or getattr(instance, 'calculated_by', None) or getattr(instance,
                                                                                                        'surgeon', None)

    if created:
        action = f"Создана запись {model_name}: {instance}"
    elif deleted:
        action = f"Удалена запись {model_name}: {instance}"
    else:
        action = f"Изменена запись {model_name}: {instance}"

    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=model_name,
        entity_id=instance.id
    )


@receiver(post_save, sender=Patient)
def patient_saved(sender, instance, created, **kwargs):
    log_model_change(instance, created=created)


@receiver(post_save, sender=IOLCalculation)
def iol_saved(sender, instance, created, **kwargs):
    log_model_change(instance, created=created)


@receiver(post_save, sender=SurgeonFeedback)
def feedback_saved(sender, instance, created, **kwargs):
    log_model_change(instance, created=created)


@receiver(post_delete, sender=Patient)
def patient_deleted(sender, instance, **kwargs):
    log_model_change(instance, deleted=True)


@receiver(post_delete, sender=IOLCalculation)
def iol_deleted(sender, instance, **kwargs):
    log_model_change(instance, deleted=True)