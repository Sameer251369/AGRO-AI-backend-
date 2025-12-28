from rest_framework import serializers
from .models import Disease, Symptom, Prescription
from .models import ContactMessage


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ['id', 'text', 'order']


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ['id', 'text', 'order']


class DiseaseSerializer(serializers.ModelSerializer):
    symptoms = serializers.SerializerMethodField()
    treatment = serializers.SerializerMethodField()
    preventionTips = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = ['id', 'name', 'description', 'category', 'symptoms', 'treatment', 'preventionTips']

    def get_symptoms(self, obj):
        # Prefer related Symptom objects if present, otherwise fall back to text field
        qs = obj.symptom_set.all()
        if qs.exists():
            return [s.text for s in qs]
        return [s for s in obj.symptoms.splitlines() if s.strip()]

    def get_treatment(self, obj):
        qs = obj.prescription_set.all()
        if qs.exists():
            return [p.text for p in qs]
        return [s for s in obj.treatment.splitlines() if s.strip()]

    def get_preventionTips(self, obj):
        return [s for s in obj.prevention_tips.splitlines() if s.strip()]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
