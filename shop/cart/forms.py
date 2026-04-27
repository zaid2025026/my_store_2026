from django import forms

class CartAddProductForm(forms.Form):
    # جعل الكمية تبدأ من 1 وتتحدد برمجياً
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.HiddenInput # سنخفيه لجعل الإضافة "بضغطة زر واحدة"
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )