from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # المنتجات
    path('', views.product_list, name='product_list'),
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # السلة (ربطناها هنا لتجنب مشاكل الـ NoReverseMatch)
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    # الطلبات
    path('order/create/', views.order_create, name='order_create'),
]