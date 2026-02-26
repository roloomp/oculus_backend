from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from .iol_calculations import IOLCalculator
from rest_framework import status
from .analytics import DoctorAnalytics
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
import os

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'gender', 'surgery_type']
    search_fields = ['last_name', 'first_name', 'passport_number']
    ordering_fields = ['created_at', 'surgery_date', 'last_name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def preparations(self, request, pk=None):
        patient = self.get_object()
        preparations = PatientPreparation.objects.filter(patient=patient)
        serializer = PatientPreparationSerializer(preparations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def iol_calculations(self, request, pk=None):
        patient = self.get_object()
        calculations = IOLCalculation.objects.filter(patient=patient)
        serializer = IOLCalculationSerializer(calculations, many=True)
        return Response(serializer.data)

    # В PatientViewSet добавьте:
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Полная медицинская история пациента"""
        patient = self.get_object()

        data = {
            'patient': PatientSerializer(patient).data,
            'iol_calculations': IOLCalculationSerializer(
                IOLCalculation.objects.filter(patient=patient),
                many=True
            ).data,
            'media_files': MediaFileSerializer(
                MediaFile.objects.filter(patient=patient),
                many=True
            ).data,
            'feedback': SurgeonFeedbackSerializer(
                SurgeonFeedback.objects.filter(patient=patient),
                many=True
            ).data
        }
        return Response(data)


class PreparationTemplateViewSet(viewsets.ModelViewSet):
    queryset = PreparationTemplate.objects.all()
    serializer_class = PreparationTemplateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['surgery_type', 'title']


class PatientPreparationViewSet(viewsets.ModelViewSet):
    queryset = PatientPreparation.objects.all()
    serializer_class = PatientPreparationSerializer

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        preparation = self.get_object()
        preparation.completed = True
        preparation.completion_date = timezone.now()
        preparation.save()
        return Response({'status': 'completed'})

class SurgeonFeedbackViewSet(viewsets.ModelViewSet):
    queryset = SurgeonFeedback.objects.all()
    serializer_class = SurgeonFeedbackSerializer

    def perform_create(self, serializer):
        serializer.save(surgeon=self.request.user)


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class IOLCalculationViewSet(viewsets.ModelViewSet):
    queryset = IOLCalculation.objects.all()
    serializer_class = IOLCalculationDetailSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return IOLCalculationSerializer
        return IOLCalculationDetailSerializer

    def perform_create(self, serializer):
        serializer.save(calculated_by=self.request.user)

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Эндпоинт для предварительного расчета без сохранения
        """
        try:
            axial_length = request.data.get('axial_length')
            k1 = request.data.get('k1')
            k2 = request.data.get('k2')
            acd = request.data.get('acd')
            formula = request.data.get('formula', 'all')

            # Валидация входных данных
            if not all([axial_length, k1, k2, acd]):
                return Response(
                    {'error': 'Не все параметры предоставлены. Необходимы: axial_length, k1, k2, acd'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверка, что значения можно преобразовать в числа
            try:
                float(axial_length)
                float(k1)
                float(k2)
                float(acd)
            except ValueError:
                return Response(
                    {'error': 'Параметры должны быть числами'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Выполняем расчет
            if formula == 'all':
                results = IOLCalculator.calculate_all(axial_length, k1, k2, acd)
            else:
                result = IOLCalculator.calculate_with_formula(formula, axial_length, k1, k2, acd)
                results = {formula: result}

            return Response(results)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Неожиданная ошибка: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def calculate_and_save(self, request):
        """Рассчитать и сохранить результат"""
        try:
            # Получаем данные из запроса
            patient_id = request.data.get('patient_id')
            axial_length = request.data.get('axial_length')
            k1 = request.data.get('k1')
            k2 = request.data.get('k2')
            acd = request.data.get('acd')
            eye = request.data.get('eye', 'right')
            formula = request.data.get('formula', 'srk_t')

            # Проверяем обязательные поля
            if not all([patient_id, axial_length, k1, k2, acd]):
                return Response(
                    {'error': 'Не все параметры предоставлены'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Рассчитываем результат
            result = IOLCalculator.calculate_with_formula(
                formula, axial_length, k1, k2, acd
            )

            # Создаем запись в БД
            calculation = IOLCalculation.objects.create(
                patient_id=patient_id,
                eye=eye,
                k1=k1,
                k2=k2,
                acd=acd,
                axial_length=axial_length,
                formula_used=formula,
                result_diopters=result,
                calculated_by=request.user
            )

            serializer = IOLCalculationDetailSerializer(calculation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def compare_formulas(self, request, pk=None):
        """
        Сравнение результатов по разным формулам для сохраненного расчета
        """
        calculation = self.get_object()
        results = IOLCalculator.calculate_all(
            calculation.axial_length,
            calculation.k1,
            calculation.k2,
            calculation.acd
        )
        return Response(results)

    @action(detail=False, methods=['get'])
    def patient_history(self, request):
        """Получить историю расчетов для пациента"""
        patient_id = request.query_params.get('patient_id')

        if not patient_id:
            return Response(
                {'error': 'Необходим параметр patient_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        calculations = IOLCalculation.objects.filter(
            patient_id=patient_id
        ).order_by('-created_at')

        serializer = IOLCalculationDetailSerializer(calculations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def compare_for_patient(self, request, pk=None):
        """Сравнить результаты разных формул для пациента"""
        calculation = self.get_object()

        results = IOLCalculator.calculate_all(
            calculation.axial_length,
            calculation.k1,
            calculation.k2,
            calculation.acd
        )

        # Добавляем рекомендацию
        recommendation = IOLCalculator.get_recommendation(
            calculation.axial_length,
            calculation.k1,
            calculation.k2,
            calculation.acd
        )

        return Response({
            'calculations': results,
            'recommendation': recommendation,
            'patient_name': str(calculation.patient),
            'eye': calculation.eye
        })


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Главная панель аналитики"""
        doctor_id = request.query_params.get('doctor_id')
        data = DoctorAnalytics.get_dashboard_data(doctor_id)
        return Response(data)

    @action(detail=False, methods=['get'])
    def patients(self, request):
        """Статистика по пациентам"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        data = DoctorAnalytics.get_patient_statistics(start_date, end_date)
        return Response(data)

    @action(detail=False, methods=['get'])
    def surgeon_report(self, request):
        """Отчет по хирургу"""
        doctor_id = request.query_params.get('doctor_id')
        start_date = datetime.fromisoformat(request.query_params.get('start_date'))
        end_date = datetime.fromisoformat(request.query_params.get('end_date'))

        if not all([doctor_id, start_date, end_date]):
            return Response(
                {'error': 'Необходимы параметры: doctor_id, start_date, end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = DoctorAnalytics.generate_surgeon_report(doctor_id, start_date, end_date)
        return Response(data)

    @action(detail=False, methods=['get'])
    def iol_statistics(self, request):
        """Статистика расчетов IOL"""
        data = DoctorAnalytics.get_iol_statistics()
        return Response(data)


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return MediaFileSerializer
        return MediaFileDetailSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Скачивание файла"""
        media_file = self.get_object()

        if not media_file.file:
            raise Http404("Файл не найден")

        response = FileResponse(
            media_file.file.open('rb'),
            as_attachment=True,
            filename=media_file.file_name or os.path.basename(media_file.file.name)
        )
        return response

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Подтверждение документа"""
        media_file = self.get_object()
        media_file.is_verified = True
        media_file.verified_by = request.user
        media_file.verified_at = timezone.now()
        media_file.save()

        return Response({'status': 'verified'})

    @action(detail=False, methods=['get'])
    def patient_files(self, request):
        """Получение файлов конкретного пациента"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'Необходим параметр patient_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        files = self.queryset.filter(patient_id=patient_id)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)