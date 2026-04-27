from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # نحن هنا نخبر جانجو أن أي رابط يبدأ بـ 'cart/' أو 'order/' أو فارغ ''
    # سيذهب للبحث عنه في ملف shop/urls.py
    path('', include('shop.urls', namespace='shop')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)