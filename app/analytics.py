from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Patient, SurgeonFeedback, IOLCalculation, User


class DoctorAnalytics:
    @staticmethod
    def get_patient_statistics(start_date=None, end_date=None):
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        queryset = Patient.objects.filter(created_at__range=[start_date, end_date])

        return {
            'total_patients': queryset.count(),
            'by_status': dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'by_gender': dict(
                queryset.values('gender').annotate(count=Count('id')).values_list('gender', 'count')
            ),
            'by_surgery_type': dict(
                queryset.values('surgery_type').annotate(count=Count('id'))
                .values_list('surgery_type', 'count')[:10]
            ),
            'new_patients_today': queryset.filter(created_at__date=timezone.now().date()).count(),
            'upcoming_surgeries': Patient.objects.filter(
                surgery_date__gte=timezone.now().date()
            ).count(),
        }

    @staticmethod
    def get_surgeon_performance(doctor_id=None, days=30):
        start_date = timezone.now() - timedelta(days=days)

        feedback = SurgeonFeedback.objects.filter(created_at__gte=start_date)

        if doctor_id:
            feedback = feedback.filter(surgeon_id=doctor_id)

        stats = list(
            feedback.values(
                'surgeon__id', 'surgeon__last_name', 'surgeon__first_name'
            ).annotate(
                total_operations=Count('id'),
                successful=Count('id', filter=Q(status_after='success')),
                with_complications=Count('id', filter=Q(status_after='complications')),
                postponed=Count('id', filter=Q(status_after='postponed')),
                cancelled=Count('id', filter=Q(status_after='cancelled')),
            )
        )

        # FIX: Division by zero guard moved here (was inside a loop that mutated a queryset dict)
        for stat in stats:
            total = stat['total_operations']
            stat['success_rate'] = round((stat['successful'] / total) * 100, 1) if total > 0 else 0

        return stats

    @staticmethod
    def get_iol_statistics():
        calculations = IOLCalculation.objects.all()

        formula_avg = list(
            calculations.values('formula_used').annotate(
                avg_result=Avg('result_diopters'),
                count=Count('id')
            )
        )

        eye_distribution = list(
            calculations.values('eye').annotate(count=Count('id'))
        )

        last_year = timezone.now() - timedelta(days=365)

        # FIX: Replaced deprecated .extra() with TruncMonth — standard Django ORM, DB-agnostic
        monthly_trends = list(
            calculations.filter(created_at__gte=last_year)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                count=Count('id'),
                avg_diopters=Avg('result_diopters'),
            )
            .order_by('month')
        )

        return {
            'by_formula': formula_avg,
            'eye_distribution': eye_distribution,
            'monthly_trends': monthly_trends,
            'total_calculations': calculations.count(),
        }

    @staticmethod
    def get_dashboard_data(doctor_id=None):
        return {
            'patient_statistics': DoctorAnalytics.get_patient_statistics(),
            'surgeon_performance': DoctorAnalytics.get_surgeon_performance(doctor_id),
            'iol_statistics': DoctorAnalytics.get_iol_statistics(),
            'recent_activities': list(DoctorAnalytics.get_recent_activities()),
        }

    @staticmethod
    def get_recent_activities(limit=10):
        from .models import AuditLog
        return AuditLog.objects.select_related('user').order_by('-created_at')[:limit].values(
            'user__email', 'action', 'entity_type', 'created_at'
        )

    @staticmethod
    def generate_surgeon_report(doctor_id, start_date, end_date):
        surgeon = User.objects.get(id=doctor_id)
        feedbacks = SurgeonFeedback.objects.filter(
            surgeon_id=doctor_id,
            created_at__range=[start_date, end_date]
        ).select_related('patient')

        total = feedbacks.count()
        # FIX: Safe division — check total > 0 before dividing
        success_rate = (
            round(feedbacks.filter(status_after='success').count() / total * 100, 1)
            if total > 0 else 0
        )

        patients = Patient.objects.filter(surgeonfeedback__in=feedbacks).distinct()

        return {
            'surgeon': f"{surgeon.last_name} {surgeon.first_name}",
            'period': f"{start_date.date()} - {end_date.date()}",
            'total_operations': total,
            'success_rate': success_rate,
            'patients_by_status': dict(
                patients.values('status').annotate(count=Count('id')).values_list('status', 'count')
            ),
            'complications': feedbacks.filter(status_after='complications').count(),
            'recent_feedback': list(
                feedbacks.order_by('-created_at')[:10].values(
                    'patient__last_name', 'patient__first_name',
                    'status_after', 'comment', 'created_at'
                )
            ),
        }
