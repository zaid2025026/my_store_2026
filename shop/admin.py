from django.contrib import admin
from .models import Category, Product

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
