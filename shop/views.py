from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from django.shortcuts import redirect
from .cart import Cart
from django.contrib import messages # لإظهار رسائل تنبيه للمستخدم
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
    return render(request, 'shop/product/detail.html', {'product': product})
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product)
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart/detail.html', {'cart': cart})
from .forms import OrderCreateForm
from .models import OrderItem
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:order_create') # سيعيد المستخدم لنفس صفحة الطلب بعد الحذف
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # فحص المخزون
            for item in cart:
                current_product = Product.objects.get(id=item['product'].id)
                if current_product.stock < item['quantity']:
                    messages.error(request, f" عذراً، الكمية من {current_product.name} غير كافية.")
                    # هنا نرجع Response في حالة وجود خطأ
                    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

            # حفظ الطلب
            order = form.save()
            for item in cart:
                p = Product.objects.get(id=item['product'].id)
                OrderItem.objects.create(order=order, product=p, price=item['price'], quantity=item['quantity'])
                p.stock -= item['quantity']
                p.save()
            
            cart.clear()
            # هنا نرجع Response في حالة النجاح
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        # هذه هي الحالة التي سببت الخطأ (حالة الـ GET)
        form = OrderCreateForm()
    
    # الحل هو نقل هذا السطر ليكون في نهاية الدالة تماماً لضمان وجود Response دائماً
    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})