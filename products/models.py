# models.py - Enhanced Product Model with Discounts
from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name

class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_gbp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def get_price(self, currency='USD'):
        """Get price in specified currency"""
        prices = {
            'USD': self.price_usd,
            'EUR': self.price_eur or self.price_usd * Decimal('0.85'),  # fallback conversion
            'GBP': self.price_gbp or self.price_usd * Decimal('0.75'),  # fallback conversion
        }
        return prices.get(currency.upper(), self.price_usd)
    
    def get_discounted_price(self, currency='USD'):
        """Calculate price after discount"""
        original_price = self.get_price(currency)
        
        if not self.discount or not self.discount.is_valid():
            return original_price
            
        if self.discount.discount_type == 'percentage':
            discount_amount = original_price * (self.discount.value / 100)
        else:  # fixed amount
            # Convert fixed discount to appropriate currency if needed
            discount_amount = self.discount.value
            if currency == 'EUR':
                discount_amount = discount_amount * Decimal('0.85')
            elif currency == 'GBP':
                discount_amount = discount_amount * Decimal('0.75')
        
        discounted_price = original_price - discount_amount
        return max(discounted_price, Decimal('0.01'))  # Minimum price of 0.01
    
    def get_discount_percentage(self):
        """Get discount percentage for display"""
        if not self.discount or not self.discount.is_valid():
            return 0
            
        if self.discount.discount_type == 'percentage':
            return self.discount.value
        else:
            # Calculate percentage for fixed amount discount
            original_price = self.price_usd
            if original_price > 0:
                return (self.discount.value / original_price) * 100
        return 0
    
    def has_discount(self):
        """Check if product has active discount"""
        return self.discount and self.discount.is_valid()

class Sale(models.Model):
    """Special sales events"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date