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
        # Look ONLY at the linked unique symptoms
        qs = obj.symptom_set.all()
        return [s.text for s in qs]

    def get_treatment(self, obj):
        # Look ONLY at the linked unique prescriptions
        qs = obj.prescription_set.all()
        return [p.text for p in qs]

    def get_preventionTips(self, obj):
        return [s for s in obj.prevention_tips.splitlines() if s.strip()]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
