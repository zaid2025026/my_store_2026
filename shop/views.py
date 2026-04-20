from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Category, Product, OrderItem
# التصحيح: الاستدعاء يكون من المجلد مباشرة وليس من التمبليت
from .cart.cart import Cart 
from .cart.forms import CartAddProductForm
from .forms import OrderCreateForm

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
    # إضافة فورم الكمية هنا ليعمل زر "إضافة للسلة" في صفحة التفاصيل
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
            # فحص المخزون
            for item in cart:
                current_product = item['product'] # الكارت غالباً يعيد الكائن مباشرة
                if current_product.stock < item['quantity']:
                    messages.error(request, f"عذراً، الكمية من {current_product.name} غير كافية.")
                    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

            # حفظ الطلب وتحديث المخزون
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, 
                                        product=item['product'], 
                                        price=item['price'], 
                                        quantity=item['quantity'])
                p = item['product']
                p.stock -= item['quantity']
                p.save()

            cart.clear()
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()

    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})