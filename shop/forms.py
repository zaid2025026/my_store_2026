from django import forms
from .models import Order  # تعديل المسار ليكون مباشر من نفس المجلد

class OrderCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control' # إضافة كلاس التنسيق لكل حقل

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'city']
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اللقب / العائلة',
            'email': 'البريد الإلكتروني',
            'address': 'العنوان بالتفصيل',
            'city': 'المدينة',
        }