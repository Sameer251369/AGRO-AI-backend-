import os
import random
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated

from .models import Disease, ContactMessage, SymptomTemplate, PrescriptionTemplate
from .serializers import DiseaseSerializer, ContactMessageSerializer
from . import classifier

# --- AUTH VIEWS ---

@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'id': user.id, 
        'username': user.username, 
        'email': user.email, 
        'token': token.key
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'id': user.id, 
        'username': user.username, 
        'email': user.email, 
        'token': token.key
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'status': 'ok'})

# --- DISEASE & PREDICTION VIEWS ---

@api_view(['GET'])
def diseases_list(request):
    # Performance Fix: Prefetching related symptoms and prescriptions
    qs = Disease.objects.prefetch_related('symptom_set', 'prescription_set').all()[:2000]
    serializer = DiseaseSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def disease_detail(request, pk):
    try:
        # Performance Fix: Prefetching for single detail view
        disease = Disease.objects.prefetch_related('symptom_set', 'prescription_set').get(pk=pk)
    except Disease.DoesNotExist:
        return Response({"error": "Disease not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = DiseaseSerializer(disease)
    return Response(serializer.data)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def predict(request):
    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']
    temp_dir = getattr(settings, 'MEDIA_ROOT', '/tmp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate unique filename to avoid collisions
    temp_path = os.path.join(temp_dir, f"{random.randint(1000, 9999)}_{image.name}")

    try:
        # Save image
        with open(temp_path, 'wb') as f:
            for chunk in image.chunks():
                f.write(chunk)

        # Run classification
        result = classifier.classify_image(temp_path)
        
        # Performance Fix: Prefetching here to avoid N+1 queries during response build
        disease_obj = None
        if result.get('disease_id'):
            disease_obj = Disease.objects.prefetch_related('symptom_set', 'prescription_set').filter(pk=result['disease_id']).first()

        response_data = {
            'is_plant': result.get('is_plant', True),
            'is_healthy': result.get('is_healthy', False),
            'confidence': result.get('confidence', 0.0),
            'disease': None,
            'summary': result.get('summary', ''),
            'severity': result.get('severity', ''),
        }

        if disease_obj:
            # Efficient sampling
            symptom_templates = list(SymptomTemplate.objects.values_list('text', flat=True))
            pres_templates = list(PrescriptionTemplate.objects.values_list('text', flat=True))

            if symptom_templates:
                sampled_symptoms = random.sample(symptom_templates, min(10, len(symptom_templates)))
            else:
                sampled_symptoms = [s.text for s in disease_obj.symptom_set.all()] or (disease_obj.symptoms or "").splitlines()

            if pres_templates:
                sampled_treatment = random.sample(pres_templates, min(10, len(pres_templates)))
            else:
                sampled_treatment = [p.text for p in disease_obj.prescription_set.all()] or (disease_obj.treatment or "").splitlines()

            response_data['disease'] = {
                'id': disease_obj.id,
                'name': disease_obj.name,
                'description': disease_obj.description,
                'category': disease_obj.category,
                'symptoms': [s.strip() for s in sampled_symptoms if s.strip()],
                'treatment': [t.strip() for t in sampled_treatment if t.strip()],
                'preventionTips': [p.strip() for p in (disease_obj.prevention_tips or "").splitlines() if p.strip()],
            }
        
        return Response(response_data)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    finally:
        # Safety Fix: Clean up temporary file to prevent disk fill-up
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- UTILITY VIEWS ---

@api_view(['POST'])
def contact_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def disease_options(request):
    try:
        count = int(request.GET.get('count', 10))
    except ValueError:
        count = 10
    
    # Efficiency Fix: Database-level random sampling
    random_symptoms = SymptomTemplate.objects.order_by('?')[:count].values_list('text', flat=True)
    random_prescriptions = PrescriptionTemplate.objects.order_by('?')[:count].values_list('text', flat=True)

    return Response({
        'symptoms': list(random_symptoms), 
        'treatment': list(random_prescriptions)
    })

@api_view(['POST'])
def chat_view(request):
    msg = (request.data.get('message') or '').strip().lower()
    if not msg:
        return Response({'reply': 'कृपया एक प्रश्न लिखें।'}, status=status.HTTP_400_BAD_REQUEST)

    if any(k in msg for k in ['नमस्ते', 'हैलो', 'hello']):
        reply = 'नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?'
    elif any(k in msg for k in ['पानी', 'सिंचाई']):
        reply = 'सिंचाई सामान्यतः सुबह या शाम को करें। मिट्टी की नमी चेक करें।'
    elif any(k in msg for k in ['कीट', 'insect']):
        reply = 'कीट नियंत्रण के लिए नीम तेल का प्रयोग करें या प्रभावित हिस्से को हटा दें।'
    else:
        reply = 'मुझे आपका प्रश्न समझ में नहीं आया। कृपया स्पष्ट प्रश्न पूछें।'

    return Response({'reply': reply})