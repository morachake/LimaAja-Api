# authentication/management/commands/create_superuser.py

from django.core.management.base import BaseCommand
from authentication.models import User

class Command(BaseCommand):
    help = 'Creates a superuser non-interactively if it doesn\'t exist'

    def handle(self, *args, **options):
        email = 'limaAja@admin.com'
        full_name = 'LimaAja Admin'
        phone_number = '0701234567'
        password = 'LimaAja2025'
        
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email, 
                full_name=full_name,
                phone_number=phone_number,
                password=password,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser with email: {email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser with email {email} already exists'))