from django.contrib import admin
from .models import Category, Product, ProductImage, Review, Discount, Sale

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'is_valid_now']
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name']
    date_hierarchy = 'start_date'
    
    def is_valid_now(self, obj):
        return obj.is_valid()
    is_valid_now.boolean = True
    is_valid_now.short_description = 'Valid Now'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price_usd', 'price_eur', 'price_gbp', 
        'stock', 'has_discount', 'discount_percentage', 'is_active'
    ]
    list_filter = ['category', 'is_active', 'created_at', 'discount']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'image', 'is_active')
        }),
        ('Pricing', {
            'fields': ('price_usd', 'price_eur', 'price_gbp'),
            'description': 'Prices in different currencies. EUR and GBP are optional - if not set, they will be automatically calculated from USD.'
        }),
        ('Inventory', {
            'fields': ('stock',)
        }),
        ('Discounts', {
            'fields': ('discount',),
            'description': 'Select a discount to apply to this product.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_discount(self, obj):
        return obj.has_discount()
    has_discount.boolean = True
    has_discount.short_description = 'Has Discount'
    
    def discount_percentage(self, obj):
        percentage = obj.get_discount_percentage()
        if percentage > 0:
            return f"{percentage:.1f}%"
        return "-"
    discount_percentage.short_description = 'Discount %'
    
    actions = ['apply_discount', 'remove_discount', 'activate_products', 'deactivate_products']
    
    def apply_discount(self, request, queryset):
        # This would open a form to select discount - simplified version
        count = queryset.count()
        self.message_user(request, f'{count} products selected for discount application.')
    apply_discount.short_description = "Apply discount to selected products"
    
    def remove_discount(self, request, queryset):
        updated = queryset.update(discount=None)
        self.message_user(request, f'{updated} products had their discounts removed.')
    remove_discount.short_description = "Remove discount from selected products"
    
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} products were activated.')
    activate_products.short_description = "Activate selected products"
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products were deactivated.')
    deactivate_products.short_description = "Deactivate selected products"

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'is_valid_now']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    date_hierarchy = 'start_date'
    filter_horizontal = ['products', 'categories']
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('name', 'description', 'discount_percentage', 'is_active')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Products & Categories', {
            'fields': ('products', 'categories'),
            'description': 'Select specific products or entire categories for this sale.'
        }),
    )
    
    def is_valid_now(self, obj):
        return obj.is_valid()
    is_valid_now.boolean = True
    is_valid_now.short_description = 'Active Now'
    
    actions = ['activate_sales', 'deactivate_sales', 'extend_sales']
    
    def activate_sales(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} sales were activated.')
    activate_sales.short_description = "Activate selected sales"
    
    def deactivate_sales(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} sales were deactivated.')
    deactivate_sales.short_description = "Deactivate selected sales"
    
    def extend_sales(self, request, queryset):
        from datetime import timedelta
        for sale in queryset:
            sale.end_date = sale.end_date + timedelta(days=7)
            sale.save()
        count = queryset.count()
        self.message_user(request, f'{count} sales were extended by 7 days.')
    extend_sales.short_description = "Extend selected sales by 7 days"

# Custom admin site configuration
admin.site.site_header = "Amazon Clone Administration"
admin.site.site_title = "Amazon Clone Admin"
admin.site.index_title = "Welcome to Amazon Clone Administration"