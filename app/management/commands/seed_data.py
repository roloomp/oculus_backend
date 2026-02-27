
import random
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password

LAST_NAMES = [
    "Иванов",    "Петров",    "Сидоров",   "Козлов",    "Новиков",
    "Морозов",   "Волков",    "Соловьёв",  "Васильев",  "Зайцев",
    "Павлов",    "Семёнов",   "Голубев",   "Виноградов","Богданов",
    "Воробьёв",  "Фёдоров",   "Михайлов",  "Беляев",    "Тарасов",
    "Белова",    "Комарова",  "Орлова",    "Кузнецова", "Попова",
    "Лебедева",  "Козлова",   "Новикова",  "Соколова",  "Михайлова",
]

FIRST_NAMES_M = [
    "Александр", "Дмитрий", "Максим",  "Сергей",  "Андрей",
    "Алексей",   "Артём",   "Илья",    "Кирилл",  "Михаил",
    "Никита",    "Роман",   "Евгений", "Виктор",  "Игорь",
]

FIRST_NAMES_F = [
    "Анна",      "Мария",    "Елена",    "Ольга",    "Наталья",
    "Татьяна",   "Светлана", "Ирина",    "Юлия",     "Екатерина",
    "Алина",     "Валерия",  "Дарья",    "Полина",   "Кристина",
]

MIDDLE_NAMES_M = [
    "Александрович", "Дмитриевич",  "Сергеевич",   "Андреевич",  "Алексеевич",
    "Михайлович",    "Владимирович","Игоревич",     "Николаевич", "Петрович",
]

MIDDLE_NAMES_F = [
    "Александровна", "Дмитриевна",  "Сергеевна",   "Андреевна",  "Алексеевна",
    "Михайловна",    "Владимировна","Игоревна",     "Николаевна", "Петровна",
]

SURGERY_TYPES = [
    "Факоэмульсификация катаракты",
    "Имплантация ИОЛ",
    "Лазерная коррекция зрения",
    "Трабекулэктомия",
    "Витрэктомия",
    "Кератопластика",
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
    ("Факоэмульсификация катаракты", "Общий анализ крови",            False, True),
    ("Факоэмульсификация катаракты", "Биохимический анализ крови",    False, True),
    ("Факоэмульсификация катаракты", "Коагулограмма",                 False, True),
    ("Факоэмульсификация катаракты", "ЭКГ",                           True,  True),
    ("Факоэмульсификация катаракты", "Флюорография",                  True,  True),
    ("Факоэмульсификация катаракты", "Осмотр терапевта",              True,  True),
    ("Факоэмульсификация катаракты", "Биометрия глаза",               True,  True),
    ("Факоэмульсификация катаракты", "УЗИ глаза (B-scan)",            True,  False),
    ("Имплантация ИОЛ", "Общий анализ крови",                         False, True),
    ("Имплантация ИОЛ", "Биохимический анализ крови",                 False, True),
    ("Имплантация ИОЛ", "Коагулограмма",                              False, True),
    ("Имплантация ИОЛ", "ЭКГ",                                        True,  True),
    ("Имплантация ИОЛ", "Флюорография",                               True,  True),
    ("Имплантация ИОЛ", "Биометрия глаза",                            True,  True),
    ("Имплантация ИОЛ", "Расчёт ИОЛ",                                 False, True),
    ("Имплантация ИОЛ", "Осмотр терапевта",                           True,  True),
    ("Лазерная коррекция зрения", "Общий анализ крови",               False, True),
    ("Лазерная коррекция зрения", "Кератотопография",                 True,  True),
    ("Лазерная коррекция зрения", "Авторефрактометрия",               False, True),
    ("Лазерная коррекция зрения", "Пахиметрия роговицы",              False, True),
    ("Лазерная коррекция зрения", "Осмотр офтальмолога",              True,  True),
    ("Антиглаукоматозная операция", "Общий анализ крови",             False, True),
    ("Антиглаукоматозная операция", "Биохимический анализ крови",     False, True),
    ("Антиглаукоматозная операция", "Суточная тонометрия",            False, True),
    ("Антиглаукоматозная операция", "Периметрия",                     True,  True),
    ("Антиглаукоматозная операция", "ОКТ диска зрительного нерва",    True,  True),
    ("Антиглаукоматозная операция", "Гониоскопия",                    False, True),
    ("Антиглаукоматозная операция", "ЭКГ",                            True,  True),
    ("Витрэктомия", "Общий анализ крови",                             False, True),
    ("Витрэктомия", "Биохимический анализ крови",                     False, True),
    ("Витрэктомия", "Коагулограмма",                                  False, True),
    ("Витрэктомия", "УЗИ глаза (B-scan)",                             True,  True),
    ("Витрэктомия", "ОКТ сетчатки",                                   True,  True),
    ("Витрэктомия", "ФАГ",                                            True,  False),
    ("Витрэктомия", "Осмотр кардиолога",                              True,  True),
    ("Кератопластика", "Общий анализ крови",                          False, True),
    ("Кератопластика", "Биохимический анализ крови",                  False, True),
    ("Кератопластика", "Коагулограмма",                               False, True),
    ("Кератопластика", "ЭКГ",                                         True,  True),
    ("Кератопластика", "Топография роговицы",                         True,  True),
    ("Кератопластика", "Осмотр терапевта",                            True,  True),
    ("Трабекулэктомия", "Общий анализ крови",                         False, True),
    ("Трабекулэктомия", "Биохимический анализ крови",                 False, True),
    ("Трабекулэктомия", "ЭКГ",                                        True,  True),
    ("Трабекулэктомия", "Периметрия",                                 True,  True),
    ("Трабекулэктомия", "Тонометрия",                                 False, True),
    ("Трабекулэктомия", "ОКТ диска зрительного нерва",                True,  False),
]

