from django.contrib.auth.models import Group, User
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from mensajeria.models import Conversation
from RehabWeb_API.models import (
    Alert,
    ExerciseSession,
    MotivationProfile,
    PacienteProfile,
    PatientBadge,
    PerfilClinico,
    TerapeutaProfile,
    WeeklySummary,
)
from RehabWeb_API.roles import ROLE_PACIENTE, ROLE_TERAPEUTA
from RehabWeb_API.services import finalize_session_metrics, is_minor, therapist_for_patient


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
    total_points = serializers.IntegerField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)
    best_streak = serializers.IntegerField(read_only=True)
    leaderboard_opt_in = serializers.BooleanField(required=False)
    leaderboard_enabled = serializers.BooleanField(read_only=True)

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
            motivation = getattr(instance, 'motivacion', None)
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
                'total_points': motivation.total_points if motivation else 0,
                'current_streak': motivation.current_streak if motivation else 0,
                'best_streak': motivation.best_streak if motivation else 0,
                'leaderboard_opt_in': motivation.leaderboard_opt_in if motivation else False,
                'leaderboard_enabled': not is_minor(instance),
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

        motivation, _ = MotivationProfile.objects.get_or_create(usuario=user)
        if 'leaderboard_opt_in' in data:
            wants_ranking = bool(data.get('leaderboard_opt_in')) and not is_minor(user)
            motivation.leaderboard_opt_in = wants_ranking
            motivation.leaderboard_consented_at = timezone.now() if wants_ranking else None
            motivation.save(update_fields=['leaderboard_opt_in', 'leaderboard_consented_at', 'updated_at'])

        if terapeuta_profile:
            Conversation.objects.get_or_create(paciente=user, terapeuta=terapeuta_profile.usuario)


class AlertSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    terapeuta_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'terapeuta',
            'terapeuta_nombre',
            'alert_type',
            'severity',
            'title',
            'message',
            'status',
            'detected_at',
            'reviewed_at',
            'resolved_at',
            'source_session',
        ]
        read_only_fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'terapeuta',
            'terapeuta_nombre',
            'alert_type',
            'severity',
            'title',
            'message',
            'detected_at',
            'reviewed_at',
            'resolved_at',
            'source_session',
        ]

    def get_paciente_nombre(self, obj):
        return obj.paciente.get_full_name().strip() or obj.paciente.username

    def get_terapeuta_nombre(self, obj):
        return obj.terapeuta.get_full_name().strip() or obj.terapeuta.username


class ExerciseSessionSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ExerciseSession
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'terapeuta',
            'performed_at',
            'scheduled_for',
            'exercise_name',
            'repetitions_completed',
            'planned_repetitions',
            'duration_seconds',
            'pain_level',
            'mobility_score',
            'points_awarded',
            'speed_bonus_points',
            'streak_days',
            'positive_feedback',
            'performance_notes',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'paciente_nombre',
            'terapeuta',
            'points_awarded',
            'speed_bonus_points',
            'streak_days',
            'positive_feedback',
            'created_at',
        ]

    def get_paciente_nombre(self, obj):
        return obj.paciente.get_full_name().strip() or obj.paciente.username

    def validate_pain_level(self, value):
        if value > 10:
            raise serializers.ValidationError('El nivel de dolor debe estar entre 0 y 10.')
        return value

    def validate(self, data):
        request = self.context.get('request')
        if not request:
            return data

        role = self.context.get('role')
        paciente = data.get('paciente')

        if role == ROLE_PACIENTE:
            data['paciente'] = request.user
        elif role == ROLE_TERAPEUTA:
            if not paciente:
                raise serializers.ValidationError({'paciente': 'Como terapeuta debes indicar el paciente.'})
            therapist = therapist_for_patient(paciente)
            if therapist and therapist != request.user:
                raise serializers.ValidationError('Solo puedes registrar sesiones de tus pacientes.')
        return data

    def create(self, validated_data):
        patient = validated_data['paciente']
        validated_data['terapeuta'] = therapist_for_patient(patient)
        session = ExerciseSession.objects.create(**validated_data)
        return finalize_session_metrics(session)


class MotivationProfileSerializer(serializers.ModelSerializer):
    leaderboard_enabled = serializers.SerializerMethodField()

    class Meta:
        model = MotivationProfile
        fields = [
            'total_points',
            'current_streak',
            'best_streak',
            'last_session_date',
            'leaderboard_opt_in',
            'leaderboard_enabled',
            'updated_at',
        ]

    def get_leaderboard_enabled(self, obj):
        return not is_minor(obj.usuario)

    def validate_leaderboard_opt_in(self, value):
        if value and is_minor(self.instance.usuario):
            raise serializers.ValidationError('El ranking no esta disponible para menores.')
        return value

    def update(self, instance, validated_data):
        if 'leaderboard_opt_in' in validated_data:
            instance.leaderboard_opt_in = validated_data['leaderboard_opt_in']
            instance.leaderboard_consented_at = timezone.now() if instance.leaderboard_opt_in else None
            instance.save(update_fields=['leaderboard_opt_in', 'leaderboard_consented_at', 'updated_at'])
        return instance


class PatientBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientBadge
        fields = ['id', 'code', 'name', 'description', 'awarded_at', 'source_session']


class WeeklySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklySummary
        fields = [
            'id',
            'week_start',
            'week_end',
            'sessions_completed',
            'sessions_scheduled',
            'points_obtained',
            'sent_at',
            'created_at',
        ]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()

    class Meta:
        model = MotivationProfile
        fields = ['nombre', 'total_points', 'best_streak']

    def get_nombre(self, obj):
        full_name = obj.usuario.get_full_name().strip()
        if full_name:
            parts = full_name.split()
            return f'{parts[0]} {parts[-1][0]}.'
        return obj.usuario.username
