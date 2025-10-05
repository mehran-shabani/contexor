# Generated migration file for contentmgmt app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_projects', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='accounts.workspace')),
            ],
            options={
                'db_table': 'projects',
                'unique_together': {('workspace', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('blog', 'Blog Post'), ('social', 'Social Media'), ('ecommerce', 'E-commerce'), ('email', 'Email Marketing'), ('ad', 'Advertisement'), ('other', 'Other')], max_length=50)),
                ('prompt_template', models.TextField()),
                ('variables', models.JSONField(default=list)),
                ('is_public', models.BooleanField(default=False)),
                ('usage_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_prompts', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prompts', to='accounts.workspace')),
            ],
            options={
                'db_table': 'prompts',
            },
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('body', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('in_progress', 'In Progress'), ('review', 'Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='draft', max_length=20)),
                ('prompt_variables', models.JSONField(default=dict)),
                ('word_count', models.IntegerField(default=0)),
                ('has_pii', models.BooleanField(default=False)),
                ('pii_warnings', models.JSONField(default=list)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_contents', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_contents', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='contentmgmt.project')),
                ('prompt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contents', to='contentmgmt.prompt')),
            ],
            options={
                'db_table': 'contents',
            },
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField()),
                ('content_snapshot', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='contentmgmt.content')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_versions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'versions',
                'ordering': ['-version_number'],
                'unique_together': {('content', 'version_number')},
            },
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['workspace'], name='projects_workspa_3f8a21_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['created_by'], name='projects_created_8a2c93_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['is_active'], name='projects_is_acti_7c9d32_idx'),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(fields=['workspace'], name='prompts_workspa_4f7b29_idx'),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(fields=['category'], name='prompts_categor_2a9c88_idx'),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(fields=['is_public'], name='prompts_is_publ_9b3e42_idx'),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(fields=['-usage_count'], name='prompts_usage_c_5c8d72_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['project'], name='contents_project_6d9f83_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['prompt'], name='contents_prompt__7f8a64_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['status'], name='contents_status_3c7e92_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['created_by'], name='contents_created_4b9e73_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['-created_at'], name='contents_created_2f8d61_idx'),
        ),
        migrations.AddIndex(
            model_name='content',
            index=models.Index(fields=['has_pii'], name='contents_has_pii_8e7f52_idx'),
        ),
        migrations.AddIndex(
            model_name='version',
            index=models.Index(fields=['content', '-version_number'], name='versions_content_9c8e41_idx'),
        ),
        migrations.AddIndex(
            model_name='version',
            index=models.Index(fields=['-created_at'], name='versions_created_7d9f32_idx'),
        ),
    ]
