from django.contrib import admin
from .models import PacienteProfile, PerfilClinico, TerapeutaProfile


@admin.register(TerapeutaProfile)
class TerapeutaProfileAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'especialidad', 'numero_licencia')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'numero_licencia')


@admin.register(PacienteProfile)
class PacienteProfileAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'terapeuta', 'estado', 'fecha_nacimiento')
    list_filter = ('estado',)
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(PerfilClinico)
class PerfilClinicoAdmin(admin.ModelAdmin):
    list_display = ('diagnostico_principal', 'nivel_movilidad')
    list_filter = ('nivel_movilidad',)
    search_fields = ('diagnostico_principal',)
