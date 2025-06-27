# products/models.py - Fixed and Complete Models
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

User = get_user_model()

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category', kwargs={'category_slug': self.slug})

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
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    
    # Pricing - keeping backward compatibility with original price field
    price = models.DecimalField(max_digits=10, decimal_places=2)  # USD price
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_gbp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)  # Keep for backward compatibility
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Sync price fields
        if self.price and not self.price_usd:
            self.price_usd = self.price
        elif self.price_usd and not self.price:
            self.price = self.price_usd
        
        # Sync availability fields
        if hasattr(self, 'is_available') and not hasattr(self, '_synced'):
            self.is_active = self.is_available
            self._synced = True
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    def get_price(self, currency='USD'):
        """Get price in specified currency"""
        currency = currency.upper()
        
        if currency == 'USD':
            return self.price_usd or self.price
        elif currency == 'EUR':
            return self.price_eur or (self.price * Decimal('0.85'))
        elif currency == 'GBP':
            return self.price_gbp or (self.price * Decimal('0.75'))
        
        return self.price  # fallback to USD
    
    def get_discounted_price(self, currency='USD'):
        """Calculate price after discount"""
        original_price = self.get_price(currency)
        
        if not self.discount or not self.discount.is_valid():
            return original_price
            
        if self.discount.discount_type == 'percentage':
            discount_amount = original_price * (self.discount.value / 100)
        else:  # fixed amount
            discount_amount = self.discount.value
            # Convert fixed discount to appropriate currency if needed
            if currency == 'EUR':
                discount_amount = discount_amount * Decimal('0.85')
            elif currency == 'GBP':
                discount_amount = discount_amount * Decimal('0.75')
        
        discounted_price = original_price - discount_amount
        return max(discounted_price, Decimal('0.01'))
    
    def get_discount_percentage(self):
        """Get discount percentage for display"""
        if not self.discount or not self.discount.is_valid():
            return 0
            
        if self.discount.discount_type == 'percentage':
            return self.discount.value
        else:
            # Calculate percentage for fixed amount discount
            original_price = self.get_price('USD')
            if original_price > 0:
                return (self.discount.value / original_price) * 100
        return 0
    
    def has_discount(self):
        """Check if product has active discount"""
        return self.discount and self.discount.is_valid()
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.product.name} - Image"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"

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
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date