import os
import tempfile
import logging
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

# --- AUTHENTICATION ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key, 
        'username': user.username
    })


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
    try:
        request.user.auth_token.delete()
    except Exception as e:
        logger.error(f"Logout error: {e}")
    
    return Response({'message': 'Logged out successfully'})


# --- CORE API ---
@api_view(['GET'])
def diseases_list(request):
    """Get list of diseases with optional filtering."""
    category = request.query_params.get('category', None)
    search = request.query_params.get('search', None)
    
    diseases = Disease.objects.all()
    
    if category:
        diseases = diseases.filter(category__icontains=category)
    
    if search:
        diseases = diseases.filter(name__icontains=search)
    
    # Limit to 100 for performance
    diseases = diseases[:100]
    
    serializer = DiseaseSerializer(diseases, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def disease_detail(request, pk):
    """Get detailed information about a specific disease."""
    try:
        disease = Disease.objects.get(pk=pk)
        serializer = DiseaseSerializer(disease)
        return Response(serializer.data)
    except Disease.DoesNotExist:
        return Response(
            {'error': 'Disease not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def disease_options(request, pk):
    """Get treatment options for a disease."""
    try:
        disease = Disease.objects.get(pk=pk)
        
        # Get prescriptions from database
        treatments = list(disease.prescription_set.values_list('text', flat=True))
        
        if not treatments:
            treatments = [
                'Chemical control with appropriate fungicides',
                'Biological control using beneficial organisms',
                'Cultural practices and preventative measures'
            ]
        
        return Response({'options': treatments})
    except Disease.DoesNotExist:
        return Response(
            {'error': 'Disease not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
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

        disease = Disease.objects.prefetch_related(
            "symptom_set", "prescription_set"
        ).get(id=result["disease_id"])

        symptoms = list(disease.symptom_set.values_list("text", flat=True))
        treatments = list(disease.prescription_set.values_list("text", flat=True))

        random.shuffle(symptoms)
        random.shuffle(treatments)

        response = {
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
            "symptoms": symptoms[: random.randint(3, 6)],
            "treatment": treatments[: random.randint(3, 6)],
            "preventionTips": disease.prevention_tips.split("\n")[:5],
            "metrics": {
                "green": result["green_ratio"],
                "discolor": result["discolor_ratio"],
                "edges": result["edge_ratio"],
            },
        }

        return Response(response)

    finally:
        os.remove(path)

@api_view(['POST'])
def chat_view(request):
    """Handle chat messages (placeholder for future AI integration)."""
    user_msg = request.data.get('message', '')
    
    if not user_msg:
        return Response(
            {'error': 'Message is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Integrate with actual AI/NLP service
    return Response({
        'reply': f"Thank you for your message. Our system is analyzing: '{user_msg[:50]}...' "
                 f"This feature will provide detailed crop disease insights soon."
    })


@api_view(['POST'])
def contact_view(request):
    """Handle contact form submissions."""
    serializer = ContactMessageSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': 'Contact message received successfully',
                'data': serializer.data
            }, 
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)