import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class PerfilClinico(models.Model):
    NIVEL_MOVILIDAD_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('dependiente', 'Dependiente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    diagnostico_principal = models.CharField(max_length=180)
    historial_medico = models.TextField(blank=True)
    nivel_movilidad = models.CharField(max_length=20, choices=NIVEL_MOVILIDAD_CHOICES, default='medio')
    restricciones = models.TextField(blank=True)

    def __str__(self):
        return self.diagnostico_principal


class TerapeutaProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='perfil_terapeuta',
        on_delete=models.CASCADE,
    )
    especialidad = models.CharField(max_length=120)
    numero_licencia = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} - {self.especialidad}'


class PacienteProfile(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='perfil_paciente',
        on_delete=models.CASCADE,
    )
    terapeuta = models.ForeignKey(
        TerapeutaProfile,
        related_name='pacientes',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    perfil_clinico = models.OneToOneField(
        PerfilClinico,
        related_name='paciente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    estrategia_validacion = models.CharField(max_length=120, default='Libre')
    estrategia_progreso = models.CharField(max_length=120, default='Por rutinas')

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class Alert(models.Model):
    TYPE_INACTIVITY_WARNING = 'INACTIVITY_WARNING'
    TYPE_PAIN_OR_DETERIORATION = 'PAIN_OR_DETERIORATION'

    ALERT_TYPE_CHOICES = [
        (TYPE_INACTIVITY_WARNING, 'Inactividad'),
        (TYPE_PAIN_OR_DETERIORATION, 'Dolor o deterioro'),
    ]

    STATUS_ACTIVE = 'activa'
    STATUS_REVIEWED = 'revisada'
    STATUS_RESOLVED = 'resuelta'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_REVIEWED, 'Revisada'),
        (STATUS_RESOLVED, 'Resuelta'),
    ]

    SEVERITY_CHOICES = [
        ('warning', 'Advertencia'),
        ('critical', 'Critica'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='alertas_como_paciente',
        on_delete=models.CASCADE,
    )
    terapeuta = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='alertas_como_terapeuta',
        on_delete=models.CASCADE,
    )
    alert_type = models.CharField(max_length=40, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='warning')
    title = models.CharField(max_length=160)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    detected_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    source_session = models.ForeignKey(
        'ExerciseSession',
        related_name='generated_alerts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-detected_at']

    def __str__(self):
        return f'{self.alert_type} - {self.paciente}'


class MotivationProfile(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='motivacion',
        on_delete=models.CASCADE,
    )
    total_points = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_session_date = models.DateField(null=True, blank=True)
    leaderboard_opt_in = models.BooleanField(default=False)
    leaderboard_consented_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Motivacion {self.usuario}'


class ExerciseSession(models.Model):
    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sesiones_rehabilitacion',
        on_delete=models.CASCADE,
    )
    terapeuta = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sesiones_supervisadas',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    performed_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateField(null=True, blank=True)
    exercise_name = models.CharField(max_length=140, default='Sesion de rehabilitacion')
    repetitions_completed = models.PositiveIntegerField(default=0)
    planned_repetitions = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    pain_level = models.PositiveSmallIntegerField(default=0)
    mobility_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    points_awarded = models.PositiveIntegerField(default=0)
    speed_bonus_points = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    positive_feedback = models.CharField(max_length=180, blank=True)
    performance_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']

    def __str__(self):
        return f'{self.exercise_name} - {self.paciente}'


class PatientBadge(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='insignias',
        on_delete=models.CASCADE,
    )
    code = models.CharField(max_length=60)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240)
    awarded_at = models.DateTimeField(default=timezone.now)
    source_session = models.ForeignKey(
        ExerciseSession,
        related_name='badges_awarded',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-awarded_at']
        unique_together = ('usuario', 'code')

    def __str__(self):
        return f'{self.name} - {self.usuario}'


class WeeklySummary(models.Model):
    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='resumenes_semanales',
        on_delete=models.CASCADE,
    )
    week_start = models.DateField()
    week_end = models.DateField()
    sessions_completed = models.PositiveIntegerField(default=0)
    sessions_scheduled = models.PositiveIntegerField(default=0)
    points_obtained = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = ('paciente', 'week_start')

    def __str__(self):
        return f'Resumen {self.paciente} {self.week_start}'
