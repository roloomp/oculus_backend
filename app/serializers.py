from rest_framework import serializers
from .models import User, Patient, PreparationTemplate, PatientPreparation, MediaFile, IOLCalculation, SurgeonFeedback
from .file_validators import FileValidator


class UserSerializer(serializers.ModelSerializer):
    # Expose the linked patient UUID so the frontend can navigate directly
    # to the patient's own record without a separate lookup.
    linked_patient_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'middle_name', 'role', 'linked_patient_id')
        read_only_fields = ('id', 'linked_patient_id')


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class PreparationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreparationTemplate
        fields = '__all__'


class PatientPreparationSerializer(serializers.ModelSerializer):
    template_details = PreparationTemplateSerializer(source='template', read_only=True)

    class Meta:
        model = PatientPreparation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class MediaFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = MediaFile
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'file_size', 'file_name', 'file_type',
                            'file_hash', 'uploaded_by')

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_file(self, value):
        validator = FileValidator()
        validation_result = validator.validate(value)

        file_hash = validation_result['hash']
        if MediaFile.objects.filter(file_hash=file_hash).exists():
            raise serializers.ValidationError('Такой файл уже был загружен ранее')

        return value

    def create(self, validated_data):
        file = validated_data.get('file')
        request = self.context.get('request')

        validated_data['file_name'] = file.name
        validated_data['file_size'] = file.size
        validated_data['file_type'] = getattr(file, 'content_type', '')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user

        validator = FileValidator()
        validated_data['file_hash'] = validator.calculate_file_hash(file)

        return super().create(validated_data)


class MediaFileDetailSerializer(MediaFileSerializer):
    # FIX: patient.full_name now exists (added to Patient model)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    preparation_info = serializers.CharField(source='preparation.template.title', read_only=True)


class IOLCalculationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IOLCalculation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class IOLCalculationDetailSerializer(serializers.ModelSerializer):
    calculated_by_name = serializers.CharField(source='calculated_by.full_name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)

    class Meta:
        model = IOLCalculation
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SurgeonFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgeonFeedback
        fields = '__all__'
        read_only_fields = ('id', 'created_at')