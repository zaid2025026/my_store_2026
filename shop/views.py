import os

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Category, Product, OrderItem

# التصحيح: الاستدعاء يكون من المجلد مباشرة وليس من التمبليت
from .cart.cart import Cart
from .cart.forms import CartAddProductForm
from .forms import OrderCreateForm
import requests
import time


def send_telegram_message(order_id, customer_name, phone, total_price):
    # وضعنا القيم الصريحة مباشرة لكي يعمل الكود من جهازك الكمبيوتر فوراً
    token = "8621006684:AAF_T8KPXV_ZtVPQ6VK1D-e0E6pgJ_5Uw4A"
    chat_id = "-1001103603405"  # معرف قناتك الموثق والصحيح

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    message = (
        f"🔔 **طلب جديد - متجر زيد**\n"
        f"---------------------------\n"
        f"📦 **رقم الطلب:** {str(order_id)}\n"
        f"👤 **العميل:** {str(customer_name)}\n"
        f"📱 **الجوال:** {str(phone)}\n"
        f"💰 **الإجمالي:** {float(total_price):.2f} ريال\n"
        f"---------------------------\n"
        f"✅ تم تسجيل الطلب بنجاح"
    )

    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    for attempt in range(3):
        try:
            response = requests.post(url, data=payload, timeout=10)
            result = response.json()
            if result.get("ok"):
                print(f"✅ تم الإرسال بنجاح إلى القناة في المحاولة رقم {attempt + 1}")
                break
            else:
                print(f"❌ فشل الإرسال من طرف تيليجرام: {result.get('description')}")
        except Exception as e:
            print(f"⚠️ محاولة {attempt + 1} فشلت بسبب الشبكة: {e}")
            time.sleep(5)


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(
        request,
        "shop/product/list.html",
        {"category": category, "categories": categories, "products": products},
    )


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(
        request,
        "shop/product/detail.html",
        {"product": product, "cart_product_form": cart_product_form},
    )


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product=product, quantity=cd["quantity"], override_quantity=cd["override"]
        )
    return redirect("shop:cart_detail")


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={"quantity": item["quantity"], "override": True}
        )
    return render(request, "shop/cart/detail.html", {"cart": cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect("shop:cart_detail")


def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )

                # تنقيص المخزون لضمان دقة إدارة المستودع
                product = item["product"]
                product.stock -= item["quantity"]
                product.save()

            # --- عملية الإرسال لتيليجرام ---
            try:
                # جلب البيانات من كائن الطلب (order)
                phone_number = getattr(order, "phone", "لم يتم إدخال رقم")
                full_name = f"{order.first_name} {order.last_name}"
                total_price = order.get_total_cost()

                print(f"جاري إرسال إشعار الطلب للبوت الجديد: {full_name}")

                send_telegram_message(
                    order_id=order.id,
                    customer_name=full_name,
                    phone=phone_number,
                    total_price=total_price,
                )
            except Exception as e:
                print(f"فشل في استدعاء وظيفة الإرسال: {e}")

            cart.clear()
            return render(request, "shop/order/created.html", {"order": order})
        else:
            print(f"خطأ في بيانات الفورم: {form.errors}")
    else:
        form = OrderCreateForm()

    return render(request, "shop/order/create.html", {"cart": cart, "form": form})
