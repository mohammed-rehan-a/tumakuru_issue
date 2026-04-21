from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CitizenProfile


class CitizenRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=15, required=True,
        widget=forms.TextInput(attrs={'placeholder': '10-digit Mobile Number'}))
    ward_number = forms.ChoiceField(choices=[('', 'Select Ward')] + [(str(i), f"Ward {i}") for i in range(1, 36)])
    address = forms.CharField(required=True,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Residential Address in Tumakuru'}))
    aadhaar_last4 = forms.CharField(max_length=4, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last 4 digits of Aadhaar (optional)'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Choose a Username'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data['phone']
            profile.ward_number = self.cleaned_data['ward_number']
            profile.address = self.cleaned_data['address']
            profile.aadhaar_last4 = self.cleaned_data.get('aadhaar_last4', '')
            profile.save()
        return user


class CitizenLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()

    class Meta:
        model = CitizenProfile
        fields = ['phone', 'ward_number', 'address', 'profile_photo', 'bio']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
