from django.db import migrations


def create_role_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for group_name in ('Paciente', 'Terapeuta'):
        Group.objects.get_or_create(name=group_name)


def remove_role_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=('Paciente', 'Terapeuta')).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
