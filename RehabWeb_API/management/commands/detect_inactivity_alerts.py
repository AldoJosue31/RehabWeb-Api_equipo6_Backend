from django.core.management.base import BaseCommand

from RehabWeb_API.services import detect_inactivity_alerts


class Command(BaseCommand):
    help = 'Genera alertas INACTIVITY_WARNING para pacientes con mas de 3 dias sin ejercicios.'

    def handle(self, *args, **options):
        generated = detect_inactivity_alerts()
        self.stdout.write(self.style.SUCCESS(f'Alertas de inactividad generadas: {generated}'))
