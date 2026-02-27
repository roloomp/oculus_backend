"""
0006_surgerfeedback_reexamine

Переводим таблицу surgeon_feedback с модели «итог операции»
на модель «направление на доследование»:

  - Убираем поле status_after (success/complications/postponed/cancelled)
  - Добавляем поле action_type (только reexamine)
  - Существующие строки получают action_type='reexamine'
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_link_user_to_patient'),
    ]

    operations = [
        # 1. Добавляем новое поле с дефолтом, чтобы существующие строки не сломались
        migrations.AddField(
            model_name='surgeonfeedback',
            name='action_type',
            field=models.CharField(
                choices=[('reexamine', 'Направить на доследование')],
                default='reexamine',
                max_length=20,
                verbose_name='Тип действия',
            ),
        ),
        # 2. Удаляем старое поле
        migrations.RemoveField(
            model_name='surgeonfeedback',
            name='status_after',
        ),
        # 3. Обновляем ordering в Meta (только через AlterModelOptions)
        migrations.AlterModelOptions(
            name='surgeonfeedback',
            options={'ordering': ['-created_at']},
        ),
    ]
