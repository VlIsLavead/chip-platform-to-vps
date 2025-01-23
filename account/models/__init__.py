from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Role(models.Model):
    name = models.CharField('Наименование', blank=False, null=False, max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Роль {self.name}'


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
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

    def __str__(self):
        return self.name_process


class Thickness(models.Model):
    STANDARD = 'standard'
    NON_STANDARD = 'non_standard'
    TYPE_CHOICES = [
        (STANDARD, 'Стандартная'),
        (NON_STANDARD, 'Нестандартная'),
    ]

    type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default=STANDARD
    )
    value = models.IntegerField()

    def __str__(self):
        return f"{self.value} мкм - {self.type}"
    
    

class Diameter(models.Model):
    STANDARD = 'standard'
    NON_STANDARD = 'non_standard'
    TYPE_CHOICES = [
        (STANDARD, 'Стандартный'),
        (NON_STANDARD, 'Нестандартный'),
    ]

    type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default=STANDARD
    )
    value = models.IntegerField()

    def __str__(self):
        return f"{self.value} мм - {self.type}"
    
    

class Substrate(models.Model):
    STANDARD = 'standard'
    NON_STANDARD = 'non_standard'
    THICKNESS_TYPE_CHOICES = [
        (STANDARD, 'Стандартная толщина подложки'),
        (NON_STANDARD, 'Нестандартная толщина подложки'),
    ]
    
    thickness_type = models.CharField(
        'Тип подложки',
        max_length=15,
        choices=THICKNESS_TYPE_CHOICES,
        default=STANDARD
    )

    def __str__(self):
        return self.thickness_type


