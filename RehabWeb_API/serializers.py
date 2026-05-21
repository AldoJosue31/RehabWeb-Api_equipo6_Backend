from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import serializers
from mensajeria.models import Conversation
from RehabWeb_API.models import PacienteProfile, PerfilClinico, TerapeutaProfile
from RehabWeb_API.roles import ROLE_PACIENTE, ROLE_TERAPEUTA


ROLE_GROUPS = {
    ROLE_PACIENTE: 'Paciente',
    ROLE_TERAPEUTA: 'Terapeuta',
}


class AccountSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    nombre_completo = serializers.CharField(max_length=180, required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    role = serializers.CharField(read_only=True)

    especialidad = serializers.CharField(max_length=120, required=False, allow_blank=True)
    numero_licencia = serializers.CharField(max_length=80, required=False, allow_blank=True)

    terapeuta_id = serializers.IntegerField(required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    estado = serializers.ChoiceField(choices=PacienteProfile.ESTADO_CHOICES, required=False)
    estrategia_validacion = serializers.CharField(max_length=120, required=False, allow_blank=True)
    estrategia_progreso = serializers.CharField(max_length=120, required=False, allow_blank=True)
    diagnostico_principal = serializers.CharField(max_length=180, required=False, allow_blank=True)
    historial_medico = serializers.CharField(required=False, allow_blank=True)
    nivel_movilidad = serializers.ChoiceField(choices=PerfilClinico.NIVEL_MOVILIDAD_CHOICES, required=False)
    restricciones = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ese usuario ya existe.')
        return value

    def validate_numero_licencia(self, value):
        role = self.context.get('role')
        if role != ROLE_TERAPEUTA or not value:
            return value

        qs = TerapeutaProfile.objects.filter(numero_licencia=value)
        if self.instance and hasattr(self.instance, 'perfil_terapeuta'):
            qs = qs.exclude(pk=self.instance.perfil_terapeuta.pk)
        if qs.exists():
            raise serializers.ValidationError('Ese numero de licencia ya existe.')
        return value

    def validate_terapeuta_id(self, value):
        if value is None:
            return value
        if not TerapeutaProfile.objects.filter(usuario_id=value).exists():
            raise serializers.ValidationError('El terapeuta seleccionado no existe.')
        return value

    def to_representation(self, instance):
        role = self.context.get('role')
        full_name = instance.get_full_name().strip()
        data = {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'nombre_completo': full_name,
            'role': role,
        }

        if role == ROLE_TERAPEUTA:
            profile = getattr(instance, 'perfil_terapeuta', None)
            data.update({
                'especialidad': profile.especialidad if profile else '',
                'numero_licencia': profile.numero_licencia if profile else '',
            })
        else:
            profile = getattr(instance, 'perfil_paciente', None)
            perfil_clinico = profile.perfil_clinico if profile else None
            data.update({
                'terapeuta_id': profile.terapeuta.usuario_id if profile and profile.terapeuta else None,
                'fecha_nacimiento': profile.fecha_nacimiento if profile else None,
                'estado': profile.estado if profile else 'activo',
                'estrategia_validacion': profile.estrategia_validacion if profile else 'Libre',
                'estrategia_progreso': profile.estrategia_progreso if profile else 'Por rutinas',
                'diagnostico_principal': perfil_clinico.diagnostico_principal if perfil_clinico else '',
                'historial_medico': perfil_clinico.historial_medico if perfil_clinico else '',
                'nivel_movilidad': perfil_clinico.nivel_movilidad if perfil_clinico else 'medio',
                'restricciones': perfil_clinico.restricciones if perfil_clinico else '',
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        role = self.context['role']
        user = User(username=validated_data['username'], email=validated_data.get('email', ''))
        self._apply_common_fields(user, validated_data)
        password = validated_data.get('password') or 'RehabWeb123!'
        user.set_password(password)
        user.save()
        self._set_group(user, role)
        self._upsert_profile(user, role, validated_data)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        role = self.context['role']
        self._apply_common_fields(instance, validated_data)
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        self._set_group(instance, role)
        self._upsert_profile(instance, role, validated_data)
        return instance

    def _apply_common_fields(self, user, data):
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        nombre_completo = data.get('nombre_completo')
        if nombre_completo is not None:
            parts = nombre_completo.strip().split(' ', 1)
            user.first_name = parts[0] if parts else ''
            user.last_name = parts[1] if len(parts) > 1 else ''
        user.is_active = True

    def _set_group(self, user, role):
        group, _ = Group.objects.get_or_create(name=ROLE_GROUPS[role])
        user.groups.add(group)

    def _upsert_profile(self, user, role, data):
        if role == ROLE_TERAPEUTA:
            TerapeutaProfile.objects.update_or_create(
                usuario=user,
                defaults={
                    'especialidad': data.get('especialidad') or 'Fisioterapia',
                    'numero_licencia': data.get('numero_licencia') or f'LIC-{user.id}',
                },
            )
            return

        terapeuta_profile = None
        terapeuta_id = data.get('terapeuta_id')
        if terapeuta_id:
            terapeuta_profile = TerapeutaProfile.objects.get(usuario_id=terapeuta_id)

        diagnostico = data.get('diagnostico_principal') or 'Sin diagnostico registrado'
        paciente_profile = getattr(user, 'perfil_paciente', None)
        perfil_clinico = paciente_profile.perfil_clinico if paciente_profile else None
        if perfil_clinico:
            perfil_clinico.diagnostico_principal = diagnostico
            perfil_clinico.historial_medico = data.get('historial_medico', perfil_clinico.historial_medico)
            perfil_clinico.nivel_movilidad = data.get('nivel_movilidad', perfil_clinico.nivel_movilidad)
            perfil_clinico.restricciones = data.get('restricciones', perfil_clinico.restricciones)
            perfil_clinico.save()
        else:
            perfil_clinico = PerfilClinico.objects.create(
                diagnostico_principal=diagnostico,
                historial_medico=data.get('historial_medico', ''),
                nivel_movilidad=data.get('nivel_movilidad', 'medio'),
                restricciones=data.get('restricciones', ''),
            )

        PacienteProfile.objects.update_or_create(
            usuario=user,
            defaults={
                'terapeuta': terapeuta_profile,
                'perfil_clinico': perfil_clinico,
                'fecha_nacimiento': data.get('fecha_nacimiento'),
                'estado': data.get('estado', 'activo'),
                'estrategia_validacion': data.get('estrategia_validacion') or 'Libre',
                'estrategia_progreso': data.get('estrategia_progreso') or 'Por rutinas',
            },
        )

        if terapeuta_profile:
            Conversation.objects.get_or_create(paciente=user, terapeuta=terapeuta_profile.usuario)
