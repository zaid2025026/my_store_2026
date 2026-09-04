import time
import logging

import requests

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect

from .models import Category, Product, Order, OrderItem
from .cart.cart import Cart
from .cart.forms import CartAddProductForm
from .forms import OrderCreateForm

logger = logging.getLogger(__name__)


# ============================================================
# Telegram - طلب جديد
# ============================================================


def send_telegram_message(
    order_id,
    customer_name,
    phone,
    total_price,
):
    """
    إرسال إشعار بالطلب الجديد إلى Telegram.
    """

    token = getattr(
        settings,
        "TELEGRAM_BOT_TOKEN",
        "",
    )

    chat_id = getattr(
        settings,
        "TELEGRAM_CHAT_ID",
        "",
    )

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
                    "Telegram notification sent successfully " "for order %s",
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


# ============================================================
# Telegram - إلغاء طلب
# ============================================================


def send_telegram_cancel_message(
    order_id,
    customer_name,
    phone,
    total_price,
):
    """
    إرسال إشعار بإلغاء الطلب إلى Telegram.
    """

    token = getattr(
        settings,
        "TELEGRAM_BOT_TOKEN",
        "",
    )

    chat_id = getattr(
        settings,
        "TELEGRAM_CHAT_ID",
        "",
    )

    if not token or not chat_id:
        logger.warning("Telegram settings are not configured.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    message = (
        f"❌ *إلغاء طلب - متجر زيد*\n"
        f"---------------------------\n"
        f"📦 *رقم الطلب:* {order_id}\n"
        f"👤 *العميل:* {customer_name}\n"
        f"📱 *الجوال:* {phone}\n"
        f"💰 *الإجمالي:* {float(total_price):.2f} ريال\n"
        f"---------------------------\n"
        f"⚠️ تم إلغاء الطلب وإعادة المخزون"
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
                    "Telegram cancellation notification "
                    "sent successfully for order %s",
                    order_id,
                )
                return True

            logger.warning(
                "Telegram cancellation error for order %s: %s",
                order_id,
                result.get("description"),
            )

        except Exception as exc:
            logger.warning(
                "Telegram cancellation attempt %s failed " "for order %s: %s",
                attempt + 1,
                order_id,
                exc,
            )

            if attempt < 2:
                time.sleep(2)

    return False


# ============================================================
# المنتجات
# ============================================================


def product_list(request, category_slug=None):
    """
    عرض جميع المنتجات، بما فيها المنتجات التي نفد مخزونها.
    """

    category = None

    categories = Category.objects.all()

    products = Product.objects.all()

    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug,
        )

        products = products.filter(
            category=category,
        )

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
    """
    عرض تفاصيل المنتج حتى لو كان المخزون = 0.
    """

    product = get_object_or_404(
        Product,
        id=id,
        slug=slug,
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


# ============================================================
# السلة
# ============================================================


def cart_add(request, product_id):
    """
    إضافة منتج إلى السلة مع التحقق من المخزون.
    """

    if request.method != "POST":
        return redirect("shop:cart_detail")

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    if not product.available or product.stock <= 0:
        messages.error(
            request,
            f"المنتج «{product.name}» نفدت كميته.",
        )

        return redirect(product.get_absolute_url())

    cart = Cart(request)

    form = CartAddProductForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]

        override = form.cleaned_data["override"]

        current_quantity = cart.cart.get(str(product.id), {}).get("quantity", 0)

        new_quantity = quantity if override else current_quantity + quantity

        if new_quantity <= 0:
            messages.error(
                request,
                "الكمية يجب أن تكون أكبر من صفر.",
            )

            return redirect(product.get_absolute_url())

        if new_quantity > product.stock:
            messages.error(
                request,
                (f"الكمية المطلوبة غير متوفرة. " f"المتوفر حالياً: {product.stock}"),
            )

            return redirect(product.get_absolute_url())

        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=override,
        )

    return redirect("shop:cart_detail")


