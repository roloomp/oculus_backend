"""
seed_data.py — Django management command для заполнения БД тестовыми данными.

Размещение:
    app/management/commands/seed_data.py

Запуск:
    python manage.py seed_data
    python manage.py seed_data --clear   # сначала очистить БД
"""

import uuid
import random
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password

# ─── Справочные данные ────────────────────────────────────────────────────────

LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Козлов", "Новиков",
    "Морозов", "Волков", "Соловьёв", "Васильев", "Зайцев",
    "Павлов", "Семёнов", "Голубев", "Виноградов", "Богданов",
    "Воробьёв", "Фёдоров", "Михайлов", "Беляев", "Тарасов",
    "Белова", "Комарова", "Орлова", "Кузнецова", "Попова",
    "Лебедева", "Козлова", "Новикова", "Соколова", "Михайлова",
]

FIRST_NAMES_M = [
    "Александр", "Дмитрий", "Максим", "Сергей", "Андрей",
    "Алексей", "Артём", "Илья", "Кирилл", "Михаил",
    "Никита", "Роман", "Евгений", "Виктор", "Игорь",
]

FIRST_NAMES_F = [
    "Анна", "Мария", "Елена", "Ольга", "Наталья",
    "Татьяна", "Светлана", "Ирина", "Юлия", "Екатерина",
    "Алина", "Валерия", "Дарья", "Полина", "Кристина",
]

MIDDLE_NAMES_M = [
    "Александрович", "Дмитриевич", "Сергеевич", "Андреевич", "Алексеевич",
    "Михайлович", "Владимирович", "Игоревич", "Николаевич", "Петрович",
]

MIDDLE_NAMES_F = [
    "Александровна", "Дмитриевна", "Сергеевна", "Андреевна", "Алексеевна",
    "Михайловна", "Владимировна", "Игоревна", "Николаевна", "Петровна",
]

SURGERY_TYPES = [
    "Факоэмульсификация катаракты",
    "Имплантация ИОЛ",
    "Лазерная коррекция зрения",
    "Трабекулэктомия",
    "Витрэктомия",
    "Кератопластика",
    "Склеропластика",
    "Антиглаукоматозная операция",
]

DIAGNOSES_ICD10 = [
    ("H26.9", "Катаракта неуточнённая"),
    ("H25.0", "Старческая начальная катаракта"),
    ("H25.1", "Старческая ядерная катаракта"),
    ("H40.1", "Первичная открытоугольная глаукома"),
    ("H52.1", "Миопия"),
    ("H52.0", "Гиперметропия"),
    ("H33.0", "Отслойка сетчатки с разрывом"),
    ("H35.3", "Дегенерация жёлтого пятна"),
    ("H18.6", "Кератоконус"),
    ("H46",   "Неврит зрительного нерва"),
]

PREPARATION_TEMPLATES_DATA = [
    # Факоэмульсификация катаракты
    ("Факоэмульсификация катаракты", "Общий анализ крови", False, True),
    ("Факоэмульсификация катаракты", "Биохимический анализ крови", False, True),
    ("Факоэмульсификация катаракты", "Коагулограмма", False, True),
    ("Факоэмульсификация катаракты", "ЭКГ", True, True),
    ("Факоэмульсификация катаракты", "Флюорография", True, True),
    ("Факоэмульсификация катаракты", "Осмотр терапевта", True, True),
    ("Факоэмульсификация катаракты", "Биометрия глаза", True, True),
    ("Факоэмульсификация катаракты", "УЗИ глаза (B-scan)", True, False),
    # Лазерная коррекция зрения
    ("Лазерная коррекция зрения", "Общий анализ крови", False, True),
    ("Лазерная коррекция зрения", "Кератотопография", True, True),
    ("Лазерная коррекция зрения", "Авторефрактометрия", False, True),
    ("Лазерная коррекция зрения", "Пахиметрия роговицы", False, True),
    ("Лазерная коррекция зрения", "Осмотр офтальмолога", True, True),
    # Антиглаукоматозная операция
    ("Антиглаукоматозная операция", "Общий анализ крови", False, True),
    ("Антиглаукоматозная операция", "Биохимический анализ крови", False, True),
    ("Антиглаукоматозная операция", "Суточная тонометрия", False, True),
    ("Антиглаукоматозная операция", "Периметрия", True, True),
    ("Антиглаукоматозная операция", "ОКТ диска зрительного нерва", True, True),
    ("Антиглаукоматозная операция", "Гониоскопия", False, True),
    ("Антиглаукоматозная операция", "ЭКГ", True, True),
    # Витрэктомия
    ("Витрэктомия", "Общий анализ крови", False, True),
    ("Витрэктомия", "Биохимический анализ крови", False, True),
    ("Витрэктомия", "Коагулограмма", False, True),
    ("Витрэктомия", "УЗИ глаза (B-scan)", True, True),
    ("Витрэктомия", "ОКТ сетчатки", True, True),
    ("Витрэктомия", "ФАГ", True, False),
    ("Витрэктомия", "Осмотр кардиолога", True, True),
]

