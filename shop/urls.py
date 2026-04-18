from django.urls import path  # تأكد من وجود هذا السطر بدقة
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    
    # روابط السلة
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
    # رابط إتمام الطلب
    path('create/', views.order_create, name='order_create'),
    
    # الروابط الديناميكية (يجب أن تبقى في الأسفل)
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]