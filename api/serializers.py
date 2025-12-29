from rest_framework import serializers
from .models import Disease, Symptom, Prescription, ContactMessage


class SymptomSerializer(serializers.ModelSerializer):
    """Serializer for disease symptoms."""
    
    class Meta:
        model = Symptom
        fields = ['id', 'text', 'order']


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer for disease prescriptions/treatments."""
    
    class Meta:
        model = Prescription
        fields = ['id', 'text', 'order']


class DiseaseSerializer(serializers.ModelSerializer):
    """Serializer for disease information with related data."""
    symptoms = serializers.SerializerMethodField()
    treatment = serializers.SerializerMethodField()
    prevention_tips = serializers.SerializerMethodField()

    class Meta:
        model = Disease
        fields = [
            'id', 
            'name', 
            'description', 
            'category', 
            'symptoms', 
            'treatment', 
            'prevention_tips'
        ]

    def get_symptoms(self, obj):
        """Get ordered list of symptom texts."""
        return [s.text for s in obj.symptom_set.all()[:10]]

    def get_treatment(self, obj):
        """Get ordered list of treatment/prescription texts."""
        return [p.text for p in obj.prescription_set.all()[:10]]

    def get_prevention_tips(self, obj):
        """Get prevention tips as a list."""
        if not obj.prevention_tips:
            return []
        
        # Split by newline and filter empty lines
        tips = [tip.strip() for tip in obj.prevention_tips.split('\n')]
        return [tip for tip in tips if tip]


class DiseaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for disease lists (no related data)."""
    
    class Meta:
        model = Disease
        fields = ['id', 'name', 'category', 'description']


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions."""
    
    class Meta:
        model = ContactMessage
        fields = [
            'id', 
            'name', 
            'email', 
            'phone', 
            'subject', 
            'message', 
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_email(self, value):
        """Ensure email is valid."""
        if not value or '@' not in value:
            raise serializers.ValidationError("Valid email address required")
        return value.lower()
    
    def validate_message(self, value):
        """Ensure message is not empty."""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Message must be at least 10 characters"
            )
        return value.strip()