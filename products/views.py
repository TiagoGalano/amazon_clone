# products/views.py - Complete and Fixed Views
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from .models import Product, Category, Sale, Discount, Review
from decimal import Decimal
import json

# Currency utilities (simplified for now)
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
}

def get_user_currency(request):
    """Get user's preferred currency from session"""
    return request.session.get('currency', 'USD')

def set_user_currency(request, currency):
    """Set user's preferred currency in session"""
    if currency in CURRENCY_SYMBOLS:
        request.session['currency'] = currency
        return True
    return False

class HomeView(ListView):
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        return Product.objects.filter(is_available=True, is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_products'] = Product.objects.filter(
            is_available=True, is_active=True
        ).order_by('-created_at')[:8]
        
        # Add currency info
        context['current_currency'] = get_user_currency(self.request)
        context['currency_symbol'] = CURRENCY_SYMBOLS.get(context['current_currency'], '$')
        
        # Add active sales
        context['active_sales'] = Sale.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )[:3]
        
        return context

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True, is_available=True)
        
        # Filter by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'name')
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_currency'] = get_user_currency(self.request)
        context['currency_symbol'] = CURRENCY_SYMBOLS.get(context['current_currency'], '$')
        
        # Current category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        
        # Search query
        context['search_query'] = self.request.GET.get('q', '')
        
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        currency = get_user_currency(self.request)
        
        # Price calculations
        context['original_price'] = product.get_price(currency)
        context['discounted_price'] = product.get_discounted_price(currency)
        context['discount_percentage'] = product.get_discount_percentage()
        context['has_discount'] = product.has_discount()
        context['currency'] = currency
        context['currency_symbol'] = CURRENCY_SYMBOLS.get(currency, '$')
        
        # Reviews and ratings
        reviews = product.reviews.all().order_by('-created_at')
        avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        
        context['reviews'] = reviews
        context['avg_rating'] = avg_rating or 0
        context['review_count'] = reviews.count()
        
        # Related products
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_available=True,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        return context

def product_detail(request, slug):
    """Function-based view for product detail (alternative to class-based)"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    currency = get_user_currency(request)
    
    # Calculate prices
    original_price = product.get_price(currency)
    discounted_price = product.get_discounted_price(currency)
    discount_percentage = product.get_discount_percentage()
    
    # Reviews and ratings
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        is_available=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'original_price': original_price,
        'discounted_price': discounted_price,
        'discount_percentage': discount_percentage,
        'has_discount': product.has_discount(),
        'currency': currency,
        'currency_symbol': CURRENCY_SYMBOLS.get(currency, '$'),
        'reviews': reviews,
        'avg_rating': avg_rating or 0,
        'review_count': reviews.count(),
        'related_products': related_products,
    }
    
    return render(request, 'products/product_detail.html', context)

def search_view(request):
    """Search products"""
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_available=True,
            is_active=True
        )
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    currency = get_user_currency(request)
    
    context = {
        'products': page_obj,
        'query': query,
        'total_results': products.count() if query else 0,
        'current_currency': currency,
        'currency_symbol': CURRENCY_SYMBOLS.get(currency, '$'),
        'categories': Category.objects.all(),
    }
    
    return render(request, 'products/search_results.html', context)

def sales_view(request):
    """View for displaying active sales"""
    active_sales = Sale.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    
    currency = get_user_currency(request)
    
    context = {
        'sales': active_sales,
        'currency': currency,
        'currency_symbol': CURRENCY_SYMBOLS.get(currency, '$'),
    }
    
    return render(request, 'products/sales.html', context)

# AJAX Views
def change_currency(request):
    """AJAX endpoint to change user currency"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            currency = data.get('currency', '').upper()
            
            if set_user_currency(request, currency):
                return JsonResponse({
                    'success': True,
                    'currency': currency,
                    'symbol': CURRENCY_SYMBOLS.get(currency, currency)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid currency'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

def change_location(request):
    """AJAX endpoint to change user location and currency"""
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            country_code = data.get('country_code', '').upper()
            country_name = data.get('country_name', '')
            
            # Debug logging
            print(f"Received data: country_code={country_code}, country_name={country_name}")
            
            if country_code and country_name:
                request.session['country_code'] = country_code
                request.session['country_name'] = country_name
                
                # Update currency based on location
                currency_map = {
                    'US': 'USD', 'GB': 'GBP', 'UK': 'GBP',
                    'DE': 'EUR', 'FR': 'EUR', 'IT': 'EUR', 'ES': 'EUR',
                    'PT': 'EUR', 'NL': 'EUR', 'AT': 'EUR', 'BE': 'EUR',
                    'FI': 'EUR', 'IE': 'EUR', 'LU': 'EUR', 'SI': 'EUR',
                    'SK': 'EUR', 'EE': 'EUR', 'LV': 'EUR', 'LT': 'EUR',
                    'MT': 'EUR', 'CY': 'EUR'
                }
                currency = currency_map.get(country_code, 'USD')
                set_user_currency(request, currency)
                
                return JsonResponse({
                    'success': True,
                    'country_code': country_code,
                    'country_name': country_name,
                    'currency': currency,
                    'currency_symbol': CURRENCY_SYMBOLS.get(currency, currency)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid location data - missing country_code or country_name'
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method allowed'
    }, status=405)

def get_product_price(request, product_id):
    """AJAX endpoint to get product price in current currency"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        currency = get_user_currency(request)
        
        original_price = product.get_price(currency)
        discounted_price = product.get_discounted_price(currency)
        
        return JsonResponse({
            'success': True,
            'original_price': float(original_price),
            'discounted_price': float(discounted_price),
            'has_discount': product.has_discount(),
            'discount_percentage': float(product.get_discount_percentage()),
            'currency': currency,
            'currency_symbol': CURRENCY_SYMBOLS.get(currency, currency)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)