import os
import django

# إعداد بيئة Django مع اسم المجلد الصحيح my_store
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# تفاصيل الحساب الجديد الذي ستدخل به للوحة التحكم العالمية
username = "zaid_admin"
email = "zaid@example.com"
password = "ZaidPassword2026"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superuser created successfully!")
else:
    print("ℹ️ Superuser already exists.")
