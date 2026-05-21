import uuid
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='conversaciones_como_paciente', 
        on_delete=models.CASCADE
    )
    terapeuta = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='conversaciones_como_terapeuta', 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Evita duplicar conversaciones entre las mismas dos personas
        unique_together = ('paciente', 'terapeuta')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.paciente} - {self.terapeuta}"


class Message(models.Model):
    STATUS_CHOICES = [
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('visto', 'Visto'),
    ]

    conversation = models.ForeignKey(
        Conversation, 
        related_name='mensajes', 
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='mensajes_enviados', 
        on_delete=models.CASCADE
    )
    
    # Aquí guardamos el texto cifrado. Para Django es solo un string largo.
    encrypted_text = models.TextField(
        blank=True, 
        null=True, 
        help_text="Texto cifrado generado por el frontend"
    )
    
    # Manejo de archivos adjuntos
    file_attachment = models.FileField(
        upload_to='mensajeria/archivos/%Y/%m/', 
        blank=True, 
        null=True
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='enviado')

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensaje {self.id} de {self.sender} en {self.timestamp}"
    
class VideoCall(models.Model):
    STATUS_CHOICES = [
        ('programada', 'Programada'), # Por si a futuro quieren agendarlas
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    # Room ID inquebrantable para Jitsi o cualquier proveedor WebRTC
    room_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    conversation = models.ForeignKey(
        Conversation, 
        related_name='videollamadas', 
        on_delete=models.CASCADE
    )
    
    # Saber quién dio click al botón primero
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='llamadas_iniciadas', 
        on_delete=models.SET_NULL,
        null=True
    )
    
    # Registro de tiempos para reportes analíticos (RF-REP-001)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(auto_now_add=True) # Cuándo empezó realmente
    ended_at = models.DateTimeField(null=True, blank=True) # Cuándo colgaron
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='activa')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sala {self.room_id} | Conversación {self.conversation.id}"

    @property
    def duration_minutes(self):
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            return round(delta.total_seconds() / 60, 2)
        return 0