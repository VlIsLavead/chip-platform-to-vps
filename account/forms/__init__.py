from django import forms
from django.contrib.auth.models import User
from ..models import Profile, Order, Platform, TechnicalProcess, Substrate, Thickness, Diameter, Message, Topic, File


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


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
        fields = ['date_of_birth']


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = [
            'mask_name',
            'order_number',
            'creator',
            'order_date',
            'deadline_date',
            'is_paid',
            'order_status',
            'contract_file',
            'invoice_file',
            'deleted_at',
            'GDS_file',
        ]

    technical_process = forms.ModelChoiceField(
        queryset=TechnicalProcess.objects.none(),
        label='Техпроцесс'
    )

    substrate_type = forms.ChoiceField(
        choices=Order.THICKNESS_TYPE_CHOICES,
        label='Тип подложки'
    )

    selected_thickness = forms.ModelChoiceField(
        queryset=Thickness.objects.none(),
        label='Толщина'
    )

    selected_diameter = forms.ModelChoiceField(
        queryset=Diameter.objects.none(),
        label='Диаметр'
    )

    field_order = [
        'order_start', 'customer_product_name', 'technical_process',
        'platform_code', 'order_type', 'product_count',
        'formation_frame_by_customer', 'substrate_type', 'selected_thickness', 'selected_diameter',
        'experimental_structure', 'dc_rf_probing_e_map', 'dc_rf_probing_inking',
        'visual_inspection_inking', 'parametric_monitor_control', 'dicing_method', 'tape_uv_support',
        'wafer_deliver_format', 'container_for_crystals', 'multiplan_dicing_plan', 'multiplan_dicing_plan_file',
        'package_servce', 'delivery_premium_template', 'delivery_premium_plate', 'special_note',
    ]

    widgets = {
        'special_note': forms.Textarea(attrs={
            'rows': 4,
            'cols': 50,
            'style': 'resize: vertical;',
        }),
    }

    def __init__(self, *args, **kwargs):
        super(OrderEditForm, self).__init__(*args, **kwargs)

        self.fields['selected_thickness'].queryset = Thickness.objects.none()
        self.fields['selected_diameter'].queryset = Diameter.objects.none()
        self.fields['technical_process'].queryset = TechnicalProcess.objects.all()
        self.fields['platform_code'].queryset = Platform.objects.all()

        if 'platform_code' in self.data:
            try:
                platform_id = int(self.data.get('platform_code'))
                self.fields['technical_process'].queryset = TechnicalProcess.objects.filter(platform_id=platform_id)
            except (ValueError, TypeError):
                pass

        if 'substrate_type' in self.data:
            try:
                substrate_type = self.data.get('substrate_type')
                self.fields['selected_thickness'].queryset = Thickness.objects.filter(type=substrate_type)

                self.fields['selected_diameter'].queryset = Diameter.objects.filter(type=substrate_type)
            except (ValueError, TypeError):
                pass

        elif self.instance.pk:
            self.fields['selected_thickness'].queryset = Thickness.objects.filter(type=self.instance.substrate_type)
            self.fields['selected_diameter'].queryset = Diameter.objects.filter(type=self.instance.substrate_type)
            
            

class OrderEditingForm(forms.ModelForm):
    class Meta:
        model = Order

        fields = ['mask_name']


class EditPlatform(forms.ModelForm):
    class Meta:
        model = Platform

        fields = ['platform_name', 'platform_code']


class AddGDSFile(forms.ModelForm):
    class Meta:
        model = Order

        fields = ['GDS_file']


class MessageForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите ваше сообщение...'}))

    class Meta:
        model = Message
        fields = ['text']


class FileForm(forms.ModelForm):
    file = forms.FileField(required=False)

    class Meta:
        model = File
        fields = ['file']


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'is_private', 'related_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Введите название темы'}),
            'is_private': forms.CheckboxInput(),
            'related_order': forms.Select(),
        }
