# views.py - Updated views with currency and discount support
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from .models import Product, Category, Sale, Discount
from utils.currency import converter, get_user_currency, set_user_currency, CURRENCY_SYMBOLS
import json

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_currency'] = get_user_currency(self.request)
        context['currency_symbol'] = CURRENCY_SYMBOLS.get(context['current_currency'], '$')
        
        # Add active sales
        context['active_sales'] = Sale.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        
        return context

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    currency = get_user_currency(request)
    
    # Calculate prices
    original_price = product.get_price(currency)
    discounted_price = product.get_discounted_price(currency)
    discount_percentage = product.get_discount_percentage()
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'original_price': original_price,
        'discounted_price': discounted_price,
        'discount_percentage': discount_percentage,
        'has_discount': product.has_discount(),
        'currency': currency,
        'currency_symbol': CURRENCY_SYMBOLS.get(currency, '$'),
        'related_products': related_products,
    }
    
    return render(request, 'products/product_detail.html', context)

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
            data = json.loads(request.body)
            country_code = data.get('country_code', '').upper()
            country_name = data.get('country_name', '')
            
            if country_code and country_name:
                request.session['country_code'] = country_code
                request.session['country_name'] = country_name
                
                # Update currency based on location
                from utils.currency import get_location_currency
                currency = get_location_currency(country_code)
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
                    'error': 'Invalid location data'
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