"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode, Organization, OrganizationMember, Workspace


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for custom User model."""
    
    list_display = ('phone_number', 'full_name', 'email', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('phone_number', 'full_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    """Admin for OTP codes."""
    
    list_display = ('phone_number', 'is_used', 'attempt_count', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('phone_number',)
    readonly_fields = ('code_hash', 'created_at', 'expires_at', 'last_sent_at')
    ordering = ('-created_at',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin for organizations."""
    
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Admin for organization members."""
    
    list_display = ('user', 'organization', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__phone_number', 'organization__name')
    ordering = ('-joined_at',)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    """Admin for workspaces."""
    
    list_display = ('name', 'organization', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'organization')
    search_fields = ('name', 'slug', 'organization__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
