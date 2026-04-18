from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    
    # روابط السلة
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    
    # رابط إتمام الطلب (يجب أن يكون هنا قبل الـ slug)
    path('create/', views.order_create, name='order_create'),
    
    # رابط الأقسام (الديناميكي) - هذا يجب أن يكون دائماً في الأسفل
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    
    # رابط تفاصيل المنتج
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
]

