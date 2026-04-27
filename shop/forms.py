from django import forms  # هذا السطر الناقص هو سبب المشكلة
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        # تأكد من حذف 'email' من هذه القائمة نهائياً
        fields = ['first_name', 'last_name', 'phone', 'address', 'city'] 
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اللقب',
            'phone': 'رقم الجوال',
            'address': 'العنوان',
            'city': 'المدينة',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control rounded-pill',
                'required': 'required' # هذا سيحل مشكلة "التنبيه عند ترك الحقل فارغاً"
            })