from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML

class CheckoutForm(forms.Form):
    # Billing Information
    billing_name = forms.CharField(max_length=100, label='Full Name')
    billing_email = forms.EmailField(label='Email')
    billing_phone = forms.CharField(max_length=20, label='Phone')
    billing_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address')
    billing_city = forms.CharField(max_length=100, label='City')
    billing_state = forms.CharField(max_length=100, label='State/Province')
    billing_zipcode = forms.CharField(max_length=20, label='ZIP/Postal Code')
    billing_country = forms.CharField(max_length=100, label='Country')
    
    # Shipping Information
    same_as_billing = forms.BooleanField(required=False, initial=True, label='Same as billing address')
    shipping_name = forms.CharField(max_length=100, label='Full Name', required=False)
    shipping_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address', required=False)
    shipping_city = forms.CharField(max_length=100, label='City', required=False)
    shipping_state = forms.CharField(max_length=100, label='State/Province', required=False)
    shipping_zipcode = forms.CharField(max_length=20, label='ZIP/Postal Code', required=False)
    shipping_country = forms.CharField(max_length=100, label='Country', required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h4>Billing Information</h4>'),
            Row(
                Column('billing_name', css_class='form-group col-md-6 mb-0'),
                Column('billing_email', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'billing_phone',
            'billing_address',
            Row(
                Column('billing_city', css_class='form-group col-md-4 mb-0'),
                Column('billing_state', css_class='form-group col-md-4 mb-0'),
                Column('billing_zipcode', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'billing_country',
            HTML('<hr><h4>Shipping Information</h4>'),
            'same_as_billing',
            Div(
                'shipping_name',
                'shipping_address',
                Row(
                    Column('shipping_city', css_class='form-group col-md-4 mb-0'),
                    Column('shipping_state', css_class='form-group col-md-4 mb-0'),
                    Column('shipping_zipcode', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                'shipping_country',
                css_id='shipping-fields'
            ),
            Submit('submit', 'Place Order', css_class='btn btn-success btn-lg btn-block mt-4')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        same_as_billing = cleaned_data.get('same_as_billing')
        
        if same_as_billing:
            # Copy billing info to shipping
            cleaned_data['shipping_name'] = cleaned_data.get('billing_name')
            cleaned_data['shipping_address'] = cleaned_data.get('billing_address')
            cleaned_data['shipping_city'] = cleaned_data.get('billing_city')
            cleaned_data['shipping_state'] = cleaned_data.get('billing_state')
            cleaned_data['shipping_zipcode'] = cleaned_data.get('billing_zipcode')
            cleaned_data['shipping_country'] = cleaned_data.get('billing_country')
        else:
            # Validate shipping fields are filled
            shipping_fields = ['shipping_name', 'shipping_address', 'shipping_city', 
                             'shipping_state', 'shipping_zipcode', 'shipping_country']
            for field in shipping_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required.')
        
        return cleaned_data