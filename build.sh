#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. تثبيت المكتبات البرمجية للمشروع
pip install -r requirements.txt

# 2. تجميع ملفات الستاتيك (الصور والتنسيقات)
python manage.py collectstatic --no-input

# 3. تطبيق هجرات قواعد البيانات
python manage.py migrate

# 4. السكريبت العبقري لإنشاء حساب المسؤول تلقائياً
python createsuperuser.py