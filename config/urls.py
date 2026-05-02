from django.contrib import admin
from django.urls import path, include, re_path # أضفنا re_path هنا
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # أضفنا serve هنا لعرض الصور
from django.contrib.auth.models import User

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls', namespace='shop')),
]

# كود لعرض ملفات الميديا (الصور) في كل الحالات (DEBUG و Production)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

# كود مؤقت لإنشاء/تحديث المستخدم (احذفه بعد نجاح الدخول)
try:
    user, created = User.objects.get_or_create(username='zaid')
    user.set_password('zaid2025026"me')
    user.is_superuser = True
    user.is_staff = True
    user.save()
except Exception as e:
    pass