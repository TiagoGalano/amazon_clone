from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('search/', views.search_view, name='search'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('sales/', views.sales_view, name='sales'),
    # AJAX URLs
    path('ajax/change-currency/', views.change_currency, name='change_currency'),
    path('ajax/change-location/', views.change_location, name='change_location'),
    path('ajax/product-price/<int:product_id>/', views.get_product_price, name='get_product_price'),
]
