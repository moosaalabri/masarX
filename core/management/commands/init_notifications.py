from django.core.management.base import BaseCommand
from core.models import NotificationTemplate
from core.notifications import DEFAULT_TEMPLATES, get_notification_content

class Command(BaseCommand):
    help = 'Initialize default notification templates'

    def handle(self, *args, **options):
        count = 0
        for key, default in DEFAULT_TEMPLATES.items():
            obj, created = NotificationTemplate.objects.get_or_create(
                key=key,
                defaults={
                    'description': default.get('description', ''),
                    'available_variables': default.get('variables', ''),
                    'subject_en': default.get('subject_en', ''),
                    'subject_ar': default.get('subject_ar', ''),
                    'email_body_en': default.get('email_body_en', ''),
                    'email_body_ar': default.get('email_body_ar', ''),
                    'whatsapp_body_en': default.get('whatsapp_body_en', ''),
                    'whatsapp_body_ar': default.get('whatsapp_body_ar', ''),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created template: {key}'))
                count += 1
            else:
                self.stdout.write(f'Template exists: {key}')
        
        self.stdout.write(self.style.SUCCESS(f'Initialized {count} new templates.'))
