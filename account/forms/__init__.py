from django import forms
from django.contrib.auth.models import User
from ..models import Profile, Order, Platform, TechnicalProcess, Substrate


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_email(self):
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Email already in use.')
        return data


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        data = self.cleaned_data['email']
        qs = User.objects.exclude(id=self.instance.id) \
            .filter(email=data)
        if qs.exists():
            raise forms.ValidationError('Email already in use.')
        return data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['date_of_birth', 'photo']


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order

        exclude = [
            'order_number',
            'creator',
            'order_date',
            'deadline_date',
            'is_paid',
            'order_status',
            # 'technical_process',
            'order_type',
            'contract_file',
            'invoice_file',
            'deleted_at',
        ]

    diameter = forms.ModelChoiceField(queryset=Substrate.objects.filter())
    field_order = ['customer_product_name', 'mask_name', 'platform_code', 'technical_process', 'substrate', 'diameter',
                   'product_count', 'dc_rf_probing_e_map', 'dc_rf_probing_inking', 'visual_inspection_inking',
                   'dicing_method', 'tape_uv_support',
                   'wafer_deliver_format', 'multiplan_dicing_plan', 'package_servce', 'delivery_premium_template',
                   'delivery_premium_plate', 'special_note', 'GDS_file']

    def __init__(self, *args, **kwargs):
        super(OrderEditForm, self).__init__(*args, **kwargs)
        # print( self.fields.keys())
        # self.fields.insert(0,'diameter',forms.CharField(label="Димаетр подложки", max_length=100))

        super().__init__(*args, **kwargs)
        self.fields["technical_process"].queryset = TechnicalProcess.objects.none()
        self.fields["substrate"].queryset = Substrate.objects.none()
        self.fields["diameter"].queryset = Substrate.objects.none()
        self.fields["platform_code"].queryset = Platform.objects.all()
        if 'platform_code' in self.data:
            try:
                platform_id = int(self.data.get('platform_code'))
                self.fields['technical_process'].queryset = TechnicalProcess.objects.filter(platform_id=platform_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        if 'technical_process' in self.data:
            try:
                technical_process_id = int(self.data.get('technical_process'))
                self.fields['substrate'].queryset = Substrate.objects.filter(tech_proces_id=technical_process_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset
        if 'substrate' in self.data:
            try:
                substrate_id = int(self.data.get('substrate'))
                thikness = Substrate.objects.get(id=substrate_id).thikness
                self.fields['diameter'].queryset = Substrate.objects.filter(thikness=thikness)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty City queryset


class OrderEditingForm(forms.ModelForm):
    class Meta:
        model = Order
        
        fields = ['order_status', 'contract_file', 'invoice_file']
