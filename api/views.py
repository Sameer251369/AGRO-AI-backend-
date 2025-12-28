import os
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Disease, ContactMessage, SymptomTemplate, PrescriptionTemplate
from .serializers import DiseaseSerializer, ContactMessageSerializer
from . import classifier
import random
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes


@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'username taken'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, email=email, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'id': user.id, 'username': user.username, 'email': user.email, 'token': token.key})


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'id': user.id, 'username': user.username, 'email': user.email, 'token': token.key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # delete user's token
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({'id': user.id, 'username': user.username, 'email': user.email})


@api_view(['GET'])
def diseases_list(request):
    qs = Disease.objects.all().prefetch_related('symptom_set', 'prescription_set')[:2000]
    serializer = DiseaseSerializer(qs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def disease_detail(request, pk):
    try:
        disease = Disease.objects.prefetch_related('symptom_set', 'prescription_set').get(pk=pk)
    except Disease.DoesNotExist:
        return Response({"error": "Disease not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = DiseaseSerializer(disease)
    return Response(serializer.data) 
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def predict(request):
    # Expect an image file under 'image'
    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

    image = request.FILES['image']
    # Save temporarily
    temp_dir = getattr(settings, 'MEDIA_ROOT', '/tmp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, image.name)
    with open(temp_path, 'wb') as f:
        for chunk in image.chunks():
            f.write(chunk)

    try:
        result = classifier.classify_image(temp_path)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Map disease id to DB entry if present
    disease_obj = None
    if result.get('disease_id'):
        try:
            disease_obj = Disease.objects.get(pk=result['disease_id'])
        except Disease.DoesNotExist:
            disease_obj = None

    response = {
        'is_plant': result.get('is_plant', True),
        'is_healthy': result.get('is_healthy', False),
        'confidence': result.get('confidence', 0.0),
        'disease': None,
        'summary': result.get('summary', ''),
        'severity': result.get('severity', ''),
    }

    if disease_obj:
        # sample symptoms/treatment from global template pools so responses vary per request
        symptom_templates = list(SymptomTemplate.objects.values_list('text', flat=True))
        pres_templates = list(PrescriptionTemplate.objects.values_list('text', flat=True))

        if symptom_templates:
            n_sym = min(10, len(symptom_templates))
            sampled_symptoms = random.sample(symptom_templates, n_sym)
        else:
            sampled_symptoms = [s.text for s in disease_obj.symptom_set.all()] if disease_obj.symptom_set.exists() else [s for s in disease_obj.symptoms.splitlines() if s.strip()]

        if pres_templates:
            n_pres = min(10, len(pres_templates))
            sampled_treatment = random.sample(pres_templates, n_pres)
        else:
            sampled_treatment = [p.text for p in disease_obj.prescription_set.all()] if disease_obj.prescription_set.exists() else [s for s in disease_obj.treatment.splitlines() if s.strip()]

        response['disease'] = {
            'id': disease_obj.id,
            'name': disease_obj.name,
            'description': disease_obj.description,
            'category': disease_obj.category,
            'symptoms': sampled_symptoms,
            'treatment': sampled_treatment,
            'preventionTips': [s for s in disease_obj.prevention_tips.splitlines() if s.strip()],
        }
    elif result.get('disease_id') and not response['is_healthy']:
        # If the disease id doesn't exist in DB, return a minimal structure with placeholders
        response['disease'] = {
            'id': result['disease_id'],
            'name': f'Disease {result["disease_id"]}',
            'description': '',
            'category': '',
            'symptoms': [],
            'treatment': [],
            'preventionTips': [],
        }

    return Response(response)


@api_view(['POST'])
def contact_view(request):
    """Accepts contact form submissions and stores them in the DB.

    Expected JSON: { name, email, phone, subject, message }
    Returns 201 with stored data on success.
    """
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save()
        # Optionally: send email/notifications here
        return Response(ContactMessageSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def disease_options(request, pk):
    """Return random symptom/prescription options drawn from the template pools.

    Query params:
      count: number of items to return for each list (default 2000, max 2000)
    """
    try:
        count = int(request.GET.get('count', 2000))
    except Exception:
        count = 2000
    count = max(1, min(2000, count))

    # Fetch random samples from template pools
    symptom_qs = SymptomTemplate.objects.all().values_list('text', flat=True)
    pres_qs = PrescriptionTemplate.objects.all().values_list('text', flat=True)

    import random
    symptom_list = list(symptom_qs)
    pres_list = list(pres_qs)

    random_symptoms = random.sample(symptom_list, min(len(symptom_list), count)) if symptom_list else []
    random_prescriptions = random.sample(pres_list, min(len(pres_list), count)) if pres_list else []

    return Response({'symptoms': random_symptoms, 'treatment': random_prescriptions})


@api_view(['POST'])
def chat_view(request):
    """Simple rule-based Hindi chatbot for demo purposes.

    Expects JSON: { message: "..." }
    Returns: { reply: "..." }
    """
    data = request.data or {}
    msg = (data.get('message') or '').strip()
    if not msg:
        return Response({'reply': 'कृपया एक प्रश्न लिखें।'}, status=status.HTTP_400_BAD_REQUEST)

    # Basic keyword-based responses in Hindi
    m = msg.lower()
    if 'नमस्ते' in m or 'हैलो' in m or 'hello' in m:
        reply = 'नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ? आप किस फसल के बारे में पूछना चाहेंगे?'
    elif 'पानी' in m or 'सिंचाई' in m or 'overwater' in m:
        reply = 'सिंचाई: सामान्यतः सुबह जल्दी या शाम को करें और पत्ती पर पानी गिरने से बचें। मिट्टी की नमी पर आधारित सिंचाई करें।'
    elif 'खरपतवार' in m or 'weed' in m:
        reply = 'खरपतवार नियंत्रण: रूपांतर से पहले मैन्युअल हटाना और बाद में मल्च का उपयोग उपयोगी होता है।'
    elif 'कीट' in m or 'insect' in m or 'pest' in m:
        reply = 'कीट नियंत्रण: पहले पहचान करें, फिर लक्ष्यगत कीटनाशक का प्रयोग करें। जैविक विकल्प: नीम तेल या बायो-कंट्रोल एजेंट।'
    elif 'बीमार' in m or 'रोग' in m or 'disease' in m:
        reply = 'यदि पत्तियों पर दाग़ दिख रहे हैं, तो प्रभावित हिस्सों को हटाएँ और आवश्यक होने पर प्रमाणित फफूंदनाशक का प्रयोग करें। तस्वीर भेजें तो और बेहतर सलाह दी जा सकेगी।'
    else:
        reply = 'मुझे आपका प्रश्न समझ में नहीं आया। कृपया हिंदी में फसल/लक्षण/इलाज के बारे में स्पष्ट प्रश्न पूछें।'

    return Response({'reply': reply})
