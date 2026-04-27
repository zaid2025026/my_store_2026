from django.contrib import admin
from .models import Category, Product
from .models import Order, OrderItem
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)} # لجعل الرابط يتولد تلقائياً من الاسم

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'created', 'updated']
    list_filter = ['created', 'updated']
    list_editable = ['price', 'stock'] # لتعديل السعر والمخزون مباشرة من الجدول
    prepopulated_fields = {'slug': ('name',)}
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0 # لمنع ظهور حقول فارغة إضافية

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 1. الأعمدة التي ستظهر في الجدول الرئيسي
    # ملاحظة: تأكد أن 'first_name' و 'last_name' موجودة في الموديل الخاص بك
    list_display = ['id', 'first_name', 'last_name', 'status', 'paid', 'created', 'updated']
    
    # 2. جعل "حالة الطلب" و "حالة الدفع" قابلة للتعديل من الجدول مباشرة دون دخول الطلب
    list_editable = ['status', 'paid'] 
    
    # 3. إضافة فلاتر جانبية لتسهيل الوصول للطلبات (حسب الحالة، الدفع، والتاريخ)
    list_filter = ['status', 'paid', 'created', 'updated']
    
    # 4. إضافة خانة بحث سريعة بالاسم
    search_fields = ['first_name', 'last_name']
    
    # 5. ربط المنتجات بالطلب لعرضها في صفحة التفاصيل
    inlines = [OrderItemInline]
    
    # 6. ترتيب الطلبات بحيث يظهر الأحدث دائماً في الأعلى
    ordering = ['-created']

    # 7. إضافة "أكشن" سريع لتغيير حالة مجموعة طلبات معاً
    actions = ['mark_as_processing']
    # تحسين العرض في الشاشات الصغيرة
    list_per_page = 10

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "تحديث الطلبات المختارة إلى (جاري التجهيز)"