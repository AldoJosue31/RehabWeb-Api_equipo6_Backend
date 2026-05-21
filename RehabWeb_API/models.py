import uuid
from django.conf import settings
from django.db import models


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
