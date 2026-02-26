from django.db import migrations


def link_users_to_patients(apps, schema_editor):
    User = apps.get_model('app', 'User')
    Patient = apps.get_model('app', 'Patient')

    linked = 0
    skipped_no_match = []
    skipped_ambiguous = []

    unlinked_patients = User.objects.filter(role='patient', linked_patient__isnull=True)

    for user in unlinked_patients:
        candidates = Patient.objects.filter(
            last_name=user.last_name,
            first_name=user.first_name,
        )

        if candidates.count() == 0:
            skipped_no_match.append(user.email)
        elif candidates.count() > 1:
            skipped_ambiguous.append(
                f"{user.email} → {candidates.count()} patients named "
                f"'{user.last_name} {user.first_name}'"
            )
        else:
            user.linked_patient = candidates.first()
            user.save()
            linked += 1
            print(f"[0005] ✓ {user.email} → {user.last_name} {user.first_name}")

    print(f"\n[0005] Done — linked: {linked}, no match: {len(skipped_no_match)}, ambiguous: {len(skipped_ambiguous)}")

    if skipped_no_match:
        print("[0005] No patient record found for:")
        for email in skipped_no_match:
            print(f"       - {email}")

    if skipped_ambiguous:
        print("[0005] Multiple patient records found (link manually):")
        for msg in skipped_ambiguous:
            print(f"       - {msg}")


def unlink_users_from_patients(apps, schema_editor):
    User = apps.get_model('app', 'User')
    count = User.objects.filter(role='patient').update(linked_patient=None)
    print(f"[0005] Reversed — unlinked {count} patient user(s).")


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_user_linked_patient'),
    ]

    operations = [
        migrations.RunPython(link_users_to_patients, reverse_code=unlink_users_from_patients),
    ]