REFERRAL_COMMENTS = [
    "Необходимо повторить ОАК — показатели гемоглобина вне нормы. Прошу направить на повторный анализ.",
    "Результаты коагулограммы вызывают опасения: МНО 2.8. Требуется консультация гематолога и корректировка антикоагулянтной терапии.",
    "На ЭКГ выявлена мерцательная аритмия. Необходима консультация кардиолога и заключение о допуске к операции.",
    "Флюорография устарела (более 12 месяцев). Прошу направить на актуальный снимок.",
    "Биометрия глаза выполнена некорректно — данные K1/K2 не совпадают с клинической картиной. Необходимо повторное исследование.",
    "Показатели АД при осмотре: 180/110. Операция противопоказана до стабилизации давления. Прошу направить к кардиологу.",
    "Уровень глюкозы 11.2 ммоль/л. Требуется консультация эндокринолога и компенсация сахарного диабета.",
    "Пахиметрия роговицы: 430 мкм — нижняя граница для лазерной коррекции. Прошу провести повторное измерение и ОКТ роговицы.",
    "Осмотр терапевта устарел (более 30 дней). Необходимо актуальное заключение о допуске к операции.",
    "На B-scan выявлено помутнение стекловидного тела. Требуется дополнительное ОКТ сетчатки.",
    "Результаты анализов не загружены в систему. Прошу загрузить все документы перед повторным запросом.",
    "Срок действия общего анализа крови истёк. Пациент должен сдать повторно — допустимый срок не более 14 дней до операции.",
]

NOTIFICATION_MESSAGES = [
    "Напоминание: завтра плановая операция пациента",
    "Пациент записан на предоперационный осмотр",
    "Готовы результаты биометрии",
    "Требуется верификация загруженных документов",
    "Пациент подтвердил явку на операцию",
    "Срок действия анализов истекает через 3 дня",
    "Новый запрос на операцию от участкового врача",
    "Хирург направил пациента на доследование",
    "Пациент переведён в статус «Готов к операции»",
    "Дата операции назначена хирургом",
]

AUDIT_ACTIONS = [
    "Добавление пациента",
    "Редактирование карточки пациента",
    "Загрузка документа",
    "Расчёт ИОЛ",
    "Запрос операции участковым врачом",
    "Направление на доследование",
    "Верификация документа",
    "Назначение даты операции хирургом",
    "Просмотр карточки пациента",
    "Изменение статуса пациента",
]


