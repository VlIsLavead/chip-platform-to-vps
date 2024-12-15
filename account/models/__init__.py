from django.db import models
from django.conf import settings
from datetime import datetime
from django.utils import timezone


class Role(models.Model):
    name = models.CharField('Наименование', blank=False, null=False, max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Роль {self.name}'


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    company_name = models.CharField('Наименование компании заказчика', blank=False, null=False, max_length=200)
    is_nda_signed = models.BooleanField('NDA подписано?', blank=False, null=False, default=False)

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Профиль {self.user.username}'


class Platform(models.Model):
    platform_name = models.CharField('Название платформы', blank=False, null=False, max_length=200)
    platform_code = models.CharField('Код платформы', blank=False, null=False, max_length=5)

    def __str__(self):
        return self.platform_code


class TechnicalProcess(models.Model):
    name_process = models.CharField('Название технического процесса', blank=False, null=False, max_length=50)
    PDK_file = models.FileField('Файл КИП', upload_to='uploads/PDK/%Y/%m/%d/', blank=True, null=False, default='')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE, null=False, )


class Substrate(models.Model):
    thikness = models.IntegerField('Толщина подложки', blank=False, null=True)
    diameter = models.IntegerField('Диаметр подложки', blank=False, null=True)
    tech_proces = models.ForeignKey(TechnicalProcess, on_delete=models.CASCADE, null=False, )


class Order(models.Model):
    class OrderType(models.TextChoices):
        MPW = 'MPW', 'MPW',
        REP = 'REP', 'Повтор',
        ENG = 'ENG', 'Инженерный'

    class OrderStatus(models.TextChoices):
        NFW = 'NFW', 'Необходима доработка',
        OVK = 'OVK', 'На проверке у куратора',
        OVC = 'OVC', 'На проверке у исполнителя',
        OA = 'OA', 'Принят'
        OGDS = 'OGDS', 'Согласование'
        PO = 'PO', 'Оплата'
        POK = 'POK', 'Подтверждение оплаты куратором'
        POC = 'POC', 'Подтверждение оплаты исполнителем'
        MPO = 'MPO', 'Производство' 
        SO = 'SO', 'Отгрузка'
        EO = 'EO', 'Завершен'

    class DCRFProbingEMap(models.TextChoices):
        DC = 'DC Probing', 'DC проверка',
        RF = 'RF Probing', 'RF проверка',
        NO = 'No', 'Без проверки'

    class DicingMethod(models.TextChoices):
        SAW = 'SAW', 'Пила',

    class WaferDeliverFormat(models.TextChoices):
        NotCut = 'Пластина (без резки)', 'Пластина (без резки)',
        Cut = 'Пластина резанная', 'Пластина резанная',
        GelPack = 'Гельпак', 'Гельпак',

    # repeat = models.BooleanField('Повтор',  blank=False, null=False,)

    # Номер заказа имеет формат FYYYYMMDD{№} где № это число из 5 символов начиная с 00001
    order_number = models.CharField('Номер заказа', blank=False, null=False, max_length=14)
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False, )
    customer_product_name = models.CharField('Имя запуска', blank=False, null=False, max_length=200)
    mask_name = models.CharField('Номер шаблона', blank=False, null=True, max_length=200)
    technical_process = models.ForeignKey(TechnicalProcess, on_delete=models.CASCADE, null=False, )
    platform_code = models.ForeignKey(Platform, on_delete=models.CASCADE, null=False, )
    order_type = models.CharField('Тип запуска', choices=OrderType.choices, default=OrderType.ENG, blank=False,
                                  null=False, max_length=200)
    product_count = models.IntegerField('Число проектов в кадре', blank=False, null=True)
    substrate = models.ForeignKey(Substrate, on_delete=models.CASCADE, null=False, )
    dc_rf_probing_e_map = models.CharField('E-map проверка', choices=DCRFProbingEMap.choices,
                                           default=DCRFProbingEMap.NO, blank=False,
                                           null=False, max_length=200)
    dc_rf_probing_inking = models.BooleanField('Inking проверка', blank=False,
                                               null=False, )
    visual_inspection_inking = models.BooleanField('Визуальная проверка', blank=False,
                                                   null=False, )
    dicing_method = models.CharField('Метод резки', choices=DicingMethod.choices, default=DicingMethod.SAW, blank=False,
                                     null=False, max_length=200)
    tape_uv_support = models.BooleanField('УФ засветка', blank=False,
                                          null=False, )
    wafer_deliver_format = models.CharField('Вариант упаковки', choices=WaferDeliverFormat.choices,
                                            default=WaferDeliverFormat.NotCut, blank=False,
                                            null=False, max_length=200)
    multiplan_dicing_plan = models.BooleanField("Сложная резка", blank=False, null=False, )
    package_servce = models.BooleanField("Корпусирование", blank=False, null=False, )
    delivery_premium_template = models.BooleanField("Ускоренный запуск шаблона", blank=False, null=False, )
    delivery_premium_plate = models.BooleanField("Ускоренный запуск пластины", blank=False, null=False, )
    special_note = models.CharField('Заметка', choices=WaferDeliverFormat.choices, default=WaferDeliverFormat.NotCut,
                                    blank=False,
                                    null=False, max_length=2000)

    order_date = models.DateTimeField('Дата заказа (оплаты)', blank=False, null=True)
    deadline_date = models.DateTimeField('Срок выполнения по договору', blank=False, null=True)
    is_paid = models.BooleanField('Заказ оплачен?', blank=True, null=True, default=False)
    order_status = models.CharField('Статус заказа', choices=OrderStatus.choices, default=OrderStatus.OVK,
                                    blank=False, null=False, max_length=200)
    invoice_file = models.FileField('Файл счета', upload_to='uploads/invoices/%Y/%m/%d/', blank=True, null=False,
                                    default='')
    contract_file = models.FileField('Файл договора', upload_to='uploads/contracts/%Y/%m/%d/', blank=True, null=False,
                                     default='')
    GDS_file = models.FileField('Файл GDS', upload_to='uploads/GDS/%Y/%m/%d/', blank=True, null=False, default='')

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    
    
class Topic(models.Model):
    name = models.CharField(max_length=255)
    is_private = models.BooleanField(default=False)
    related_order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.CASCADE) 

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE) 
    topic = models.ForeignKey(Topic, related_name="messages", on_delete=models.CASCADE)  
    text = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Message by {self.user.username} in {self.topic.name}"


class File(models.Model):
    message = models.ForeignKey(Message, related_name="files", on_delete=models.CASCADE)  
    file = models.FileField(upload_to='topic_files/')  

    def __str__(self):
        return f"File attached to {self.message.id}"


class UserTopic(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user.username} in topic {self.topic.name}"
