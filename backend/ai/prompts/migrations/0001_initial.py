# Generated migration for PromptTemplate model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromptTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('kind', models.CharField(choices=[('outline', 'Outline'), ('draft', 'Draft'), ('rewrite', 'Rewrite'), ('caption', 'Caption')], help_text='Type of content generation', max_length=20)),
                ('template_text', models.TextField(help_text='Prompt template with {placeholders}')),
                ('params', models.JSONField(default=dict, help_text='Parameter definitions and defaults')),
                ('version', models.IntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('usage_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_prompt_templates', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(blank=True, help_text='If null, template is global', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prompt_templates', to='accounts.workspace')),
            ],
            options={
                'db_table': 'prompt_templates',
                'ordering': ['-usage_count', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='prompttemplate',
            index=models.Index(fields=['kind'], name='prompt_templates_kind_idx'),
        ),
        migrations.AddIndex(
            model_name='prompttemplate',
            index=models.Index(fields=['workspace'], name='prompt_templates_workspace_idx'),
        ),
        migrations.AddIndex(
            model_name='prompttemplate',
            index=models.Index(fields=['is_active'], name='prompt_templates_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='prompttemplate',
            index=models.Index(fields=['-usage_count'], name='prompt_templates_usage_count_idx'),
        ),
    ]
