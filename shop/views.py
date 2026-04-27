from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Category, Product, OrderItem
# التصحيح: الاستدعاء يكون من المجلد مباشرة وليس من التمبليت
from .cart.cart import Cart 
from .cart.forms import CartAddProductForm
from .forms import OrderCreateForm
import requests
def send_telegram_message(order_id, customer_name, phone, total_price):
    token = "8734187814:AAE66hJs4QEpEKszZqdeeUT13qZqEDhEbh0"
    chat_id = "335892547"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # رسالة واضحة ومنظمة مع إيموجي (بدون تنسيق معقد قد يسبب أخطاء)
    message = (
        f"🔔 طلب جديد - متجر زيد\n"
        f"---------------------------\n"
        f"📦 رقم الطلب: {order_id}\n"
        f"👤 العميل: {customer_name}\n"
        f"📱 الجوال: {phone}\n"
        f"💰 الإجمالي: {total_price} ريال\n"
        f"📊 الحالة: قيد الانتظار\n"
        f"---------------------------\n"
        f"✅ تم تسجيل الطلب بنجاح"
    )
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        # حذفنا الـ parse_mode لضمان وصول الرسالة دائماً مهما كان محتواها
    }
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"تم الإرسال بنجاح: {response.json()}")
    except Exception as e:
        print(f"خطأ في الإرسال: {e}")
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    # نمرر المخزون المتاح للفورم إذا أردت إظهاره
    cart_product_form = CartAddProductForm()
    return render(request, 'shop/product/detail.html', {
        'product': product,
        'cart_product_form': cart_product_form
    })

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={
            'quantity': item['quantity'],
            'override': True
        })
    return render(request, 'shop/cart/detail.html', {'cart': cart})

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                        product=item['product'],
                                        price=item['price'],
                                        quantity=item['quantity'])
                
                # تنقيص المخزون
                product = item['product']
                product.stock -= item['quantity']
                product.save() 
            
            # --- الإرسال هنا (تأكد من المحاذاة مع الـ for) ---
            try:
                # نستخدم getattr لتجنب توقف الكود إذا كان الحقل فارغاً أو باسم مختلف
                phone_number = getattr(order, 'phone', 'لم يتم إدخال رقم')
                full_name = f"{order.first_name} {order.last_name}"
                total_price = order.get_total_cost()
                
                print(f"جاري محاولة الإرسال للتلجرام: {full_name} - {phone_number}")
                
                send_telegram_message(
                    order_id=order.id, 
                    customer_name=full_name, 
                    phone=phone_number, 
                    total_price=total_price
                )
            except Exception as e:
                print(f"فشل استدعاء دالة التلجرام: {e}")
            
            cart.clear()
            return render(request, 'shop/order/created.html', {'order': order})
        else:
            print(f"خطأ في بيانات الفورم: {form.errors}") 
    else:
        form = OrderCreateForm()
    
    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})