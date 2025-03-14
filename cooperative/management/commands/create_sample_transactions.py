from django.core.management.base import BaseCommand
from cooperative.models import Transaction, BankAccount, Order
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample financial transactions for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20, help='Number of transactions to create')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        
        # Get all cooperatives
        cooperatives = User.objects.filter(role='cooperative')
        if not cooperatives.exists():
            self.stdout.write(self.style.ERROR('No cooperatives found. Please create at least one cooperative user.'))
            return
        
        # Create sample bank accounts if none exist
        for cooperative in cooperatives:
            if not BankAccount.objects.filter(cooperative=cooperative).exists():
                self.create_sample_bank_accounts(cooperative)
        
        # Get orders to link some transactions to
        orders = Order.objects.all()
        
        # Create transactions
        transactions_created = 0
        for i in range(count):
            cooperative = random.choice(cooperatives)
            
            # Determine transaction type and amount
            transaction_type = random.choice(['sent', 'received'])
            
            # Received transactions tend to be larger
            if transaction_type == 'received':
                amount = Decimal(str(random.randint(50000, 1000000)))
            else:
                amount = Decimal(str(random.randint(10000, 200000)))
            
            # Determine payment method
            payment_method = random.choice(['credit_card', 'wire_transfer', 'mobile_money', 'cash'])
            
            # Determine status (most are successful)
            status = random.choices(
                ['success', 'pending', 'failed'],
                weights=[0.8, 0.15, 0.05],
                k=1
            )[0]
            
            # Determine party name
            if transaction_type == 'received':
                party_names = [
                    'Simba Supermarket', 'Kigali Grocers', 'Food Distributors Ltd',
                    'Ministry of Agriculture', 'Food Aid International', 'Local Market Cooperative'
                ]
            else:
                party_names = [
                    'Farmer Support Program', 'Agricultural Supplies Ltd', 'Transport Services',
                    'Packaging Solutions', 'Staff Payroll', 'Utility Bills'
                ]
            
            party_name = random.choice(party_names)
            
            # Description
            descriptions = [
                f'Payment for {random.choice(["produce", "services", "supplies"])}',
                'Monthly transaction',
                'Scheduled payment',
                'Invoice settlement',
                ''
            ]
            description = random.choice(descriptions)
            
            # Link to order if it's a received payment
            order = None
            if transaction_type == 'received' and orders.exists() and random.random() > 0.5:
                order = random.choice(orders)
            
            # Create transaction
            transaction = Transaction.objects.create(
                cooperative=cooperative,
                transaction_type=transaction_type,
                amount=amount,
                payment_method=payment_method,
                status=status,
                party_name=party_name,
                description=description,
                reference_number=f'REF-{random.randint(10000, 99999)}',
                order=order
            )
            
            # Adjust created_at date to spread transactions over the last 90 days
            days_ago = random.randint(0, 90)
            transaction.created_at = timezone.now() - timedelta(days=days_ago)
            transaction.save(update_fields=['created_at'])
            
            transactions_created += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {transactions_created} sample transactions'))
    
    def create_sample_bank_accounts(self, cooperative):
        bank_data = [
            {
                'bank_name': 'Bank of Rwanda',
                'account_number': f'RW{random.randint(10000000, 99999999)}',
                'account_holder_name': cooperative.full_name,
                'is_primary': True
            },
            {
                'bank_name': 'IMI BANK',
                'account_number': f'IM{random.randint(10000000, 99999999)}',
                'account_holder_name': cooperative.full_name,
                'is_primary': False
            }
        ]
        
        for data in bank_data:
            BankAccount.objects.create(
                cooperative=cooperative,
                **data
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created sample bank accounts for {cooperative.full_name}'))

