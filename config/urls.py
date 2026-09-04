from django.contrib import admin
from django.urls import path, include, re_path  # أضفنا re_path هنا
from django.conf import settings
from django.views.static import serve  # أضفنا serve هنا لعرض الصور

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("shop.urls", namespace="shop")),
]

# كود لعرض ملفات الميديا (الصور) في كل الحالات (DEBUG و Production)
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]