class Order(models.Model):
    STANDARD = 'standard'
    NON_STANDARD = 'non_standard'
    THICKNESS_TYPE_CHOICES = [
        (STANDARD, 'Стандартная толщина подложки'),
        (NON_STANDARD, 'Нестандартная толщина подложки'),
    ]
    
    class OrderStart(models.TextChoices):
        NEW = 'NEW', 'Новый заказ'
        REP = 'REP', 'Повтор заказа'
    
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
        NotCut = 'Пластины неразделенные', 'Пластины неразделенные',
        Cut = 'Пластина разделенная на полимерном носителе', 'Пластина разделенная на полимерном носителе',
        Container = 'Кристаллы в таре', 'Кристаллы в таре',

    class ContainerForCrystals(models.TextChoices):
        GelPack = 'Gel-Pak', 'Gel-Pak',
        PlasticCells = 'Пластмассовые ячейки', 'Пластмассовые ячейки',
        PetriDish = 'Чашка Петри', 'Чашка Петри',

    # repeat = models.BooleanField('Повтор',  blank=False, null=False,)

    # Номер заказа имеет формат FYYYYMMDD{№} где № это число из 5 символов начиная с 00001
    order_number = models.CharField(blank=False, null=False, max_length=14)
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False)
    customer_product_name = models.CharField('Имя запуска', blank=False, null=False, max_length=200)
    order_start = models.CharField('Тип заказа',choices=OrderStart.choices,
                                     default=OrderStart.NEW, blank=False, null=False, 
                                     max_length=200)
    mask_name = models.CharField('Номер шаблона', blank=False, null=True, max_length=200)
    technical_process = models.ForeignKey(TechnicalProcess, on_delete=models.CASCADE, null=False,
                                          verbose_name='Техпроцесс')
    platform_code = models.ForeignKey(Platform, on_delete=models.CASCADE, null=False, verbose_name='Площадка')
    order_type = models.CharField('Тип запуска', choices=OrderType.choices, default=OrderType.ENG, blank=False,
                                  null=False, max_length=200)
    product_count = models.IntegerField('Число проектов в кадре', blank=False, null=True,
                                        validators=[MinValueValidator(1)])
    formation_frame_by_customer = models.BooleanField('Формирование кадра заказчиком', blank=False,
                                                      null=False, default=False)
    substrate_type = models.CharField(max_length=15, choices=THICKNESS_TYPE_CHOICES, default=STANDARD,
                                      verbose_name='Тип толщины подложки')
    selected_thickness = models.ForeignKey(Thickness, on_delete=models.CASCADE, verbose_name='Толщина')
    selected_diameter = models.ForeignKey(Diameter, on_delete=models.CASCADE, verbose_name='Диаметр')
    dc_rf_probing_e_map = models.CharField('Контроль электрических параметров на пластине',
                                           choices=DCRFProbingEMap.choices,
                                           default=DCRFProbingEMap.NO, blank=False,
                                           null=False, max_length=200)
    dc_rf_probing_inking = models.BooleanField('Маркировка брака по электрическим параметрам', blank=False,
                                               null=False, )
    visual_inspection_inking = models.BooleanField('Визуальный контроль и маркировка брака', blank=False,
                                                   null=False, )
    parametric_monitor_control = models.BooleanField('Предоставление данных контроля параметрического монитора',
                                                     blank=False,
                                                     null=False, default=False, )
    experimental_structure = models.BooleanField('Экспериментальная структура', blank=False,
                                                 null=False, default=False, )
    dicing_method = models.CharField('Способ разделения пластины на кристаллы', choices=DicingMethod.choices,
                                     default=DicingMethod.SAW, blank=False,
                                     null=False, max_length=200)
    tape_uv_support = models.BooleanField('УФ засветка полимерного носителя', blank=False,
                                          null=False, )
    wafer_deliver_format = models.CharField('Вид поставки пластин', choices=WaferDeliverFormat.choices,
                                            default=WaferDeliverFormat.NotCut, blank=False,
                                            null=False, max_length=200)
    container_for_crystals = models.CharField('Вид тары для кристаллов', choices=ContainerForCrystals.choices,
                                              default=ContainerForCrystals.GelPack, blank=False,
                                              null=False, max_length=200)
    parametric_monitor_control = models.BooleanField('Предоставление данных контроля параметрического монитора',
                                                     blank=False,
                                                     null=False, default=False, )
    # Разделение пластины на кристаллы по схеме заказчика(значение pdf по нажатию чекбокса)
    multiplan_dicing_plan = models.BooleanField("Разделение пластины на кристаллы по схеме заказчика", blank=False,
                                                null=False, )
    multiplan_dicing_plan_file = models.FileField('Файл ', upload_to='uploads/dicing_plan/%Y/%m/%d/', blank=True,
                                                  null=True,
                                                  default='')
    package_servce = models.BooleanField("Корпусирование силами производителя", blank=False, null=False, )
    delivery_premium_template = models.BooleanField("Ускоренный запуск производства фотошаблонов", blank=False,
                                                    null=False, )
    delivery_premium_plate = models.BooleanField("Ускоренный запуск производства пластин", blank=False, null=False, )
    special_note = models.TextField('Заметка', blank=False, null=True, max_length=2000)

    order_date = models.DateTimeField('Дата оплаты', blank=False, null=True)
    deadline_date = models.DateTimeField('Срок выполнения по договору', blank=False, null=True)
    is_paid = models.BooleanField('Заказ оплачен?', blank=True, null=True, default=False)
    order_status = models.CharField('Статус заказа', choices=OrderStatus.choices, default=OrderStatus.OVK,
                                    blank=False, null=False, max_length=200)
    invoice_file = models.FileField('Файл счета', upload_to='uploads/invoices/%Y/%m/%d/', blank=True, null=False,
                                    default='')
    contract_file = models.FileField('Файл договора', upload_to='uploads/contracts/%Y/%m/%d/', blank=True, null=False,
                                     default='')
    GDS_file = models.FileField('Файл GDS', upload_to='uploads/GDS/%Y/%m/%d/', blank=True, null=False, default='')
    # Форму заполнил(закинуть почту профиля)

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
    last_read_message = models.ForeignKey('Message', null=True,
        blank=True, on_delete=models.SET_NULL, related_name='last_read_by'
    )

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user.username} in topic {self.topic.name}"
