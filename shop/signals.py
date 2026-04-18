from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def send_telegram_notification(sender, instance, created, **kwargs):
    # نرسل الإشعار في حالتين: إذا كان الطلب جديداً، أو إذا تم تحديثه ليصبح "مدفوعاً"
    if created or instance.paid:
        status = "مدفوع" if instance.paid else "قيد الانتظار"
        print(f"--- تنبيه تليجرام ---")
        print(f"طلب جديد رقم: {instance.id}")
        print(f"العميل: {instance.first_name} {instance.last_name}")
        print(f"الحالة: {status}")
        # هنا سنربط لاحقاً مكتبة Telethon الخاصة بك