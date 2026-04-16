from django.core.management.base import BaseCommand
from app.models import TutorialStep

BASE_HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '    <meta charset="UTF-8">\n'
    '    <title>{% block title %}DjangoQuest{% endblock %}</title>\n'
    '    <style>\n'
    '        * { box-sizing: border-box; margin: 0; padding: 0; }\n'
    '        body { font-family: Arial, sans-serif; padding: 20px; background: #f9f9f9; color: #222; }\n'
    '        h1 { font-size: 1.8rem; margin-bottom: 12px; color: #1a1a2e; }\n'
    '        h2 { font-size: 1.3rem; margin: 10px 0 6px; color: #333; }\n'
    '        p  { margin-bottom: 10px; line-height: 1.5; }\n'
    '        nav { background: #1a1a2e; padding: 12px 20px; margin: -20px -20px 20px; }\n'
    '        nav a { color: white; margin-right: 16px; text-decoration: none; font-weight: bold; }\n'
    '        article { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 16px; margin-bottom: 12px; }\n'
    '    </style>\n'
    '</head>\n'
    '<body>\n'
    '    {% block content %}{% endblock %}\n'
    '</body>\n'
    '</html>'
)


class Command(BaseCommand):
    help = 'Populates base_template on all django-type TutorialStep records'

    def handle(self, *args, **options):
        updated = TutorialStep.objects.filter(file_type='django').update(base_template=BASE_HTML)
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} django steps with base_template'))
