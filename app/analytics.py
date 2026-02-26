from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Patient, SurgeonFeedback, IOLCalculation, User
from decimal import Decimal


class DoctorAnalytics:
    """Аналитика для врачей"""

    @staticmethod
    def get_patient_statistics(start_date=None, end_date=None):
        """Статистика по пациентам"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        queryset = Patient.objects.filter(created_at__range=[start_date, end_date])

        return {
            'total_patients': queryset.count(),
            'by_status': dict(queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_gender': dict(queryset.values('gender').annotate(count=Count('id')).values_list('gender', 'count')),
            'by_surgery_type': dict(
                queryset.values('surgery_type').annotate(count=Count('id')).values_list('surgery_type', 'count')[:10]),
            'new_patients_today': queryset.filter(created_at__date=timezone.now().date()).count(),
            'upcoming_surgeries': Patient.objects.filter(
                surgery_date__gte=timezone.now().date()
            ).count(),
        }

    @staticmethod
    def get_surgeon_performance(doctor_id=None, days=30):
        """Статистика работы хирургов"""
        start_date = timezone.now() - timedelta(days=days)

        feedback = SurgeonFeedback.objects.filter(
            created_at__gte=start_date
        )

        if doctor_id:
            feedback = feedback.filter(surgeon_id=doctor_id)

        stats = feedback.values('surgeon__id', 'surgeon__last_name', 'surgeon__first_name').annotate(
            total_operations=Count('id'),
            successful=Count('id', filter=Q(status_after='success')),
            with_complications=Count('id', filter=Q(status_after='complications')),
            postponed=Count('id', filter=Q(status_after='postponed')),
            cancelled=Count('id', filter=Q(status_after='cancelled'))
        )

        for stat in stats:
            total = stat['total_operations']
            if total > 0:
                stat['success_rate'] = (stat['successful'] / total) * 100
            else:
                stat['success_rate'] = 0

        return list(stats)

    @staticmethod
    def get_iol_statistics():
        """Статистика расчетов IOL"""
        calculations = IOLCalculation.objects.all()

        # Средние значения по формулам
        formula_avg = calculations.values('formula_used').annotate(
            avg_result=Avg('result_diopters'),
            count=Count('id')
        )

        # Распределение по глазам
        eye_distribution = calculations.values('eye').annotate(count=Count('id'))

        # Тренды по месяцам
        last_year = timezone.now() - timedelta(days=365)
        monthly_trends = calculations.filter(
            created_at__gte=last_year
        ).extra(
            {'month': "EXTRACT(month FROM created_at)",
             'year': "EXTRACT(year FROM created_at)"}
        ).values('year', 'month').annotate(
            count=Count('id'),
            avg_diopters=Avg('result_diopters')
        ).order_by('year', 'month')

        return {
            'by_formula': list(formula_avg),
            'eye_distribution': list(eye_distribution),
            'monthly_trends': list(monthly_trends),
            'total_calculations': calculations.count(),
        }

    @staticmethod
    def get_dashboard_data(doctor_id=None):
        """Сводная информация для дашборда"""
        return {
            'patient_statistics': DoctorAnalytics.get_patient_statistics(),
            'surgeon_performance': DoctorAnalytics.get_surgeon_performance(doctor_id),
            'iol_statistics': DoctorAnalytics.get_iol_statistics(),
            'recent_activities': DoctorAnalytics.get_recent_activities(),
        }

    @staticmethod
    def get_recent_activities(limit=10):
        """Последние активности в системе"""
        from .models import AuditLog

        return AuditLog.objects.select_related('user').order_by('-created_at')[:limit].values(
            'user__email', 'action', 'entity_type', 'created_at'
        )

    @staticmethod
    def generate_surgeon_report(doctor_id, start_date, end_date):
        """Детальный отчет по хирургу"""
        surgeon = User.objects.get(id=doctor_id)
        feedbacks = SurgeonFeedback.objects.filter(
            surgeon_id=doctor_id,
            created_at__range=[start_date, end_date]
        ).select_related('patient')

        patients = Patient.objects.filter(surgeonfeedback__in=feedbacks).distinct()

        return {
            'surgeon': f"{surgeon.last_name} {surgeon.first_name}",
            'period': f"{start_date.date()} - {end_date.date()}",
            'total_operations': feedbacks.count(),
            'success_rate': feedbacks.filter(
                status_after='success').count() / feedbacks.count() * 100 if feedbacks.exists() else 0,
            'patients_by_status': dict(
                patients.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'complications': feedbacks.filter(status_after='complications').count(),
            'recent_feedback': list(feedbacks.order_by('-created_at')[:10].values(
                'patient__last_name', 'patient__first_name', 'status_after', 'comment', 'created_at'
            )),
        }