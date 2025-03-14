from django.core.management.base import BaseCommand
from cooperative.models import (
    ProduceType, ProduceVariant, CooperativeProduce, 
    Customer, Order, OrderItem, OrderReview
)
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample orders for testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of orders to create')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        
        # Get all cooperatives
        cooperatives = User.objects.filter(role='cooperative')
        if not cooperatives.exists():
            self.stdout.write(self.style.ERROR('No cooperatives found. Please create at least one cooperative user.'))
            return
        
        # Create sample customers if none exist
        if Customer.objects.count() < 5:
            self.create_sample_customers()
        
        customers = Customer.objects.all()
        
        # Get all produce types
        produce_types = ProduceType.objects.all()
        if not produce_types.exists():
            self.stdout.write(self.style.ERROR('No produce types found. Please run create_initial_produce command first.'))
            return
        
        # Create orders
        orders_created = 0
        for i in range(count):
            cooperative = random.choice(cooperatives)
            customer = random.choice(customers)
            
            # Create order
            order = Order.objects.create(
                cooperative=cooperative,
                customer=customer,
                status=random.choice(['new', 'processing', 'delivery', 'delivered', 'cancelled']),
                shipping_address=f"{customer.full_name}, {random.choice(['Kigali', 'Butare', 'Gisenyi', 'Ruhengeri', 'Cyangugu'])}",
                payment_method=random.choice(['Cash on Delivery', 'Mobile Money', 'Bank Transfer']),
                notes=random.choice(['Please deliver in the morning', 'Call before delivery', '', ''])
            )

            # Create 1-3 order items
            num_items = random.randint(1, 3)
            total_price = 0
            for j in range(num_items):
                produce_type = random.choice(produce_types)
                variant = random.choice(produce_type.variants.all())
                quantity = Decimal(str(round(random.uniform(0.5, 5.0), 2)))
                unit_price = produce_type.base_price * variant.price_multiplier
                subtotal = quantity * unit_price
                
                OrderItem.objects.create(
                    order=order,
                    produce_type=produce_type,
                    variant=variant,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                
                total_price += subtotal

            # Update order total
            order.total_price = total_price
            order.save()
            
            # Add review for some delivered orders
            if order.status == 'delivered' and random.random() > 0.3:
                OrderReview.objects.create(
                    order=order,
                    rating=random.randint(3, 5),
                    comment=random.choice([
                        'Great quality produce!',
                        'Delivery was on time and the produce was fresh.',
                        'Very satisfied with my purchase.',
                        'Will order again.',
                        'Good service, thank you.'
                    ])
                )
            
            # Adjust created_at date to spread orders over the last 30 days
            days_ago = random.randint(0, 30)
            order.created_at = timezone.now() - timedelta(days=days_ago)
            order.save(update_fields=['created_at'])
            
            orders_created += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {orders_created} sample orders'))
    
    def create_sample_customers(self):
        customers_data = [
            {
                'full_name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone_number': '+250781234567',
                'role': 'individual',
                'address': 'Kigali, Rwanda'
            },
            {
                'full_name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'phone_number': '+250782345678',
                'role': 'individual',
                'address': 'Butare, Rwanda'
            },
            {
                'full_name': 'Simba Supermarket',
                'email': 'orders@simbasupermarket.com',
                'phone_number': '+250783456789',
                'role': 'business',
                'address': 'Kigali, Rwanda'
            },
            {
                'full_name': 'Ministry of Agriculture',
                'email': 'agriculture@gov.rw',
                'phone_number': '+250784567890',
                'role': 'government',
                'address': 'Kigali, Rwanda'
            },
            {
                'full_name': 'Food Aid International',
                'email': 'procurement@foodaid.org',
                'phone_number': '+250785678901',
                'role': 'ngo',
                'address': 'Gisenyi, Rwanda'
            }
        ]
        
        for data in customers_data:
            Customer.objects.get_or_create(
                email=data['email'],
                defaults=data
            )
        
        self.stdout.write(self.style.SUCCESS('Created sample customers'))