AUDIT_ACTIONS = [
    "Добавление пациента",
    "Редактирование карточки пациента",
    "Загрузка документа",
    "Расчёт ИОЛ",
    "Подтверждение готовности пациента",
    "Добавление отзыва хирурга",
    "Верификация документа",
    "Назначение даты операции",
    "Просмотр карточки пациента",
    "Изменение статуса пациента",
]

FEEDBACK_COMMENTS = [
    "Операция прошла успешно, пациент чувствует себя хорошо. Острота зрения восстановлена.",
    "Незначительные осложнения в виде отёка роговицы, назначена дополнительная терапия.",
    "Плановая операция перенесена в связи с ОРВИ у пациента.",
    "Отличный результат, пациент доволен. Рекомендованы контрольные осмотры.",
    "Операция выполнена без осложнений. Имплантирована ИОЛ +18.5 D.",
    "Выявлены противопоказания к наркозу, операция отменена до получения кардиологического заключения.",
    "Послеоперационный период протекает нормально. Назначены антибактериальные капли.",
    "Пациент отказался от операции после консультации с родственниками.",
    "Хирургическое вмешательство прошло в штатном режиме. Зрение 0.8 на следующий день.",
    "Рекомендована коррекция медикаментозной подготовки перед следующим визитом.",
]

NOTIFICATION_MESSAGES = [
    "Напоминание: завтра плановая операция пациента",
    "Пациент записан на предоперационный осмотр",
    "Готовы результаты биометрии",
    "Требуется верификация загруженных документов",
    "Пациент подтвердил явку на операцию",
    "Срок действия анализов истекает через 3 дня",
    "Новый пациент направлен на консультацию хирурга",
    "Операция перенесена на другую дату",
]


def rand_date_past(years_min=20, years_max=80) -> date:
    """Случайная дата рождения."""
    days = random.randint(years_min * 365, years_max * 365)
    return date.today() - timedelta(days=days)


def rand_datetime_past(days_min=1, days_max=180) -> datetime:
    delta = timedelta(
        days=random.randint(days_min, days_max),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    dt = timezone.now() - delta
    return dt


def rand_passport_series() -> str:
    return f"{random.randint(10, 99)} {random.randint(10, 99)}"


def rand_passport_number() -> str:
    return f"{random.randint(100000, 999999)}"


def rand_snils() -> str:
    n = random.randint(100_000_000, 999_999_999)
    return f"{str(n)[:3]}-{str(n)[3:6]}-{str(n)[6:9]} {random.randint(10,99)}"


def rand_insurance() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(16)])


