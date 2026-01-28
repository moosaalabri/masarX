from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = _('Masar Express Management')
    default = True

    def ready(self):
        from django.contrib.auth.models import Permission
        
        # Monkey-patch Permission.__str__ to show a VERY short name
        # Standard was: "app_label | model | name" (e.g. core | country | Can add country)
        # Previous fix: "Country | Can add country"
        # New fix: "add Country", "change Country" (strips "Can " prefix)
        
        def short_str(self):
            name = str(self.name)
            if name.startswith("Can "):
                return name[4:]
            return name

        Permission.__str__ = short_str