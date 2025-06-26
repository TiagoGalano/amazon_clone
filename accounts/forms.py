from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

User = get_user_model()

#formulario de signup
class SignUpForm(UserCreationForm):
    #Campos apresentados, todos são necessários
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    # requerimentos
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        # init com os argumentos da classe pai
        super().__init__(*args, **kwargs)
        
        # django-crispy-forms implements a class called FormHelper that defines the form 
        # rendering behavior. Helpers give you a way to control form attributes and its layout, 
        # doing this in a programmatic way using Python. This way you write as little HTML as 
        # possible, and all your logic stays in the forms and views files.
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'username',
            'email',
            'password1',
            'password2',
            Submit('submit', 'Create Account', css_class='btn btn-primary btn-block')
        )

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Login', css_class='btn btn-primary btn-block')
        )

class ProfileForm(forms.ModelForm):
    #Requerimentos
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode', 'country']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'email',
            'phone',
            'address',
            Row(
                Column('city', css_class='form-group col-md-6 mb-0'),
                Column('state', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('zipcode', css_class='form-group col-md-6 mb-0'),
                Column('country', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Update Profile', css_class='btn btn-primary')
        )