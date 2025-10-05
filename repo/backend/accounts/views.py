"""
Views for accounts app.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, Organization, OrganizationMember, Workspace
from .serializers import (
    OTPRequestSerializer, OTPVerifySerializer,
    UserSerializer, OrganizationSerializer,
    OrganizationMemberSerializer, WorkspaceSerializer
)
from .services.otp import OTPService


@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    """
    Request OTP code for phone number.
    
    POST /api/auth/otp/request
    Body: {"phone_number": "+989123456789"}
    """
    serializer = OTPRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone_number = serializer.validated_data['phone_number']
    
    success, message, ttl = OTPService.issue_otp(phone_number)
    
    if success:
        return Response({
            'success': True,
            'message': message,
            'ttl': ttl
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': message,
            'retry_after': ttl
        }, status=status.HTTP_429_TOO_MANY_REQUESTS if ttl else status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP code and get JWT tokens.
    
    POST /api/auth/otp/verify
    Body: {"phone_number": "+989123456789", "code": "123456"}
    """
    serializer = OTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    phone_number = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']
    
    success, message, token_data = OTPService.verify_otp(phone_number, code)
    
    if success:
        return Response({
            'success': True,
            'message': message,
            **token_data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user.
    
    GET /api/auth/me
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization CRUD."""
    
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']


class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationMember CRUD."""
    
    queryset = OrganizationMember.objects.select_related('user', 'organization')
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['organization', 'role']
    search_fields = ['user__phone_number', 'user__full_name']
    ordering_fields = ['joined_at']
    ordering = ['-joined_at']


class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for Workspace CRUD."""
    
    queryset = Workspace.objects.select_related('organization')
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['organization', 'is_active']
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
