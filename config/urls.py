from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User

urlpatterns = [
    path('admin/', admin.site.urls),
    # نحن هنا نخبر جانجو أن أي رابط يبدأ بـ 'cart/' أو 'order/' أو فارغ ''
    # سيذهب للبحث عنه في ملف shop/urls.py
    path('', include('shop.urls', namespace='shop')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
    
    # كود للتأكد من وجود المستخدم وصلاحياته وكلمة مروره على السيرفر
try:
    # ابحث عن المستخدم أو أنشئه إذا لم يكن موجوداً
    user, created = User.objects.get_or_create(username='zaid')
    user.set_password('zaid2025026"me') # ضع كلمة مرور قوية
    user.is_superuser = True
    user.is_staff = True
    user.save()
except Exception as e:
    print(f"Error: {e}")