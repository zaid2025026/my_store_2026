from django.db import models
from django.urls import reverse  # ضروري جداً لعمل الروابط
class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    # الدالة يجب أن تكون بمحاذاة الدوال الأخرى داخل الكلاس
    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return self.name

    # إضافة هذه الدالة للمنتج أيضاً لتسهيل الانتقال لصفحة التفاصيل
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class Order(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="الاسم الأول")
    last_name = models.CharField(max_length=50, verbose_name="الاسم الأخير")
    # تم استخدام رقم الجوال بدلاً من البريد الإلكتروني بناءً على طلبك
    phone = models.CharField(max_length=20, blank=False, null=False, verbose_name="رقم الجوال") 
    address = models.CharField(max_length=250, verbose_name="العنوان")
    city = models.CharField(max_length=100, verbose_name="المدينة")
    created = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    paid = models.BooleanField(default=False, verbose_name="تم الدفع")
    # خيارات حالة الطلب
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('processing', 'جاري التجهيز'),
        ('shipped', 'تم الشحن'),
        ('delivered', 'تم التسليم'),
        ('canceled', 'ملغي'),
    )

    # أضف هذا الحقل تحت الحقول الموجودة لديك
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="حالة الطلب"
    )

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"

    def __str__(self):
        return f'Order {self.id}'

    # دالة حساب إجمالي الفاتورة بالكامل
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, 
                              related_name='items', 
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product, 
                                related_name='order_items', 
                                on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, 
                                decimal_places=2, 
                                verbose_name="السعر عند الشراء")
    quantity = models.PositiveIntegerField(default=1, 
                                           verbose_name="الكمية")

    def __str__(self):
        return str(self.id)

    # الدالة الضرورية لحساب تكلفة الصنف الواحد (السعر × الكمية)
    def get_cost(self):
        return self.price * self.quantity