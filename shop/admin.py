from django.contrib import admin, messages
from django.db import transaction

from .models import Category, Product, Order, OrderItem, DeliveryZone


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "price",
        "stock",
        "available",
        "created",
        "updated",
    ]

    list_filter = [
        "available",
        "created",
        "updated",
    ]

    list_editable = [
        "price",
        "stock",
        "available",
    ]

    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]
    extra = 0


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = [
        "city",
        "fee",
        "active",
    ]

    list_filter = [
        "active",
    ]

    search_fields = [
        "city",
    ]

    list_editable = [
        "fee",
        "active",
    ]

    ordering = [
        "city",
    ]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "first_name",
        "last_name",
        "status",
        "paid",
        "created",
        "updated",
    ]

    list_filter = [
        "status",
        "paid",
        "created",
        "updated",
    ]

    search_fields = [
        "first_name",
        "last_name",
        "phone",
    ]

    inlines = [OrderItemInline]

    ordering = ["-created"]

    list_per_page = 10

    actions = [
        "mark_as_processing",
        "mark_as_canceled",
    ]

    def save_model(self, request, obj, form, change):
        """
        نحفظ الحالة القديمة قبل تغييرها.
        """
        if change:
            old_order = Order.objects.get(pk=obj.pk)
            obj._old_status = old_order.status
        else:
            obj._old_status = None

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        """
        تتم معالجة المخزون بعد حفظ OrderItems.
        """

        # حفظ عناصر الطلب أولاً
        super().save_related(
            request,
            form,
            formsets,
            change,
        )

        order = form.instance
        old_status = getattr(
            order,
            "_old_status",
            None,
        )

        # ==================================================
        # 1. طلب جديد من لوحة الإدارة
        # ==================================================

        if not change:

            # إذا لم يكن ملغياً، نخصم المخزون
            if order.status != "canceled":

                for item in order.items.select_related("product"):

                    product = Product.objects.select_for_update().get(
                        pk=item.product_id
                    )

                    if product.stock < item.quantity:
                        raise ValueError(f"المخزون غير كافٍ للمنتج: {product.name}")

                    product.stock -= item.quantity

                    # لا نجعل المنتج مختفياً من المتجر
                    # فقط نضبط available حسب المخزون
                    product.available = product.stock > 0

                    product.save(
                        update_fields=[
                            "stock",
                            "available",
                        ]
                    )

            return

        # ==================================================
        # 2. تحويل طلب موجود إلى ملغي
        # ==================================================

        if old_status != "canceled" and order.status == "canceled":

            for item in order.items.select_related("product"):

                product = Product.objects.select_for_update().get(pk=item.product_id)

                product.stock += item.quantity

                # إذا عاد المخزون، المنتج يصبح متاحاً
                if product.stock > 0:
                    product.available = True

                product.save(
                    update_fields=[
                        "stock",
                        "available",
                    ]
                )

            return

        # ==================================================
        # 3. إعادة طلب ملغي إلى حالة نشطة
        # ==================================================

        if old_status == "canceled" and order.status != "canceled":

            for item in order.items.select_related("product"):

                product = Product.objects.select_for_update().get(pk=item.product_id)

                if product.stock < item.quantity:
                    raise ValueError(
                        f"المخزون غير كافٍ لإعادة تفعيل الطلب "
                        f"للمنتج: {product.name}"
                    )

                product.stock -= item.quantity

                product.available = product.stock > 0

                product.save(
                    update_fields=[
                        "stock",
                        "available",
                    ]
                )

    # ======================================================
    # Action: تحويل إلى جاري التجهيز
    # ======================================================

    @admin.action(description="تحديث الطلبات المختارة إلى (جاري التجهيز)")
    def mark_as_processing(
        self,
        request,
        queryset,
    ):

        queryset.exclude(status="canceled").update(status="processing")

        self.message_user(
            request,
            "تم تحديث حالة الطلبات إلى جاري التجهيز.",
            messages.SUCCESS,
        )

    # ======================================================
    # Action: إلغاء الطلبات وإعادة المخزون
    # ======================================================

    @admin.action(description="إلغاء الطلبات المختارة وإعادة المخزون")
    @transaction.atomic
    def mark_as_canceled(
        self,
        request,
        queryset,
    ):

        orders = queryset.exclude(status="canceled")

        canceled_count = 0

        for order in orders:

            for item in order.items.select_related("product"):

                product = Product.objects.select_for_update().get(pk=item.product_id)

                product.stock += item.quantity

                if product.stock > 0:
                    product.available = True

                product.save(
                    update_fields=[
                        "stock",
                        "available",
                    ]
                )

            order.status = "canceled"

            order.save(
                update_fields=[
                    "status",
                    "updated",
                ]
            )

            canceled_count += 1

        self.message_user(
            request,
            f"تم إلغاء {canceled_count} طلب وإعادة المخزون بنجاح.",
            messages.SUCCESS,
        )
