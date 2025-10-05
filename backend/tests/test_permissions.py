"""
Unit tests for permissions.
"""
from django.test import TestCase, RequestFactory
from unittest.mock import Mock

from accounts.models import User, Organization, OrganizationMember, Workspace
from accounts.permissions import (
    IsOrganizationAdmin, IsOrganizationMember,
    CanEditContent, CanCreateContent, CanApproveContent
)
from contentmgmt.models import Project, Content


class PermissionsTestCase(TestCase):
    """Test cases for custom permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create users
        self.admin_user = User.objects.create_user(phone_number='+989121111111')
        self.editor_user = User.objects.create_user(phone_number='+989122222222')
        self.writer_user = User.objects.create_user(phone_number='+989123333333')
        self.viewer_user = User.objects.create_user(phone_number='+989124444444')
        self.non_member = User.objects.create_user(phone_number='+989125555555')
        
        # Create organization
        self.org = Organization.objects.create(
            name='Test Org',
            slug='test-org'
        )
        
        # Create memberships
        OrganizationMember.objects.create(
            user=self.admin_user,
            organization=self.org,
            role=OrganizationMember.Role.ADMIN
        )
        OrganizationMember.objects.create(
            user=self.editor_user,
            organization=self.org,
            role=OrganizationMember.Role.EDITOR
        )
        OrganizationMember.objects.create(
            user=self.writer_user,
            organization=self.org,
            role=OrganizationMember.Role.WRITER
        )
        OrganizationMember.objects.create(
            user=self.viewer_user,
            organization=self.org,
            role=OrganizationMember.Role.VIEWER
        )
        
        # Create workspace and project
        self.workspace = Workspace.objects.create(
            name='Test Workspace',
            slug='test-workspace',
            organization=self.org
        )
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project',
            workspace=self.workspace,
            created_by=self.admin_user
        )
        
        # Create content
        self.content = Content.objects.create(
            title='Test Content',
            project=self.project,
            created_by=self.writer_user,
            status=Content.Status.DRAFT
        )
    
    def test_is_organization_admin(self):
        """Test IsOrganizationAdmin permission."""
        permission = IsOrganizationAdmin()
        view = Mock()
        
        # Admin should have permission
        request = self.factory.get('/')
        request.user = self.admin_user
        self.assertTrue(permission.has_object_permission(request, view, self.org))
        
        # Non-admin should not have permission
        request.user = self.editor_user
        self.assertFalse(permission.has_object_permission(request, view, self.org))
        
        # Non-member should not have permission
        request.user = self.non_member
        self.assertFalse(permission.has_object_permission(request, view, self.org))
    
    def test_is_organization_member(self):
        """Test IsOrganizationMember permission."""
        permission = IsOrganizationMember()
        view = Mock()
        
        # All members should have permission
        request = self.factory.get('/')
        for user in [self.admin_user, self.editor_user, self.writer_user, self.viewer_user]:
            request.user = user
            self.assertTrue(permission.has_object_permission(request, view, self.org))
        
        # Non-member should not have permission
        request.user = self.non_member
        self.assertFalse(permission.has_object_permission(request, view, self.org))
    
    def test_can_edit_content_safe_methods(self):
        """Test CanEditContent permission for safe methods (GET, etc)."""
        permission = CanEditContent()
        view = Mock()
        
        # All members can view (safe methods)
        request = self.factory.get('/')
        for user in [self.admin_user, self.editor_user, self.writer_user, self.viewer_user]:
            request.user = user
            self.assertTrue(permission.has_object_permission(request, view, self.content))
    
    def test_can_edit_content_unsafe_methods(self):
        """Test CanEditContent permission for unsafe methods (POST, PUT, etc)."""
        permission = CanEditContent()
        view = Mock()
        
        # Admin and Editor can edit
        request = self.factory.post('/')
        for user in [self.admin_user, self.editor_user]:
            request.user = user
            self.assertTrue(permission.has_object_permission(request, view, self.content))
        
        # Writer and Viewer cannot edit
        for user in [self.writer_user, self.viewer_user]:
            request.user = user
            self.assertFalse(permission.has_object_permission(request, view, self.content))
        
        # Non-member cannot edit
        request.user = self.non_member
        self.assertFalse(permission.has_object_permission(request, view, self.content))
    
    def test_can_create_content(self):
        """Test CanCreateContent permission."""
        permission = CanCreateContent()
        view = Mock()
        
        # Admin, Editor, and Writer can create
        request = self.factory.post('/')
        for user in [self.admin_user, self.editor_user, self.writer_user]:
            request.user = user
            self.assertTrue(permission.has_object_permission(request, view, self.content))
        
        # Viewer cannot create
        request.user = self.viewer_user
        self.assertFalse(permission.has_object_permission(request, view, self.content))
        
        # Non-member cannot create
        request.user = self.non_member
        self.assertFalse(permission.has_object_permission(request, view, self.content))
    
    def test_can_approve_content(self):
        """Test CanApproveContent permission."""
        permission = CanApproveContent()
        view = Mock()
        
        # Admin and Editor can approve
        request = self.factory.post('/')
        for user in [self.admin_user, self.editor_user]:
            request.user = user
            self.assertTrue(permission.has_object_permission(request, view, self.content))
        
        # Writer and Viewer cannot approve
        for user in [self.writer_user, self.viewer_user]:
            request.user = user
            self.assertFalse(permission.has_object_permission(request, view, self.content))
        
        # Non-member cannot approve
        request.user = self.non_member
        self.assertFalse(permission.has_object_permission(request, view, self.content))
    
    def test_permission_with_workspace_object(self):
        """Test permission checking with workspace object."""
        permission = IsOrganizationMember()
        view = Mock()
        
        request = self.factory.get('/')
        request.user = self.admin_user
        
        # Should work with workspace object
        self.assertTrue(permission.has_object_permission(request, view, self.workspace))
    
    def test_permission_with_project_object(self):
        """Test permission checking with project object."""
        permission = IsOrganizationMember()
        view = Mock()
        
        request = self.factory.get('/')
        request.user = self.admin_user
        
        # Should work with project object
        self.assertTrue(permission.has_object_permission(request, view, self.project))
