from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from datetime import datetime
import os

from .models import (
    Patient, PreparationTemplate, PatientPreparation,
    MediaFile, IOLCalculation, SurgeonFeedback
)
from .serializers import (
    PatientSerializer, PreparationTemplateSerializer, PatientPreparationSerializer,
    MediaFileSerializer, MediaFileDetailSerializer, IOLCalculationSerializer,
    IOLCalculationDetailSerializer, SurgeonFeedbackSerializer, UserSerializer
)
from .iol_calculations import IOLCalculator
from .analytics import DoctorAnalytics
from .permissions import IsMedicalStaff, IsSurgeon, IsAdminOrReadOnly


class PatientViewSet(viewsets.ModelViewSet):
    # FIX: Added explicit role-based permission — only medical staff can access patients
    permission_classes = [IsMedicalStaff]
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

    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        data = {
            'patient': PatientSerializer(patient).data,
            'iol_calculations': IOLCalculationSerializer(
                IOLCalculation.objects.filter(patient=patient), many=True
            ).data,
            'media_files': MediaFileSerializer(
                MediaFile.objects.filter(patient=patient),
                many=True,
                context={'request': request}
            ).data,
            'feedback': SurgeonFeedbackSerializer(
                SurgeonFeedback.objects.filter(patient=patient), many=True
            ).data,
        }
        return Response(data)


class PreparationTemplateViewSet(viewsets.ModelViewSet):
    # FIX: Read for all medical staff; writes restricted to admins
    permission_classes = [IsAdminOrReadOnly]
    queryset = PreparationTemplate.objects.all()
    serializer_class = PreparationTemplateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['surgery_type', 'title']


class PatientPreparationViewSet(viewsets.ModelViewSet):
    # FIX: Only medical staff
    permission_classes = [IsMedicalStaff]
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
    # FIX: Only surgeons can create/edit feedback
    permission_classes = [IsSurgeon]
    queryset = SurgeonFeedback.objects.all()
    serializer_class = SurgeonFeedbackSerializer

    def perform_create(self, serializer):
        serializer.save(surgeon=self.request.user)


class CurrentUserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class IOLCalculationViewSet(viewsets.ModelViewSet):
    # FIX: Only medical staff can access IOL calculations
    permission_classes = [IsMedicalStaff]
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
        try:
            axial_length = request.data.get('axial_length')
            k1 = request.data.get('k1')
            k2 = request.data.get('k2')
            acd = request.data.get('acd')
            formula = request.data.get('formula', 'all')

            if not all([axial_length, k1, k2, acd]):
                return Response(
                    {'error': 'Не все параметры предоставлены. Необходимы: axial_length, k1, k2, acd'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                axial_length = float(axial_length)
                k1 = float(k1)
                k2 = float(k2)
                acd = float(acd)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Параметры должны быть числами'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if formula == 'all':
                results = IOLCalculator.calculate_all(axial_length, k1, k2, acd)
            else:
                result = IOLCalculator.calculate_with_formula(formula, axial_length, k1, k2, acd)
                results = {formula: result}

            return Response(results)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Неожиданная ошибка: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def calculate_and_save(self, request):
        try:
            patient_id = request.data.get('patient_id')
            axial_length = request.data.get('axial_length')
            k1 = request.data.get('k1')
            k2 = request.data.get('k2')
            acd = request.data.get('acd')
            eye = request.data.get('eye', 'right')
            formula = request.data.get('formula', 'srk_t')

            if not all([patient_id, axial_length, k1, k2, acd]):
                return Response(
                    {'error': 'Не все параметры предоставлены'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = IOLCalculator.calculate_with_formula(
                formula, float(axial_length), float(k1), float(k2), float(acd)
            )

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
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def compare_formulas(self, request, pk=None):
        calculation = self.get_object()
        results = IOLCalculator.calculate_all(
            float(calculation.axial_length),
            float(calculation.k1),
            float(calculation.k2),
            float(calculation.acd)
        )
        return Response(results)

    @action(detail=False, methods=['get'])
    def patient_history(self, request):
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
        calculation = self.get_object()
        al = float(calculation.axial_length)
        k1 = float(calculation.k1)
        k2 = float(calculation.k2)
        acd = float(calculation.acd)

        results = IOLCalculator.calculate_all(al, k1, k2, acd)
        recommendation = IOLCalculator.get_recommendation(al, k1, k2, acd)

        return Response({
            'calculations': results,
            'recommendation': recommendation,
            'patient_name': str(calculation.patient),
            'eye': calculation.eye,
        })


class AnalyticsViewSet(viewsets.ViewSet):
    # FIX: Restricted to medical staff
    permission_classes = [IsMedicalStaff]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        doctor_id = request.query_params.get('doctor_id')
        data = DoctorAnalytics.get_dashboard_data(doctor_id)
        return Response(data)

    @action(detail=False, methods=['get'])
    def patients(self, request):
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
        # FIX: Validate all params BEFORE parsing dates to prevent TypeError crash
        doctor_id = request.query_params.get('doctor_id')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not all([doctor_id, start_date_str, end_date_str]):
            return Response(
                {'error': 'Необходимы параметры: doctor_id, start_date, end_date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return Response(
                {'error': 'Некорректный формат даты. Используйте ISO 8601 (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = DoctorAnalytics.generate_surgeon_report(doctor_id, start_date, end_date)
        return Response(data)

    @action(detail=False, methods=['get'])
    def iol_statistics(self, request):
        data = DoctorAnalytics.get_iol_statistics()
        return Response(data)


class MediaFileViewSet(viewsets.ModelViewSet):
    # FIX: Only medical staff
    permission_classes = [IsMedicalStaff]
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileDetailSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return MediaFileSerializer
        return MediaFileDetailSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
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
        # FIX: Only surgeons/admins should be able to verify documents
        if request.user.role not in ('surgeon', 'admin'):
            return Response(
                {'error': 'Только хирурги и администраторы могут верифицировать документы'},
                status=status.HTTP_403_FORBIDDEN
            )
        media_file = self.get_object()
        media_file.is_verified = True
        media_file.verified_by = request.user
        media_file.verified_at = timezone.now()
        media_file.save()
        return Response({'status': 'verified'})

    @action(detail=False, methods=['get'])
    def patient_files(self, request):
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'Необходим параметр patient_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        files = self.queryset.filter(patient_id=patient_id)
        serializer = self.get_serializer(files, many=True)
        return Response(serializer.data)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email и пароль обязательны'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return Response({'message': 'Logged in', 'role': user.role})
        return Response({'error': 'Неверный email или пароль'}, status=status.HTTP_401_UNAUTHORIZED)


# FIX: Renamed CSFView -> CSRFView; fixed typo in response message; added AllowAny
@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'message': 'CSRF cookie set'})
