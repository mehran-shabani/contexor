# Generated migration for Prompt 3 implementation

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contentmgmt', '0001_initial'),
        ('ai', '0002_aijob_auditlog_aiusage'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField()),
                ('title', models.CharField(max_length=500)),
                ('body_markdown', models.TextField(help_text='Content body in Markdown format with RTL support')),
                ('metadata', models.JSONField(default=dict, help_text='Additional metadata like meta description, keywords, etc.')),
                ('word_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ai_job', models.ForeignKey(blank=True, help_text='AI job that created this version', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_versions', to='ai.aijob')),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='contentmgmt.content')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_content_versions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'content_versions',
                'ordering': ['-version_number'],
            },
        ),
        migrations.AlterField(
            model_name='version',
            name='content',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legacy_versions', to='contentmgmt.content'),
        ),
        migrations.AlterField(
            model_name='version',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_legacy_versions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='content',
            name='current_version',
            field=models.ForeignKey(blank=True, help_text='Current active version of this content', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_for_content', to='contentmgmt.contentversion'),
        ),
        migrations.AddIndex(
            model_name='contentversion',
            index=models.Index(fields=['content', '-version_number'], name='content_versions_content_version_idx'),
        ),
        migrations.AddIndex(
            model_name='contentversion',
            index=models.Index(fields=['ai_job'], name='content_versions_ai_job_idx'),
        ),
        migrations.AddIndex(
            model_name='contentversion',
            index=models.Index(fields=['-created_at'], name='content_versions_created_at_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='contentversion',
            unique_together={('content', 'version_number')},
        ),
    ]
