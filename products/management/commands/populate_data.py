from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Product
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Create superuser if not exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))

        # Create categories
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'description': 'Latest electronic gadgets and devices'},
            {'name': 'Clothing', 'slug': 'clothing', 'description': 'Fashion and apparel for all occasions'},
            {'name': 'Books', 'slug': 'books', 'description': 'Books across all genres and topics'},
            {'name': 'Home & Garden', 'slug': 'home-garden', 'description': 'Everything for your home and garden'},
            {'name': 'Sports', 'slug': 'sports', 'description': 'Sports equipment and accessories'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create sample products
        electronics = Category.objects.get(slug='electronics')
        clothing = Category.objects.get(slug='clothing')
        books = Category.objects.get(slug='books')

        products_data = [
            {
                'name': 'Smartphone Pro Max',
                'slug': 'smartphone-pro-max',
                'description': 'Latest smartphone with advanced features and excellent camera quality.',
                'price': Decimal('999.99'),
                'stock': 50,
                'category': electronics,
            },
            {
                'name': 'Wireless Headphones',
                'slug': 'wireless-headphones',
                'description': 'Premium wireless headphones with noise cancellation.',
                'price': Decimal('299.99'),
                'stock': 30,
                'category': electronics,
            },
            {
                'name': 'Classic T-Shirt',
                'slug': 'classic-t-shirt',
                'description': 'Comfortable cotton t-shirt perfect for everyday wear.',
                'price': Decimal('19.99'),
                'stock': 100,
                'category': clothing,
            },
            {
                'name': 'Denim Jeans',
                'slug': 'denim-jeans',
                'description': 'High-quality denim jeans with perfect fit.',
                'price': Decimal('79.99'),
                'stock': 75,
                'category': clothing,
            },
            {
                'name': 'Programming Guide',
                'slug': 'programming-guide',
                'description': 'Complete guide to modern programming techniques.',
                'price': Decimal('39.99'),
                'stock': 25,
                'category': books,
            },
        ]

        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults=prod_data
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')

        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))