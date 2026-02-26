from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_mediafile_file_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='linked_patient',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='user_account',
                to='app.patient',
            ),
        ),
    ]
