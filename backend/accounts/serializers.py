"""
Serializers for accounts app.
"""
from rest_framework import serializers
from phonenumbers import parse, is_valid_number, NumberParseException
from .models import User, Organization, OrganizationMember, Workspace


class PhoneNumberField(serializers.CharField):
    """Custom field for phone number validation."""
    
    def to_internal_value(self, data):
        try:
            # Parse phone number (assume IR if no country code)
            if not data.startswith('+'):
                data = '+98' + data.lstrip('0')
            
            phone = parse(data, None)
            if not is_valid_number(phone):
                raise serializers.ValidationError('Invalid phone number')
            
            # Return in E164 format
            from phonenumbers import format_number, PhoneNumberFormat
            return format_number(phone, PhoneNumberFormat.E164)
            
        except NumberParseException:
            raise serializers.ValidationError('Invalid phone number format')


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for OTP request."""
    
    phone_number = PhoneNumberField(max_length=20)
    
    def validate_phone_number(self, value):
        """Additional validation for phone number."""
        if not value:
            raise serializers.ValidationError('Phone number is required')
        return value


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    
    phone_number = PhoneNumberField(max_length=20)
    code = serializers.CharField(min_length=6, max_length=6)
    
    def validate_code(self, value):
        """Validate OTP code format."""
        if not value.isdigit():
            raise serializers.ValidationError('OTP code must contain only digits')
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'full_name', 'email', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'phone_number', 'is_active', 'date_joined', 'last_login']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    
    member_count = serializers.SerializerMethodField()
    workspace_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'is_active',
            'created_at', 'updated_at', 'member_count', 'workspace_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_workspace_count(self, obj):
        return obj.workspaces.filter(is_active=True).count()


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMember model."""
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = ['id', 'user', 'user_id', 'organization', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for Workspace model."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    project_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workspace
        fields = [
            'id', 'name', 'slug', 'organization', 'organization_name',
            'description', 'is_active', 'created_at', 'updated_at', 'project_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_project_count(self, obj):
        return obj.projects.filter(is_active=True).count()
