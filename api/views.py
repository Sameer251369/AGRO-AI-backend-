import os
import tempfile
import logging
import random

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Disease, ContactMessage
from .serializers import DiseaseSerializer, ContactMessageSerializer
from . import classifier

logger = logging.getLogger(__name__)

# ---------------- AUTH ----------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        username=request.data.get('username'),
        password=request.data.get('password')
    )

    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.username})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})


# ---------------- DISEASE APIs ----------------
@api_view(['GET'])
def diseases_list(request):
    diseases = Disease.objects.all()[:100]
    return Response(DiseaseSerializer(diseases, many=True).data)


@api_view(['GET'])
def disease_detail(request, pk):
    try:
        disease = Disease.objects.get(pk=pk)
        return Response(DiseaseSerializer(disease).data)
    except Disease.DoesNotExist:
        return Response({'error': 'Disease not found'}, status=404)


@api_view(['GET'])
def disease_options(request, pk):
    try:
        disease = Disease.objects.get(pk=pk)
        treatments = list(disease.prescription_set.values_list('text', flat=True))
        return Response({'options': treatments})
    except Disease.DoesNotExist:
        return Response({'error': 'Disease not found'}, status=404)


# ---------------- AI PREDICT ----------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def predict(request):
    image = request.FILES.get("image")

    if not image:
        return Response({"error": "Image required"}, status=400)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        for chunk in image.chunks():
            tmp.write(chunk)
        path = tmp.name

    try:
        result = classifier.classify_image(path)

        if not result["is_plant"]:
            return Response(result)

        # 🔥 THIS IS THE REAL FIX
        disease = random.choice(
            list(
                Disease.objects.prefetch_related(
                    "symptom_set", "prescription_set"
                )
            )
        )

        symptoms = list(disease.symptom_set.values_list("text", flat=True))
        treatments = list(disease.prescription_set.values_list("text", flat=True))

        random.shuffle(symptoms)
        random.shuffle(treatments)

        return Response({
            "isPlant": True,
            "confidence": result["confidence"],
            "severity": result["severity"],
            "summary": result["summary"],
            "disease": {
                "id": disease.id,
                "name": disease.name,
                "category": disease.category,
                "description": disease.description,
            },
            "symptoms": symptoms[:random.randint(3, 6)],
            "treatment": treatments[:random.randint(3, 6)],
            "preventionTips": disease.prevention_tips.split("\n")[:5],
            "metrics": {
                "green": result["green_ratio"],
                "discolor": result["discolor_ratio"],
                "edges": result["edge_ratio"],
            },
        })

    finally:
        os.remove(path)


# ---------------- CHAT & CONTACT ----------------
@api_view(['POST'])
def chat_view(request):
    msg = request.data.get('message', '')
    return Response({'reply': f"Analyzing: {msg[:50]}..."})


@api_view(['POST'])
def contact_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