def cart_detail(request):
    """
    عرض السلة.
    """

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
        {
            "cart": cart,
        },
    )


def cart_remove(request, product_id):
    """
    حذف منتج من السلة.
    """

    if request.method != "POST":
        return redirect("shop:cart_detail")

    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id,
    )

    cart.remove(product)

    return redirect("shop:cart_detail")


# ============================================================
# إنشاء الطلب
# ============================================================


@transaction.atomic
def order_create(request):
    """
    إنشاء الطلب وخصم المخزون بشكل آمن داخل Transaction.
    """

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
                        f"المنتج «{product.name}» " f"لم يعد متاحاً.",
                    )

                    return redirect("shop:cart_detail")

                if item["quantity"] > product.stock:
                    messages.error(
                        request,
                        (
                            f"المنتج «{product.name}» "
                            f"المتوفر منه "
                            f"{product.stock} فقط."
                        ),
                    )

                    return redirect("shop:cart_detail")

            # إنشاء الطلب
            order = form.save()

            # إنشاء عناصر الطلب وخصم المخزون
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

            # إرسال إشعار Telegram
            try:
                full_name = f"{order.first_name} " f"{order.last_name}"

                total_price = order.get_total_cost()

                send_telegram_message(
                    order_id=order.id,
                    customer_name=full_name,
                    phone=order.phone,
                    total_price=total_price,
                )

            except Exception:
                logger.exception(
                    "Failed to send Telegram notification " f"for order {order.id}",
                )

            # تفريغ السلة
            cart.clear()

            # عرض الفاتورة
            return render(
                request,
                "shop/order/created.html",
                {
                    "order": order,
                },
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


# ============================================================
# تتبع الطلب
# ============================================================


def order_track(request):
    """
    تتبع الطلب للعميل.

    السلوك:
    - ?new=1 يبدأ عملية تتبع جديدة ويمسح بيانات التتبع فقط.
    - POST يتحقق من رقم الطلب ورمز المتابعة ويحفظهما في Session.
    - بعد نجاح البحث يتم Redirect إلى GET لمنع إعادة إرسال النموذج عند Refresh.
    - Refresh يعرض آخر طلب تم التحقق منه.
    - فتح صفحة التتبع مباشرة يحافظ على الطلب الموجود في Session.
    - لا يتم المساس بالسلة أو أي بيانات Session أخرى.
    """

    # =========================================================
    # 1) بدء تتبع جديد
    # =========================================================
    if request.method == "GET" and request.GET.get("new") == "1":
        request.session.pop("tracked_order_id", None)
        request.session.pop("tracked_order_code", None)
        request.session.modified = True

        return render(
            request,
            "shop/order/track.html",
            {"order": None},
        )

    # =========================================================
    # 2) البحث عن الطلب
    # =========================================================
    if request.method == "POST":
        order_id = request.POST.get("order_id", "").strip()
        tracking_code = request.POST.get("tracking_code", "").strip()

        if not order_id or not tracking_code:
            messages.error(
                request,
                "يرجى إدخال رقم الطلب ورمز المتابعة.",
            )

            return render(
                request,
                "shop/order/track.html",
                {"order": None},
            )

        try:
            order = Order.objects.prefetch_related("items__product").get(
                id=order_id,
                tracking_code=tracking_code,
            )

        except (Order.DoesNotExist, ValueError):
            messages.error(
                request,
                "بيانات الطلب غير صحيحة.",
            )

            return render(
                request,
                "shop/order/track.html",
                {"order": None},
            )

        # =====================================================
        # حفظ الطلب الذي تم التحقق منه في Session
        # =====================================================
        request.session["tracked_order_id"] = order.id
        request.session["tracked_order_code"] = order.tracking_code
        request.session.modified = True

        # =====================================================
        # POST → Redirect → GET
        #
        # يمنع مشكلة إعادة إرسال POST عند تحديث الصفحة.
        # الطلب سيُسترجع من Session في طلب GET التالي.
        # =====================================================
        return redirect("shop:order_track")

    # =========================================================
    # 3) GET عادي / Refresh
    # =========================================================
    order = None

    tracked_order_id = request.session.get("tracked_order_id")
    tracked_order_code = request.session.get("tracked_order_code")

    if tracked_order_id and tracked_order_code:
        try:
            order = (
                Order.objects.prefetch_related("items__product")
                .filter(
                    id=int(tracked_order_id),
                    tracking_code=tracked_order_code,
                )
                .first()
            )

        except (TypeError, ValueError):
            order = None

        # =====================================================
        # إذا أصبحت بيانات Session غير صالحة
        # =====================================================
        if order is None:
            request.session.pop("tracked_order_id", None)
            request.session.pop("tracked_order_code", None)
            request.session.modified = True

    # =========================================================
    # 4) عرض صفحة التتبع
    # =========================================================
    return render(
        request,
        "shop/order/track.html",
        {"order": order},
    )


# ============================================================
# إلغاء الطلب من العميل
# ============================================================


@transaction.atomic
def customer_cancel_order(request, order_id):
    """
    إلغاء الطلب من العميل.

    مسموح فقط إذا كانت حالة الطلب:
    pending

    عند الإلغاء:
    - إعادة المخزون
    - تغيير الحالة إلى canceled
    - إرسال إشعار Telegram
    - حذف الطلب المتتبع من الجلسة
    """

    if request.method != "POST":
        return redirect("shop:order_track")

    # التحقق من الطلب الموجود في جلسة العميل
    tracked_order_id = request.session.get("tracked_order_id")

    tracked_order_code = request.session.get("tracked_order_code")

    if (
        not tracked_order_id
        or not tracked_order_code
        or int(tracked_order_id) != int(order_id)
    ):
        messages.error(
            request,
            "لا يمكن تنفيذ هذا الإجراء.",
        )

        return redirect("shop:order_track")

    # قفل الطلب لمنع عمليات متزامنة
    order = get_object_or_404(
        Order.objects.select_for_update(),
        id=order_id,
        tracking_code=tracked_order_code,
    )

    # الإلغاء مسموح فقط للطلبات قيد الانتظار
    if order.status != "pending":

        messages.error(
            request,
            (
                "لا يمكن إلغاء الطلب الآن. "
                "يمكن إلغاء الطلب فقط عندما تكون حالته "
                "قيد الانتظار."
            ),
        )

        return redirect("shop:order_track")

    # إعادة المخزون
    for item in order.items.select_related("product"):

        product = Product.objects.select_for_update().get(pk=item.product_id)

        product.stock += item.quantity

        # بعد إعادة المخزون يصبح المنتج متاحاً
        product.available = True

        product.save(
            update_fields=[
                "stock",
                "available",
            ]
        )

    # تغيير حالة الطلب
    order.status = "canceled"

    order.save(
        update_fields=[
            "status",
            "updated",
        ]
    )

    # إرسال إشعار الإلغاء إلى Telegram
    try:
        full_name = f"{order.first_name} " f"{order.last_name}"

        total_price = order.get_total_cost()

        send_telegram_cancel_message(
            order_id=order.id,
            customer_name=full_name,
            phone=order.phone,
            total_price=total_price,
        )

    except Exception:
        logger.exception(
            "Failed to send Telegram cancellation "
            f"notification for order {order.id}",
        )

    # إزالة الطلب من جلسة التتبع
    request.session.pop(
        "tracked_order_id",
        None,
    )

    request.session.pop(
        "tracked_order_code",
        None,
    )

    request.session.modified = True

    messages.success(
        request,
        (f"تم إلغاء الطلب رقم {order.id} " "بنجاح وتمت إعادة المنتجات إلى المخزون."),
    )

    return redirect("shop:order_track")
