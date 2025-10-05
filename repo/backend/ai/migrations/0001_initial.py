# Generated migration file for ai app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('contentmgmt', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(max_length=100)),
                ('prompt_tokens', models.IntegerField()),
                ('completion_tokens', models.IntegerField()),
                ('total_tokens', models.IntegerField()),
                ('estimated_cost', models.DecimalField(decimal_places=6, max_digits=10)),
                ('request_duration', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('success', models.BooleanField(default=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('content', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to='contentmgmt.content')),
                ('organization', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to='accounts.organization')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to=settings.AUTH_USER_MODEL)),
                ('workspace', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_logs', to='accounts.workspace')),
            ],
            options={
                'db_table': 'usage_logs',
            },
        ),
        migrations.CreateModel(
            name='UsageLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scope', models.CharField(choices=[('user', 'User'), ('workspace', 'Workspace'), ('organization', 'Organization')], max_length=20)),
                ('scope_id', models.IntegerField()),
                ('requests_limit', models.IntegerField(blank=True, null=True)),
                ('tokens_limit', models.IntegerField(blank=True, null=True)),
                ('cost_limit', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('period', models.CharField(choices=[('monthly', 'Monthly'), ('daily', 'Daily')], default='monthly', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'usage_limits',
                'unique_together': {('scope', 'scope_id')},
            },
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['user', '-timestamp'], name='usage_logs_user_id_3f8a21_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['workspace', '-timestamp'], name='usage_logs_workspa_4f7b29_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['organization', '-timestamp'], name='usage_logs_organiz_2a9c88_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['-timestamp'], name='usage_logs_timesta_8b3e42_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['model'], name='usage_logs_model_9c8e41_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelimit',
            index=models.Index(fields=['scope', 'scope_id'], name='usage_limi_scope_7d9f32_idx'),
        ),
    ]
