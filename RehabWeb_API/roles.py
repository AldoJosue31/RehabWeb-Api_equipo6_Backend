ROLE_PACIENTE = 'paciente'
ROLE_TERAPEUTA = 'terapeuta'
VALID_ROLES = {ROLE_PACIENTE, ROLE_TERAPEUTA}

ROLE_GROUP_ALIASES = {
    ROLE_PACIENTE: {'paciente', 'pacientes', 'patient', 'patients'},
    ROLE_TERAPEUTA: {'terapeuta', 'terapeutas', 'therapist', 'therapists'},
}


def normalize_role(value):
    if not value:
        return None

    role = str(value).strip().lower()
    for canonical_role, aliases in ROLE_GROUP_ALIASES.items():
        if role in aliases:
            return canonical_role

    return role if role in VALID_ROLES else None


def get_user_roles(user):
    if not user or not user.is_authenticated:
        return set()

    roles = set()

    if user.is_superuser:
        roles.update(VALID_ROLES)

    for group_name in user.groups.values_list('name', flat=True):
        role = normalize_role(group_name)
        if role:
            roles.add(role)

    try:
        from mensajeria.models import Conversation

        if Conversation.objects.filter(paciente=user).exists():
            roles.add(ROLE_PACIENTE)
        if Conversation.objects.filter(terapeuta=user).exists():
            roles.add(ROLE_TERAPEUTA)
    except Exception:
        pass

    return roles


def user_has_role(user, role):
    normalized_role = normalize_role(role)
    return bool(normalized_role and normalized_role in get_user_roles(user))


def get_request_role(request):
    if not request:
        return None

    role = request.headers.get('X-Rehab-Role') or request.data.get('role') or request.data.get('rol')
    return normalize_role(role)


def user_matches_conversation_role(user, conversation, role):
    normalized_role = normalize_role(role)

    if normalized_role == ROLE_PACIENTE:
        return conversation.paciente_id == user.id
    if normalized_role == ROLE_TERAPEUTA:
        return conversation.terapeuta_id == user.id

    return conversation.paciente_id == user.id or conversation.terapeuta_id == user.id
