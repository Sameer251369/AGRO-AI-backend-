import os
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

# --- AUTHENTICATION ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, email=email, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': {'id': user.id, 'username': user.username}})

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'username': user.username})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({'id': request.user.id, 'username': request.user.username, 'email': request.user.email})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})

# --- CORE API ---
@api_view(['GET'])
def diseases_list(request):
    # Performance: Only load first 100 for broad list
    diseases = Disease.objects.all()[:100] 
    serializer = DiseaseSerializer(diseases, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def disease_detail(request, pk):
    try:
        disease = Disease.objects.get(pk=pk)
        return Response(DiseaseSerializer(disease).data)
    except Disease.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def disease_options(request, pk):
    return Response({'options': ['Chemical control', 'Biological control', 'Preventative measures']})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def predict(request):
    file = request.FILES.get('image')
    if not file:
        return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
    prediction_name = classifier.predict_image(file)
    disease = Disease.objects.filter(name__icontains=prediction_name).first()
    return Response({
        'prediction': prediction_name,
        'details': DiseaseSerializer(disease).data if disease else "No detailed data found."
    })

@api_view(['POST'])
def chat_view(request):
    user_msg = request.data.get('message', '')
    return Response({'reply': f"AI received: {user_msg}. Analyzing your crop query..."})

@api_view(['POST'])
def contact_view(request):
    serializer = ContactMessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)