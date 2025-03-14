from django.core.management.base import BaseCommand
from cooperative.models import ProduceType, ProduceVariant
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates initial produce types and variants with images'

    def handle(self, *args, **kwargs):
        # Initial produce data with image URLs
        produce_types = [
            {
                'name': 'Almond',
                'description': 'Premium quality almonds grown in Rwanda',
                'category': 'nuts',
                'base_price': Decimal('2000.00'),
                'image_url': 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=800',
            },
            {
                'name': 'Rice',
                'description': 'High-quality rice grown in local paddies',
                'category': 'grains',
                'base_price': Decimal('1200.00'),
                'image_url': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800',
            },
            {
                'name': 'Tomatoes',
                'description': 'Fresh, locally grown tomatoes',
                'category': 'vegetables',
                'base_price': Decimal('800.00'),
                'image_url': 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800',
            },
            {
                'name': 'Bananas',
                'description': 'Sweet and nutritious bananas',
                'category': 'fruits',
                'base_price': Decimal('1000.00'),
                'image_url': 'https://images.unsplash.com/photo-1603833665858-e61d17a86224?w=800',
            },
            {
                'name': 'Coffee Beans',
                'description': 'Premium Rwandan coffee beans',
                'category': 'other',
                'base_price': Decimal('3000.00'),
                'image_url': 'https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=800',
            },
            {
                'name': 'Potatoes',
                'description': 'Fresh potatoes from local farms',
                'category': 'vegetables',
                'base_price': Decimal('600.00'),
                'image_url': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=800',
            }
        ]

        self.stdout.write(self.style.SUCCESS('Starting to create initial produce types...'))
        
        for produce_data in produce_types:
            # Get or create the produce type
            produce_type, created = ProduceType.objects.get_or_create(
                name=produce_data['name'],
                defaults={
                    'description': produce_data['description'],
                    'category': produce_data['category'],
                    'base_price': produce_data['base_price'],
                    'image_url': produce_data['image_url'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created produce type: {produce_type.name}'))
                
                # Create variants for each produce type with different price multipliers
                variants = [
                    ('A', Decimal('1.2')),  # Premium grade
                    ('B', Decimal('1.0')),  # Standard grade
                    ('C', Decimal('0.8')),  # Economy grade
                ]
                
                for grade, multiplier in variants:
                    variant, variant_created = ProduceVariant.objects.get_or_create(
                        produce_type=produce_type,
                        grade=grade,
                        defaults={'price_multiplier': multiplier}
                    )
                    
                    if variant_created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created variant: {variant} (Price: RWF {produce_type.base_price * multiplier})'
                            )
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Produce type already exists: {produce_type.name}')
                )

        self.stdout.write(self.style.SUCCESS('Initial produce types and variants created successfully'))
        
        # Count and display the number of produce types and variants
        produce_count = ProduceType.objects.count()
        variant_count = ProduceVariant.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total produce types: {produce_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total produce variants: {variant_count}'))

