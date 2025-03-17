# authentication/management/commands/create_superuser.py

from django.core.management.base import BaseCommand
from authentication.models import User  

class Command(BaseCommand):
    help = 'Creates a superuser non-interactively if it doesn\'t exist'

    def handle(self, *args, **options):
        username = 'limaAja@admin.com'
        email = 'limaAja@admin.com'
        password = 'LimaAja2025'
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {username} already exists'))