"""
Custom permissions for accounts app.
"""
from rest_framework import permissions
from .models import OrganizationMember


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of the organization.
    """
    
    def has_object_permission(self, request, view, obj):
        # Get organization from object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'workspace'):
            organization = obj.workspace.organization
        elif hasattr(obj, 'project'):
            organization = obj.project.workspace.organization
        else:
            return False
        
        # Check if user is admin
        return OrganizationMember.objects.filter(
            user=request.user,
            organization=organization,
            role=OrganizationMember.Role.ADMIN
        ).exists()


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization.
    """
    
    def has_object_permission(self, request, view, obj):
        # Get organization from object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        elif hasattr(obj, 'workspace'):
            organization = obj.workspace.organization
        elif hasattr(obj, 'project'):
            organization = obj.project.workspace.organization
        else:
            return False
        
        # Check if user is member
        return OrganizationMember.objects.filter(
            user=request.user,
            organization=organization
        ).exists()


class CanEditContent(permissions.BasePermission):
    """
    Permission to check if user can edit content.
    Admins and Editors can edit, Writers and Viewers cannot.
    """
    
    def has_object_permission(self, request, view, obj):
        # GET, HEAD, OPTIONS are allowed for all members
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Get organization from object
        if hasattr(obj, 'project'):
            organization = obj.project.workspace.organization
        else:
            return False
        
        # Check role
        try:
            member = OrganizationMember.objects.get(
                user=request.user,
                organization=organization
            )
            return member.role in [
                OrganizationMember.Role.ADMIN,
                OrganizationMember.Role.EDITOR
            ]
        except OrganizationMember.DoesNotExist:
            return False


class CanCreateContent(permissions.BasePermission):
    """
    Permission to check if user can create content.
    Admins, Editors, and Writers can create.
    """
    
    def has_permission(self, request, view):
        # All authenticated users can create (will check organization membership in view)
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For creation, check if user has write access
        if hasattr(obj, 'project'):
            organization = obj.project.workspace.organization
        else:
            return False
        
        try:
            member = OrganizationMember.objects.get(
                user=request.user,
                organization=organization
            )
            return member.role in [
                OrganizationMember.Role.ADMIN,
                OrganizationMember.Role.EDITOR,
                OrganizationMember.Role.WRITER
            ]
        except OrganizationMember.DoesNotExist:
            return False


class CanApproveContent(permissions.BasePermission):
    """
    Permission to check if user can approve/reject content.
    Only Admins and Editors can approve.
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            organization = obj.project.workspace.organization
        else:
            return False
        
        try:
            member = OrganizationMember.objects.get(
                user=request.user,
                organization=organization
            )
            return member.role in [
                OrganizationMember.Role.ADMIN,
                OrganizationMember.Role.EDITOR
            ]
        except OrganizationMember.DoesNotExist:
            return False
