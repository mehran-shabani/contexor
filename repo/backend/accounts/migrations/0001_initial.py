# Generated migration file for accounts app

from django.db import migrations, models
import django.db.models.deletion
from django.contrib.auth.hashers import make_password


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('phone_number', models.CharField(max_length=20, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='OTPCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=20)),
                ('code_hash', models.CharField(max_length=255)),
                ('is_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('attempt_count', models.IntegerField(default=0)),
                ('last_sent_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'otp_codes',
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'organizations',
            },
        ),
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workspaces', to='accounts.organization')),
            ],
            options={
                'db_table': 'workspaces',
                'unique_together': {('organization', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='OrganizationMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('editor', 'Editor'), ('writer', 'Writer'), ('viewer', 'Viewer')], max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='accounts.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_memberships', to='accounts.user')),
            ],
            options={
                'db_table': 'organization_members',
                'unique_together': {('user', 'organization')},
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['phone_number'], name='users_phone_n_2c6e91_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='users_is_acti_b760ab_idx'),
        ),
        migrations.AddIndex(
            model_name='otpcode',
            index=models.Index(fields=['phone_number', '-created_at'], name='otp_codes_phone_n_8c8a31_idx'),
        ),
        migrations.AddIndex(
            model_name='otpcode',
            index=models.Index(fields=['expires_at'], name='otp_codes_expires_8a3b24_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['slug'], name='organizati_slug_2a9c88_idx'),
        ),
        migrations.AddIndex(
            model_name='organization',
            index=models.Index(fields=['is_active'], name='organizati_is_acti_4f7b29_idx'),
        ),
        migrations.AddIndex(
            model_name='workspace',
            index=models.Index(fields=['organization'], name='workspaces_organiz_3f8b21_idx'),
        ),
        migrations.AddIndex(
            model_name='workspace',
            index=models.Index(fields=['is_active'], name='workspaces_is_acti_7c9d32_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(fields=['user', 'organization'], name='organizati_user_id_5a2c93_idx'),
        ),
        migrations.AddIndex(
            model_name='organizationmember',
            index=models.Index(fields=['role'], name='organizati_role_3f8a19_idx'),
        ),
    ]
