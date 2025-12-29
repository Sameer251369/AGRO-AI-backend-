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

    class Meta:
        model = Disease
        fields = ['id', 'name', 'description', 'category', 'symptoms', 'treatment', 'prevention_tips']

    def get_symptoms(self, obj):
        # This calls the unique symptoms we just linked
        return [s.text for s in obj.symptom_set.all()]

    def get_treatment(self, obj):
        # This calls the unique prescriptions (treatments)
        return [p.text for p in obj.prescription_set.all()]

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
