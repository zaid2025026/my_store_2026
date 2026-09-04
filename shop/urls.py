from django.urls import path

from . import views

app_name = "shop"


urlpatterns = [
    # ============================================================
    # السلة
    # ============================================================
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    # ============================================================
    # الطلب
    # ============================================================
    path("order/create/", views.order_create, name="order_create"),
    # تتبع الطلب
    path("order/track/", views.order_track, name="order_track"),
    # إلغاء الطلب من العميل
    path(
        "order/<int:order_id>/cancel/",
        views.customer_cancel_order,
        name="customer_cancel_order",
    ),
    # ============================================================
    # المنتجات
    # ============================================================
    path("", views.product_list, name="product_list"),
    # تصنيف المنتجات
    path("<slug:category_slug>/", views.product_list, name="product_list_by_category"),
    # تفاصيل المنتج
    path("<int:id>/<slug:slug>/", views.product_detail, name="product_detail"),
]
