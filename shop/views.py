from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Category, Product, OrderItem
from shop.cart.cart import Cart 
from shop.cart.forms import CartAddProductForm
from .forms import OrderCreateForm# التأكد أن الملف هو shop/forms.py

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
    return redirect('shop:cart_detail') # العودة للسلة وليس لصفحة الطلب

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # فحص المخزون
            for item in cart:
                current_product = Product.objects.get(id=item['product'].id)
                if current_product.stock < item['quantity']:
                    messages.error(request, f"عذراً، الكمية من {current_product.name} غير كافية.")
                    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

            # حفظ الطلب وتحديث المخزون
            order = form.save()
            for item in cart:
                p = Product.objects.get(id=item['product'].id)
                OrderItem.objects.create(order=order, product=p, price=item['price'], quantity=item['quantity'])
                p.stock -= item['quantity']
                p.save()

            cart.clear()
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()

    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})