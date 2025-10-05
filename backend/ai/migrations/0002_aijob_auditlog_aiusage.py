# Generated migration for Prompt 3 implementation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0001_initial'),
        ('contentmgmt', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AiJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('kind', models.CharField(max_length=20)),
                ('params', models.JSONField(default=dict)),
                ('result_data', models.JSONField(blank=True, default=dict, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_jobs', to='contentmgmt.content')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_jobs', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_jobs', to='accounts.workspace')),
            ],
            options={
                'db_table': 'ai_jobs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='usagelog',
            name='ai_job',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to='ai.aijob'),
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('created', 'Created'), ('updated', 'Updated'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('deleted', 'Deleted'), ('status_changed', 'Status Changed')], max_length=20)),
                ('old_status', models.CharField(blank=True, max_length=20, null=True)),
                ('new_status', models.CharField(blank=True, max_length=20, null=True)),
                ('changes', models.JSONField(blank=True, default=dict)),
                ('notes', models.TextField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='contentmgmt.content')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='AiUsage',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'AI Usage',
                'verbose_name_plural': 'AI Usage',
            },
            bases=('ai.usagelog',),
        ),
        migrations.AddIndex(
            model_name='aijob',
            index=models.Index(fields=['content'], name='ai_jobs_content_idx'),
        ),
        migrations.AddIndex(
            model_name='aijob',
            index=models.Index(fields=['user'], name='ai_jobs_user_idx'),
        ),
        migrations.AddIndex(
            model_name='aijob',
            index=models.Index(fields=['workspace'], name='ai_jobs_workspace_idx'),
        ),
        migrations.AddIndex(
            model_name='aijob',
            index=models.Index(fields=['status'], name='ai_jobs_status_idx'),
        ),
        migrations.AddIndex(
            model_name='aijob',
            index=models.Index(fields=['-created_at'], name='ai_jobs_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['content'], name='audit_logs_content_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user'], name='audit_logs_user_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action'], name='audit_logs_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-timestamp'], name='audit_logs_timestamp_idx'),
        ),
    ]