def rand_iol_params():
    """Типичные биометрические параметры глаза."""
    al = round(random.uniform(21.0, 26.5), 2)   # Axial Length
    k1 = round(random.uniform(41.0, 46.0), 2)   # Keratometry 1
    k2 = round(random.uniform(42.0, 47.0), 2)   # Keratometry 2
    if k2 < k1:
        k1, k2 = k2, k1
    acd = round(random.uniform(2.5, 4.0), 2)    # Anterior Chamber Depth
    return al, k1, k2, acd


class Command(BaseCommand):
    help = "Заполняет БД реалистичными тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить все таблицы перед заполнением",
        )

    def handle(self, *args, **options):
        # Импорты внутри handle, чтобы Django успел инициализироваться
        from app.models import (
            User, Patient, PreparationTemplate, PatientPreparation,
            MediaFile, IOLCalculation, SurgeonFeedback,
            Notification, AuditLog,
        )
        from app.iol_calculations import IOLCalculator

        if options["clear"]:
            self.stdout.write("🗑  Очистка таблиц...")
            AuditLog.objects.all().delete()
            Notification.objects.all().delete()
            SurgeonFeedback.objects.all().delete()
            IOLCalculation.objects.all().delete()
            MediaFile.objects.all().delete()
            PatientPreparation.objects.all().delete()
            PreparationTemplate.objects.all().delete()
            Patient.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("   Таблицы очищены.\n"))

        # ── 1. Пользователи ───────────────────────────────────────────────────
        self.stdout.write("👤 Создание пользователей...")

        DEFAULT_PASSWORD = "Test1234!"

        # Администратор
        admin, _ = User.objects.get_or_create(
            email="admin@oculus.ru",
            defaults=dict(
                first_name="Администратор",
                last_name="Системный",
                middle_name="Иванович",
                role="admin",
                is_staff=True,
                is_superuser=True,
                is_active=True,
                password=make_password(DEFAULT_PASSWORD),
            ),
        )

        # Участковые врачи
        doctors_data = [
            ("Смирнова",  "Ольга",    "Петровна",   "doctor1@oculus.ru"),
            ("Захаров",   "Владимир", "Николаевич",  "doctor2@oculus.ru"),
            ("Крылова",   "Наталья",  "Сергеевна",   "doctor3@oculus.ru"),
        ]
        doctors = []
        for last, first, mid, email in doctors_data:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last, middle_name=mid,
                    role="district_doctor", is_active=True,
                    password=make_password(DEFAULT_PASSWORD),
                ),
            )
            doctors.append(u)

        # Хирурги
        surgeons_data = [
            ("Громов",   "Дмитрий",  "Алексеевич",  "surgeon1@oculus.ru", "ХИР-001-2019"),
            ("Беликова", "Марина",   "Владимировна", "surgeon2@oculus.ru", "ХИР-002-2020"),
            ("Орлов",    "Сергей",   "Михайлович",   "surgeon3@oculus.ru", "ХИР-003-2018"),
            ("Тихонова", "Людмила",  "Андреевна",    "surgeon4@oculus.ru", "ХИР-004-2021"),
        ]
        surgeons = []
        for last, first, mid, email, lic in surgeons_data:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last, middle_name=mid,
                    role="surgeon", is_active=True,
                    medical_license_number=lic,
                    password=make_password(DEFAULT_PASSWORD),
                ),
            )
            surgeons.append(u)

        self.stdout.write(f"   ✓ {1 + len(doctors) + len(surgeons)} пользователей")

        # ── 2. Шаблоны подготовки ─────────────────────────────────────────────
        self.stdout.write("📋 Создание шаблонов подготовки...")
        templates = []
        for stype, title, req_file, required in PREPARATION_TEMPLATES_DATA:
            t, _ = PreparationTemplate.objects.get_or_create(
                surgery_type=stype,
                title=title,
                defaults=dict(requires_file=req_file, required=required),
            )
            templates.append(t)
        self.stdout.write(f"   ✓ {len(templates)} шаблонов")

        # ── 3. Пациенты ───────────────────────────────────────────────────────
        self.stdout.write("🏥 Создание пациентов...")

        statuses = ["red", "red", "red", "yellow", "yellow", "green", "green", "blue"]
        patients = []

        for i in range(30):
            gender = random.choice(["male", "female"])
            last_name  = random.choice(LAST_NAMES)
            first_name = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
            middle     = random.choice(MIDDLE_NAMES_M if gender == "male" else MIDDLE_NAMES_F)
            diag_icd, diag_text = random.choice(DIAGNOSES_ICD10)
            surgery_type = random.choice(SURGERY_TYPES)
            status = random.choice(statuses)

            surgery_date = None
            if status == "blue":
                surgery_date = date.today() + timedelta(days=random.randint(3, 60))
            elif status == "green":
                surgery_date = date.today() + timedelta(days=random.randint(14, 90))

            p = Patient.objects.create(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle,
                birth_date=rand_date_past(30, 80),
                gender=gender,
                passport_series=rand_passport_series(),
                passport_number=rand_passport_number(),
                passport_issued_by=f"УМВД России по г. {random.choice(['Москва', 'Санкт-Петербург', 'Казань', 'Новосибирск', 'Екатеринбург'])}",
                passport_issue_date=rand_date_past(1, 15),
                snils=rand_snils(),
                insurance_policy=rand_insurance(),
                diagnosis_icd10=diag_icd,
                diagnosis_text=diag_text,
                surgery_type=surgery_type,
                status=status,
                surgery_date=surgery_date,
                created_by=random.choice(doctors),
                created_at=rand_datetime_past(1, 120),
            )
            patients.append(p)

        self.stdout.write(f"   ✓ {len(patients)} пациентов")

        # ── 4. Пользователи-пациенты (linked) ────────────────────────────────
        self.stdout.write("🔗 Создание аккаунтов пациентов...")
        patient_users = []
        for patient in patients[:5]:
            email = f"patient_{patient.id.hex[:6]}@mail.ru"
            u, _ = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=patient.first_name,
                    last_name=patient.last_name,
                    middle_name=patient.middle_name,
                    role="patient",
                    is_active=True,
                    linked_patient=patient,
                    password=make_password(DEFAULT_PASSWORD),
                ),
            )
            patient_users.append(u)
        self.stdout.write(f"   ✓ {len(patient_users)} аккаунтов пациентов")

        # ── 5. Пункты подготовки пациентов ───────────────────────────────────
        self.stdout.write("✅ Создание пунктов подготовки...")
        preps_created = 0
        for patient in patients:
            stype = patient.surgery_type
            matching = [t for t in templates if t.surgery_type == stype]
            if not matching:
                matching = random.sample(templates, min(4, len(templates)))
            for tmpl in matching:
                completed = random.random() > 0.45
                PatientPreparation.objects.create(
                    patient=patient,
                    template=tmpl,
                    completed=completed,
                    completion_date=date.today() - timedelta(days=random.randint(1, 30)) if completed else None,
                    comment=random.choice([None, None, "Анализ сдан в частной лаборатории", "Повторный анализ"]),
                    created_at=rand_datetime_past(2, 90),
                )
                preps_created += 1
        self.stdout.write(f"   ✓ {preps_created} пунктов подготовки")

        # ── 6. Расчёты ИОЛ ───────────────────────────────────────────────────
        self.stdout.write("🔬 Создание расчётов ИОЛ...")
        formulas = ["srk_t", "holladay", "haigis", "barrett", "hoffer_q"]
        iol_created = 0

        for patient in patients:
            n_calcs = random.randint(0, 3)
            for _ in range(n_calcs):
                al, k1, k2, acd = rand_iol_params()
                formula = random.choice(formulas)
                eye = random.choice(["right", "left"])
                try:
                    result = IOLCalculator.calculate_with_formula(formula, al, k1, k2, acd)
                except ValueError:
                    result = round(random.uniform(15.0, 25.0), 2)

                IOLCalculation.objects.create(
                    patient=patient,
                    eye=eye,
                    k1=k1, k2=k2, acd=acd, axial_length=al,
                    formula_used=formula,
                    result_diopters=result,
                    calculated_by=random.choice(surgeons + doctors),
                    created_at=rand_datetime_past(1, 60),
                )
                iol_created += 1
        self.stdout.write(f"   ✓ {iol_created} расчётов ИОЛ")

        # ── 7. Обратная связь хирургов ────────────────────────────────────────
        self.stdout.write("💬 Создание отзывов хирургов...")
        feedback_statuses = ["success", "success", "success", "complications", "postponed", "cancelled"]
        feedback_created = 0
        operated_patients = [p for p in patients if p.status in ("green", "blue")]

        for patient in operated_patients:
            if random.random() > 0.3:
                SurgeonFeedback.objects.create(
                    patient=patient,
                    surgeon=random.choice(surgeons),
                    comment=random.choice(FEEDBACK_COMMENTS),
                    status_after=random.choice(feedback_statuses),
                    created_at=rand_datetime_past(1, 30),
                )
                feedback_created += 1
        self.stdout.write(f"   ✓ {feedback_created} отзывов")

        # ── 8. Уведомления ────────────────────────────────────────────────────
        self.stdout.write("🔔 Создание уведомлений...")
        all_users = doctors + surgeons
        notif_created = 0
        for _ in range(40):
            user = random.choice(all_users)
            patient = random.choice(patients)
            Notification.objects.create(
                user=user,
                patient=patient,
                message=f"{random.choice(NOTIFICATION_MESSAGES)}: {patient.last_name} {patient.first_name[0]}.",
                sent=random.random() > 0.3,
                created_at=rand_datetime_past(0, 30),
            )
            notif_created += 1
        self.stdout.write(f"   ✓ {notif_created} уведомлений")

        # ── 9. Журнал аудита ──────────────────────────────────────────────────
        self.stdout.write("📝 Создание записей аудита...")
        entity_types = ["Patient", "IOLCalculation", "MediaFile", "PatientPreparation", "SurgeonFeedback"]
        audit_created = 0
        for _ in range(80):
            user = random.choice(doctors + surgeons + [admin])
            patient = random.choice(patients)
            AuditLog.objects.create(
                user=user,
                action=random.choice(AUDIT_ACTIONS),
                entity_type=random.choice(entity_types),
                entity_id=patient.id,
                created_at=rand_datetime_past(0, 60),
            )
            audit_created += 1
        self.stdout.write(f"   ✓ {audit_created} записей аудита")

        # ── Итог ──────────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ База данных успешно заполнена!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("")
        self.stdout.write("📊 Статистика:")
        self.stdout.write(f"   Пользователей:           {User.objects.count()}")
        self.stdout.write(f"   Пациентов:               {Patient.objects.count()}")
        self.stdout.write(f"   Шаблонов подготовки:     {PreparationTemplate.objects.count()}")
        self.stdout.write(f"   Пунктов подготовки:      {PatientPreparation.objects.count()}")
        self.stdout.write(f"   Расчётов ИОЛ:            {IOLCalculation.objects.count()}")
        self.stdout.write(f"   Отзывов хирургов:        {SurgeonFeedback.objects.count()}")
        self.stdout.write(f"   Уведомлений:             {Notification.objects.count()}")
        self.stdout.write(f"   Записей аудита:          {AuditLog.objects.count()}")
        self.stdout.write("")
        self.stdout.write("🔑 Учётные данные (все пароли: Test1234!):")
        self.stdout.write(f"   Администратор:    admin@oculus.ru")
        self.stdout.write(f"   Врачи:            doctor1@oculus.ru  /  doctor2@oculus.ru  /  doctor3@oculus.ru")
        self.stdout.write(f"   Хирурги:          surgeon1@oculus.ru ... surgeon4@oculus.ru")
        self.stdout.write(f"   Пациент (пример): patient_XXXXXX@mail.ru  (см. базу)")
        self.stdout.write("")
