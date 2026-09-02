import time
import logging

import requests

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect

from .models import Category, Product, OrderItem
from .cart.cart import Cart
from .cart.forms import CartAddProductForm
from .forms import OrderCreateForm

logger = logging.getLogger(__name__)


def send_telegram_message(order_id, customer_name, phone, total_price):
    """
    إرسال إشعار بالطلب إلى تيليجرام.
    التوكن و Chat ID يتم قراءتهما من settings.py
    """

    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        logger.warning("Telegram settings are not configured.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    message = (
        f"🔔 *طلب جديد - متجر زيد*\n"
        f"---------------------------\n"
        f"📦 *رقم الطلب:* {order_id}\n"
        f"👤 *العميل:* {customer_name}\n"
        f"📱 *الجوال:* {phone}\n"
        f"💰 *الإجمالي:* {float(total_price):.2f} ريال\n"
        f"---------------------------\n"
        f"✅ تم تسجيل الطلب بنجاح"
    )

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    for attempt in range(3):
        try:
            response = requests.post(
                url,
                data=payload,
                timeout=10,
            )

            result = response.json()

            if result.get("ok"):
                logger.info(
                    "Telegram notification sent successfully for order %s",
                    order_id,
                )
                return True

            logger.warning(
                "Telegram error for order %s: %s",
                order_id,
                result.get("description"),
            )

        except Exception as exc:
            logger.warning(
                "Telegram attempt %s failed for order %s: %s",
                attempt + 1,
                order_id,
                exc,
            )

            if attempt < 2:
                time.sleep(2)

    return False


def product_list(request, category_slug=None):
    category = None

    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug,
        )
        products = products.filter(category=category)

    return render(
        request,
        "shop/product/list.html",
        {
            "category": category,
            "categories": categories,
            "products": products,
        },
    )


def product_detail(request, id, slug):
    product = get_object_or_404(
        Product,
        id=id,
        slug=slug,
        available=True,
    )

    cart_product_form = CartAddProductForm()

    return render(
        request,
        "shop/product/detail.html",
        {
            "product": product,
            "cart_product_form": cart_product_form,
        },
    )


def cart_add(request, product_id):
    if request.method != "POST":
        return redirect("shop:cart_detail")

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
        available=True,
    )

    form = CartAddProductForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        override = form.cleaned_data["override"]

        # منع تجاوز المخزون عند إضافة المنتج للسلة
        current_quantity = cart.cart.get(str(product.id), {}).get("quantity", 0)

        new_quantity = quantity if override else current_quantity + quantity

        if new_quantity > product.stock:
            messages.error(
                request,
                f"الكمية المطلوبة غير متوفرة. المتوفر حالياً: {product.stock}",
            )
            return redirect(product.get_absolute_url())

        if new_quantity <= 0:
            messages.error(
                request,
                "الكمية يجب أن تكون أكبر من صفر.",
            )
            return redirect(product.get_absolute_url())

        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=override,
        )

    return redirect("shop:cart_detail")


def cart_detail(request):
    cart = Cart(request)

    for item in cart:
        item["update_quantity_form"] = CartAddProductForm(
            initial={
                "quantity": item["quantity"],
                "override": True,
            }
        )

    return render(
        request,
        "shop/cart/detail.html",
        {"cart": cart},
    )


def cart_remove(request, product_id):
    if request.method != "POST":
        return redirect("shop:cart_detail")

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart.remove(product)

    return redirect("shop:cart_detail")


@transaction.atomic
def order_create(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.warning(
            request,
            "السلة فارغة، أضف منتجات أولاً.",
        )
        return redirect("shop:product_list")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():

            # إعادة جلب المنتجات من قاعدة البيانات
            # داخل المعاملة للتأكد من المخزون الحالي.
            product_ids = [item["product"].id for item in cart]

            products = Product.objects.select_for_update().filter(id__in=product_ids)

            products_by_id = {product.id: product for product in products}

            # التحقق من المخزون قبل إنشاء الطلب
            for item in cart:
                product = products_by_id.get(item["product"].id)

                if not product:
                    messages.error(
                        request,
                        "أحد المنتجات لم يعد متاحاً.",
                    )
                    return redirect("shop:cart_detail")

                if not product.available:
                    messages.error(
                        request,
                        f"المنتج «{product.name}» لم يعد متاحاً.",
                    )
                    return redirect("shop:cart_detail")

                if item["quantity"] > product.stock:
                    messages.error(
                        request,
                        (
                            f"المنتج «{product.name}» "
                            f"المتوفر منه {product.stock} فقط."
                        ),
                    )
                    return redirect("shop:cart_detail")

            # إنشاء الطلب
            order = form.save()

            # إنشاء تفاصيل الطلب + خصم المخزون
            for item in cart:
                product = products_by_id[item["product"].id]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=item["quantity"],
                )

                product.stock -= item["quantity"]

                if product.stock == 0:
                    product.available = False

                product.save(
                    update_fields=[
                        "stock",
                        "available",
                    ]
                )

            # إرسال إشعار تيليجرام
            try:
                full_name = f"{order.first_name} {order.last_name}"
                total_price = order.get_total_cost()

                send_telegram_message(
                    order_id=order.id,
                    customer_name=full_name,
                    phone=order.phone,
                    total_price=total_price,
                )

            except Exception:
                logger.exception(
                    "Failed to send Telegram notification for order %s",
                    order.id,
                )

            # تفريغ السلة بعد نجاح العملية
            cart.clear()

            return render(
                request,
                "shop/order/created.html",
                {"order": order},
            )

        logger.warning(
            "Order form validation failed: %s",
            form.errors,
        )

    else:
        form = OrderCreateForm()

    return render(
        request,
        "shop/order/create.html",
        {
            "cart": cart,
            "form": form,
        },
    )