def rand_date_past(years_min=20, years_max=80):
    return date.today() - timedelta(days=random.randint(years_min * 365, years_max * 365))


def rand_datetime_past(days_min=0, days_max=180):
    delta = timedelta(
        days=random.randint(days_min, days_max),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return timezone.now() - delta


def rand_passport_series():
    return f"{random.randint(10, 99)} {random.randint(10, 99)}"


def rand_passport_number():
    return str(random.randint(100000, 999999))


def rand_snils():
    n = str(random.randint(100_000_000, 999_999_999))
    return f"{n[:3]}-{n[3:6]}-{n[6:9]} {random.randint(10, 99)}"


def rand_insurance():
    return "".join(str(random.randint(0, 9)) for _ in range(16))


def rand_iol_params():
    al  = round(random.uniform(21.0, 26.5), 2)
    k1  = round(random.uniform(41.0, 46.0), 2)
    k2  = round(random.uniform(42.0, 47.0), 2)
    if k2 < k1:
        k1, k2 = k2, k1
    acd = round(random.uniform(2.5, 4.0), 2)
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
        from app.models import (
            User, Patient, PreparationTemplate, PatientPreparation,
            IOLCalculation, SurgeonFeedback, Notification, AuditLog,
        )
        from app.iol_calculations import IOLCalculator

        if options["clear"]:
            self.stdout.write("🗑  Очистка таблиц...")
            AuditLog.objects.all().delete()
            Notification.objects.all().delete()
            SurgeonFeedback.objects.all().delete()
            IOLCalculation.objects.all().delete()
            PatientPreparation.objects.all().delete()
            PreparationTemplate.objects.all().delete()
            User.objects.filter(role="patient").update(linked_patient=None)
            Patient.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("   Таблицы очищены.\n"))

        DEFAULT_PASSWORD = "Test1234!"

        self.stdout.write("👤 Создание пользователей...")

        admin, _ = User.objects.get_or_create(
            email="admin@oculus.ru",
            defaults=dict(
                first_name="Администратор", last_name="Системный", middle_name="Иванович",
                role="admin", is_staff=True, is_superuser=True, is_active=True,
                password=make_password(DEFAULT_PASSWORD),
            ),
        )

        doctors = []
        for last, first, mid, email in [
            ("Смирнова",  "Ольга",    "Петровна",   "doctor1@oculus.ru"),
            ("Захаров",   "Владимир", "Николаевич",  "doctor2@oculus.ru"),
            ("Крылова",   "Наталья",  "Сергеевна",   "doctor3@oculus.ru"),
        ]:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=first, last_name=last, middle_name=mid,
                    role="district_doctor", is_active=True,
                    password=make_password(DEFAULT_PASSWORD),
                ),
            )
            doctors.append(u)

        surgeons = []
        for last, first, mid, email, lic in [
            ("Громов",   "Дмитрий", "Алексеевич",   "surgeon1@oculus.ru", "ХИР-001-2019"),
            ("Беликова", "Марина",  "Владимировна",  "surgeon2@oculus.ru", "ХИР-002-2020"),
            ("Орлов",    "Сергей",  "Михайлович",    "surgeon3@oculus.ru", "ХИР-003-2018"),
            ("Тихонова", "Людмила", "Андреевна",     "surgeon4@oculus.ru", "ХИР-004-2021"),
        ]:
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

        self.stdout.write("📋 Создание шаблонов подготовки...")
        templates = []
        for stype, title, req_file, required in PREPARATION_TEMPLATES_DATA:
            t, _ = PreparationTemplate.objects.get_or_create(
                surgery_type=stype, title=title,
                defaults=dict(requires_file=req_file, required=required),
            )
            templates.append(t)
        self.stdout.write(f"   ✓ {len(templates)} шаблонов")

        self.stdout.write("🏥 Создание пациентов...")

        status_pool = (
            ["red"]    * 10 +
            ["yellow"] * 8  +
            ["green"]  * 7  +
            ["blue"]   * 5
        )

        CITIES = [
            "Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург",
            "Нижний Новгород", "Самара", "Ростов-на-Дону", "Уфа", "Омск",
        ]

        patients = []
        for _ in range(30):
            gender      = random.choice(["male", "female"])
            last_name   = random.choice(LAST_NAMES)
            first_name  = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
            middle      = random.choice(MIDDLE_NAMES_M if gender == "male" else MIDDLE_NAMES_F)
            diag_icd, diag_text = random.choice(DIAGNOSES_ICD10)
            surgery_type = random.choice(SURGERY_TYPES)
            status = random.choice(status_pool)

            surgery_date = None
            if status == "blue":
                surgery_date = date.today() + timedelta(days=random.randint(5, 60))

            p = Patient.objects.create(
                last_name=last_name, first_name=first_name, middle_name=middle,
                birth_date=rand_date_past(30, 80),
                gender=gender,
                passport_series=rand_passport_series(),
                passport_number=rand_passport_number(),
                passport_issued_by=f"УМВД России по г. {random.choice(CITIES)}",
                passport_issue_date=rand_date_past(1, 15),
                snils=rand_snils(),
                insurance_policy=rand_insurance(),
                diagnosis_icd10=diag_icd,
                diagnosis_text=diag_text,
                surgery_type=surgery_type,
                status=status,
                surgery_date=surgery_date,
                created_by=random.choice(doctors),
                created_at=rand_datetime_past(1, 180),
            )
            patients.append(p)

        self.stdout.write(f"   ✓ {len(patients)} пациентов")

        self.stdout.write("🔗 Создание аккаунтов пациентов...")
        patient_users = []
        for patient in patients[:5]:
            email = f"patient_{patient.id.hex[:6]}@mail.ru"
            u, _ = User.objects.get_or_create(
                email=email,
                defaults=dict(
                    first_name=patient.first_name, last_name=patient.last_name,
                    middle_name=patient.middle_name, role="patient", is_active=True,
                    linked_patient=patient, password=make_password(DEFAULT_PASSWORD),
                ),
            )
            patient_users.append(u)
        self.stdout.write(f"   ✓ {len(patient_users)} аккаунтов пациентов")

        self.stdout.write("✅ Создание пунктов подготовки...")
        preps_created = 0
        for patient in patients:
            stype    = patient.surgery_type
            matching = [t for t in templates if t.surgery_type == stype]
            if not matching:
                matching = random.sample(templates, min(4, len(templates)))

            complete_chance = {
                "red":    0.10,
                "yellow": 0.50,
                "green":  0.90,
                "blue":   0.95,
            }.get(patient.status, 0.5)

            for tmpl in matching:
                completed = random.random() < complete_chance
                PatientPreparation.objects.create(
                    patient=patient,
                    template=tmpl,
                    completed=completed,
                    completion_date=(
                        date.today() - timedelta(days=random.randint(1, 30))
                        if completed else None
                    ),
                    comment=random.choice(
                        [None, None, None,
                         "Анализ сдан в частной лаборатории",
                         "Повторный анализ после лечения"]
                    ),
                    created_at=rand_datetime_past(2, 90),
                )
                preps_created += 1
        self.stdout.write(f"   ✓ {preps_created} пунктов подготовки")

        self.stdout.write("🔭 Создание расчётов ИОЛ...")
        formulas = ["srk_t", "holladay", "haigis", "barrett", "hoffer_q"]
        iol_created = 0

        for patient in [p for p in patients if p.status in ("yellow", "green", "blue")]:
            for _ in range(random.randint(1, 3)):
                al, k1, k2, acd = rand_iol_params()
                formula = random.choice(formulas)
                eye     = random.choice(["right", "left"])
                try:
                    result = IOLCalculator.calculate_with_formula(formula, al, k1, k2, acd)
                except Exception:
                    result = round(random.uniform(15.0, 25.0), 2)
                IOLCalculation.objects.create(
                    patient=patient, eye=eye,
                    k1=k1, k2=k2, acd=acd, axial_length=al,
                    formula_used=formula, result_diopters=result,
                    calculated_by=random.choice(surgeons + doctors),
                    created_at=rand_datetime_past(1, 60),
                )
                iol_created += 1
        self.stdout.write(f"   ✓ {iol_created} расчётов ИОЛ")

        self.stdout.write("🔬 Создание направлений на доследование...")
        referral_created = 0

        for patient in [p for p in patients if p.status == "yellow"]:
            if random.random() < 0.6:
                SurgeonFeedback.objects.create(
                    patient=patient,
                    surgeon=random.choice(surgeons),
                    comment=random.choice(REFERRAL_COMMENTS),
                    action_type="reexamine",
                    created_at=rand_datetime_past(3, 45),
                )
                referral_created += 1

        green_patients = [p for p in patients if p.status == "green"]
        for patient in random.sample(green_patients, k=min(2, len(green_patients))):
            SurgeonFeedback.objects.create(
                patient=patient,
                surgeon=random.choice(surgeons),
                comment=random.choice(REFERRAL_COMMENTS),
                action_type="reexamine",
                created_at=rand_datetime_past(20, 60),
            )
            referral_created += 1

        self.stdout.write(f"   ✓ {referral_created} направлений на доследование")

        self.stdout.write("🔔 Создание уведомлений...")
        notif_created = 0
        for _ in range(40):
            user    = random.choice(doctors + surgeons)
            patient = random.choice(patients)
            Notification.objects.create(
                user=user, patient=patient,
                message=(
                    f"{random.choice(NOTIFICATION_MESSAGES)}: "
                    f"{patient.last_name} {patient.first_name[0]}."
                ),
                sent=random.random() > 0.3,
                created_at=rand_datetime_past(0, 30),
            )
            notif_created += 1
        self.stdout.write(f"   ✓ {notif_created} уведомлений")

        self.stdout.write("📝 Создание записей аудита...")
        audit_created = 0
        for _ in range(100):
            user    = random.choice(doctors + surgeons + [admin])
            patient = random.choice(patients)
            AuditLog.objects.create(
                user=user,
                action=random.choice(AUDIT_ACTIONS),
                entity_type=random.choice(
                    ["Patient", "IOLCalculation", "PatientPreparation", "SurgeonFeedback"]
                ),
                entity_id=patient.id,
                created_at=rand_datetime_past(0, 90),
            )
            audit_created += 1
        self.stdout.write(f"   ✓ {audit_created} записей аудита")

        sc = {s: Patient.objects.filter(status=s).count() for s in ("red", "yellow", "green", "blue")}

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 54))
        self.stdout.write(self.style.SUCCESS("  ✅  База данных успешно заполнена!"))
        self.stdout.write(self.style.SUCCESS("=" * 54))
        self.stdout.write("")
        self.stdout.write("📊 Статистика:")
        self.stdout.write(f"   Пользователей:               {User.objects.count()}")
        self.stdout.write(f"   Пациентов:                   {Patient.objects.count()}")
        self.stdout.write(f"     🔴 red    (неполные):       {sc['red']}")
        self.stdout.write(f"     🟡 yellow (подготовка):     {sc['yellow']}")
        self.stdout.write(f"     🟢 green  (запрос опер.):   {sc['green']}")
        self.stdout.write(f"     🔵 blue   (дата назнач.):   {sc['blue']}")
        self.stdout.write(f"   Шаблонов подготовки:         {PreparationTemplate.objects.count()}")
        self.stdout.write(f"   Пунктов подготовки:          {PatientPreparation.objects.count()}")
        self.stdout.write(f"   Расчётов ИОЛ:                {IOLCalculation.objects.count()}")
        self.stdout.write(f"   Направлений на доследование: {SurgeonFeedback.objects.count()}")
        self.stdout.write(f"   Уведомлений:                 {Notification.objects.count()}")
        self.stdout.write(f"   Записей аудита:              {AuditLog.objects.count()}")
        self.stdout.write("")
        self.stdout.write("🔑 Учётные данные (пароль для всех: Test1234!):")
        self.stdout.write("   Администратор : admin@oculus.ru")
        self.stdout.write("   Врачи         : doctor1@oculus.ru  /  doctor2@oculus.ru  /  doctor3@oculus.ru")
        self.stdout.write("   Хирурги       : surgeon1@oculus.ru ... surgeon4@oculus.ru")
        self.stdout.write("   Пациент       : patient_XXXXXX@mail.ru  (см. таблицу users)")
        self.stdout.write("")