# Generated for user stories: alerts, sessions, motivation.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RehabWeb_API', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MotivationProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_points', models.PositiveIntegerField(default=0)),
                ('current_streak', models.PositiveIntegerField(default=0)),
                ('best_streak', models.PositiveIntegerField(default=0)),
                ('last_session_date', models.DateField(blank=True, null=True)),
                ('leaderboard_opt_in', models.BooleanField(default=False)),
                ('leaderboard_consented_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='motivacion', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ExerciseSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('performed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('scheduled_for', models.DateField(blank=True, null=True)),
                ('exercise_name', models.CharField(default='Sesion de rehabilitacion', max_length=140)),
                ('repetitions_completed', models.PositiveIntegerField(default=0)),
                ('planned_repetitions', models.PositiveIntegerField(default=0)),
                ('duration_seconds', models.PositiveIntegerField(default=0)),
                ('pain_level', models.PositiveSmallIntegerField(default=0)),
                ('mobility_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('points_awarded', models.PositiveIntegerField(default=0)),
                ('speed_bonus_points', models.PositiveIntegerField(default=0)),
                ('streak_days', models.PositiveIntegerField(default=0)),
                ('positive_feedback', models.CharField(blank=True, max_length=180)),
                ('performance_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sesiones_rehabilitacion', to=settings.AUTH_USER_MODEL)),
                ('terapeuta', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sesiones_supervisadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-performed_at'],
            },
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(choices=[('INACTIVITY_WARNING', 'Inactividad'), ('PAIN_OR_DETERIORATION', 'Dolor o deterioro')], max_length=40)),
                ('severity', models.CharField(choices=[('warning', 'Advertencia'), ('critical', 'Critica')], default='warning', max_length=20)),
                ('title', models.CharField(max_length=160)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('activa', 'Activa'), ('revisada', 'Revisada'), ('resuelta', 'Resuelta')], default='activa', max_length=20)),
                ('detected_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_como_paciente', to=settings.AUTH_USER_MODEL)),
                ('source_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_alerts', to='RehabWeb_API.exercisesession')),
                ('terapeuta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas_como_terapeuta', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-detected_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientBadge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=60)),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(max_length=240)),
                ('awarded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('source_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='badges_awarded', to='RehabWeb_API.exercisesession')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='insignias', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-awarded_at'],
                'unique_together': {('usuario', 'code')},
            },
        ),
        migrations.CreateModel(
            name='WeeklySummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField()),
                ('week_end', models.DateField()),
                ('sessions_completed', models.PositiveIntegerField(default=0)),
                ('sessions_scheduled', models.PositiveIntegerField(default=0)),
                ('points_obtained', models.PositiveIntegerField(default=0)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resumenes_semanales', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-week_start'],
                'unique_together': {('paciente', 'week_start')},
            },
        ),
    ]
