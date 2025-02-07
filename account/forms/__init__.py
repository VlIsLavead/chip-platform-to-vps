from django import forms
from django.contrib.auth.models import User
from ..models import Profile, Order, Platform, TechnicalProcess, Substrate, Thickness, Diameter, Message, Topic, File, RegistrationProfile


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = ['name', 'mail', 'number', 'company', 'processing_data']
        
        exclude = [
            'privacy_file'
        ]
        
        

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
        label='Техпроцесс',
        help_text='Технология, по которой будет изготовлен проект',
    )

    substrate_type = forms.ChoiceField(
        choices=Order.THICKNESS_TYPE_CHOICES,
        label='Тип подложки',
    )

    selected_thickness = forms.ModelChoiceField(
        queryset=Thickness.objects.none(),
        label='Толщина подложки, мкм'
    )

    selected_diameter = forms.ModelChoiceField(
        queryset=Diameter.objects.none(),
        label='Диаметр подложки, мм'
    )
    
    wafer_deliver_format = forms.ChoiceField(
        choices=Order.WaferDeliverFormat.choices,
        label='Вид поставки пластин',
        help_text='Выбор вида разделения пластины \
        на отдельные структуры перед отгрузкой, \
        либо его отсутсвие'
    )

    container_for_crystals = forms.ChoiceField(
        choices=[],
        label='Тара для кристаллов',
        help_text='Выбор тары, в которой будут \
        поставляться структуры после разделения пластины'
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
        
        for field_name, field in self.fields.items():
            if not field.help_text:
                field.help_text = None
                

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
            
        if 'wafer_deliver_format' in self.data:
            wafer_deliver_format = self.data.get('wafer_deliver_format')
            self._update_container_for_crystals_choices(wafer_deliver_format)
        elif self.instance.pk:
            wafer_deliver_format = self.instance.wafer_deliver_format
            self._update_container_for_crystals_choices(wafer_deliver_format)
            

    def clean(self):
        cleaned_data = super().clean()
        wafer_deliver_format = cleaned_data.get('wafer_deliver_format')

        if wafer_deliver_format:
            self._update_container_for_crystals_choices(wafer_deliver_format)

        return cleaned_data

    def _update_container_for_crystals_choices(self, wafer_deliver_format):
        if wafer_deliver_format == Order.WaferDeliverFormat.NotCut:
            self.fields['container_for_crystals'].choices = [
                (Order.ContainerForCrystals.СontainerForCrystalls, 'Тара для пластин'),
            ]
        elif wafer_deliver_format == Order.WaferDeliverFormat.Cut:
            self.fields['container_for_crystals'].choices = [
                (Order.ContainerForCrystals.PlasticCells, 'Пластмассовые ячейки'),
            ]
        elif wafer_deliver_format == Order.WaferDeliverFormat.Container:
            self.fields['container_for_crystals'].choices = [
                (Order.ContainerForCrystals.GelPack, 'Gel-Pak'),
            ]
        else:
            self.fields['container_for_crystals'].choices = []
            
            
            
class ViewOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        
        exclude = [
                'order_number',
                'creator',
            ]
        
        field_order = [
            'order_start', 'customer_product_name', 'technical_process',
            'platform_code', 'order_type', 'product_count',
            'formation_frame_by_customer', 'substrate_type', 'selected_thickness', 'selected_diameter',
            'experimental_structure', 'dc_rf_probing_e_map', 'dc_rf_probing_inking',
            'visual_inspection_inking', 'parametric_monitor_control', 'dicing_method', 'tape_uv_support',
            'wafer_deliver_format', 'container_for_crystals', 'multiplan_dicing_plan', 'multiplan_dicing_plan_file',
            'package_servce', 'delivery_premium_template', 'delivery_premium_plate', 'special_note', 'mask_name', 
            'order_date', 'deadline_date', 'is_paid', 'order_status', 'contract_file', 'invoice_file', 'deleted_at', 
            'GDS_file',
        ]
        
    def get_order_data(self, order):
        order_data = {
            'Тип заказа': order.get_order_start_display(),
            'Имя запуска': order.customer_product_name,
            'Номер шаблона': order.mask_name if order.mask_name else "Не указан",
            'Техпроцесс': order.technical_process.name_process if order.technical_process else "Не указано",
            'Производственная площадка': order.platform_code.platform_code if order.platform_code else "Не указана",
            'Тип запуска': order.get_order_type_display(),
            'Число проектов в кадре': order.product_count,
            'Формирование кадра заказчиком': "Да" if order.formation_frame_by_customer else "Нет",
            'Тип толщины подложки': order.get_substrate_type_display(),
            'Толщина': str(order.selected_thickness) if order.selected_thickness else "Не указана",
            'Диаметр': str(order.selected_diameter) if order.selected_diameter else "Не указан",
            'Экспериментальная структура': "Да" if order.experimental_structure else "Нет",
            'Контроль электрических параметров на пластине': order.get_dc_rf_probing_e_map_display(),
            'Маркировка брака по электрическим параметрам': "Да" if order.dc_rf_probing_inking else "Нет",
            'Визуальный контроль и маркировка брака': "Да" if order.visual_inspection_inking else "Нет",
            'Предоставление данных контроля параметрического монитора': "Да" if order.parametric_monitor_control else "Нет",
            'Способ разделения пластины на кристаллы': order.get_dicing_method_display(),
            'УФ засветка полимерного носителя': "Да" if order.tape_uv_support else "Нет",
            'Вид поставки пластин': order.get_wafer_deliver_format_display(),
            'Вид тары для кристаллов': order.get_container_for_crystals_display(),
            'Разделение пластины на кристаллы по схеме заказчика': "Да" if order.multiplan_dicing_plan else "Нет",
            'Разделение пластины на кристаллы по схеме заказчика(Файл)': order.multiplan_dicing_plan_file.url if order.multiplan_dicing_plan_file else "Нет файла",
            'Корпусирование силами производителя': "Да" if order.package_servce else "Нет",
            'Ускоренный запуск производства фотошаблонов': "Да" if order.delivery_premium_template else "Нет",
            'Ускоренный запуск производства пластин': "Да" if order.delivery_premium_plate else "Нет",
            'Заметка': order.special_note if order.special_note else "Нет заметки",
            'Дата оплаты': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else "Не указана",
            'Срок выполнения по договору': order.deadline_date.strftime('%Y-%m-%d %H:%M:%S') if order.deadline_date else "Не указана",
            'Заказ оплачен?': "Да" if order.is_paid else "Нет",
            'Статус заказа': order.get_order_status_display(),
            'Файл договора': order.contract_file.url if order.contract_file else "Нет файла",
            'Файл счета': order.invoice_file.url if order.invoice_file else "Нет файла",
            'Файл GDS': order.GDS_file.url if order.GDS_file else "Нет файла",
        }
        
        order_items = [(field, value) for field, value in order_data.items()]
        return order_items
    

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


class EditPaidForm(forms.ModelForm):
    class Meta:
        model = Order
        
        fields = ['contract_file', 'invoice_file']


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
