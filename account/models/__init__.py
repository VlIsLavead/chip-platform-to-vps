from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import now
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
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    company_name = models.CharField('Наименование компании заказчика', blank=False, null=False, max_length=200)
    is_nda_signed = models.BooleanField('NDA подписано?', blank=False, null=False, default=False)
    expiration_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Профиль {self.user.username}'
    
    def is_expired(self):
        return self.expiration_date and now() > self.expiration_date
    

class CustomerProfile(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="customer_profile")
    class MarketName(models.TextChoices):
        PS = 'PS', 'Госсектор',
        CR = 'CR', 'Корпоративный',
        CM = 'CM', 'Потребительский'
        
    class ContractForm(models.TextChoices):
        SH = 'SH', 'СЧ ОКР',
        SA = 'SA', 'Договор оказания услуг',
        DA = 'DA', 'Договор поставки'
        
    class LaunchFormat(models.TextChoices):
        MU = 'MU', 'Многопользовательский',
        EF = 'EF', 'Инженерный',
        DF = 'DF', 'Производственный'
    
    contact_technical_issues = models.TextField('Контактное лицо для обсуждения технических вопросов',\
                                blank=False, null=True, max_length=2000,
                                help_text='ФИО, тел. Электронная почта', )
    contact_economic_issues = models.TextField('Контактное лицо для обсуждения экономических вопросов',\
                                blank=False, null=True, max_length=2000,
                                help_text='ФИО, тел. Электронная почта', )
    market_name = models.CharField('Рынок, на который планируются поставки изделий',
                                choices=MarketName.choices, default=MarketName.PS, blank=False,
                                null=False, max_length=200, help_text=None)
    head_customer = models.TextField('Головной заказчик (при наличии)',\
                                blank=False, null=True, max_length=2000, help_text=None, )
    contract_form = models.CharField('Форма организации договора',
                                choices=ContractForm.choices, default=ContractForm.SH, blank=False,
                                null=False, max_length=200, help_text=None)
    competitive_procedures = models.TextField('Наличие конкурсных прроцедур',
                                blank=False, null=True, max_length=2000,
                                help_text='Указать площадку', )
    vp_control = models.TextField('Контроль ВП, контроль ценообразования ВП, ориентировочный срок письма \
                                в адрес 514 ВП о взятии под контроль ',\
                                blank=False, null=True, max_length=2000,
                                help_text=None, )
    stage_selection = models.TextField('Количество и состав этапов выполнения работы и их взаимосвязь (могут \
                                выполняться параллельно, только последовательно) ',
                                blank=False, null=True, max_length=2000,
                                help_text=None, )
    manufacturing_technology = models.TextField('Технология изготовления с учетом технологических опций',
                                blank=False, null=True, max_length=2000,
                                help_text=None, )
    pdk_version = models.TextField('Используемая версия PDK', blank=False, null=True, max_length=2000,
                                help_text=None, )
    hierarchry_structure = models.BooleanField('Иерархичность структуры топологии', blank=False,
                                null=False, default=False, help_text="Да/нет")
    project_name_and_abbreviation = models.TextField('Название проекта и аббревиатура (для заявки на фабрику)',
                                blank=False, null=True, max_length=2000,
                                help_text='Пример: Название проекта 1(аббревиатуры названия кристаллов)', )
    description_project = models.TextField('Краткое описание проекта (функционал)',
                                blank=False, null=True, max_length=2000,
                                help_text='Пример: СВЧ широкополосный усилитель 0-8 ГГц, усиление 20 дБ…', )
    scope_of_application = models.TextField('Область применения',
                                blank=False, null=True, max_length=2000,
                                help_text='Связь / радиолокация и т.п.', )
    name_technology_process = models.TextField('Наименование технологического процесса',
                                blank=False, null=True, max_length=2000,
                                help_text=None, )
    first_launch_date = models.DateTimeField('Планируемая дата первого запуска', blank=False, null=True, )
    crystal_size = models.IntegerField('Размер кристалла (в мкм)', blank=False, null=True,
                                validators=[MinValueValidator(1)], help_text=None, )
    launch_format = models.CharField('В каком формате планируется запуск (для уточнения возможности реализации)',
                                choices=LaunchFormat.choices, default=LaunchFormat.MU, blank=False,
                                null=False, max_length=200, help_text=None)
    production_plan = models.TextField('Производственный план на ближайшие 3-5 лет',
                                blank=False, null=True, max_length=2000,
                                help_text='год / тип запуска (количество кристаллов/пластин)', )

    def __str__(self):
        return f'Анкета заказчика {self.profile.user.username}'

def document_upload_path(instance, filename):
    return f'uploads/{instance.document_type}/{filename}'

  
class Document(models.Model):
    DOCUMENT_TYPES = [
        ('NDA', 'NDA'),
        ('consumer_request', 'consumer_request'),
        ('consumer_form', 'consumer_form'),
    ]
    
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file_path = models.FileField(upload_to=document_upload_path)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f'{self.get_document_type_display()} - {self.owner.username}'
    
    def is_expired(self):
        return self.expiration_date and timezone.now() > self.expiration_date
    

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
    value = models.TextField('Толщина (мкм)', unique=True)

    def __str__(self):
        return f"{self.value}"
    
    

class Diameter(models.Model):
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name='diameters',
        verbose_name='Платформа'
    )
    value = models.IntegerField('Диаметр (мм)')

    class Meta:
        unique_together = ('platform', 'value')

    def __str__(self):
        return f"{self.value} мм)"
    
    

class Substrate(models.Model):
    MATERIAL_CHOICES = [
        ('Si(Кремний)', 'Si(Кремний)'),
    ]
    
    material = models.CharField(
        'Тип материала подложки',
        max_length=15,
        choices=MATERIAL_CHOICES,
        default='Si'
    )
    
    def __str__(self):
        return self.get_material_display()


class Order(models.Model):
    # STANDARD = 'standard'
    # NON_STANDARD = 'non_standard'
    # THICKNESS_TYPE_CHOICES = [
    #     (STANDARD, 'Стандартная толщина подложки'),
    #     (NON_STANDARD, 'Нестандартная толщина подложки'),
    # ]
    
    class OrderStart(models.TextChoices):
        NEW = 'NEW', 'Новый заказ'
        REP = 'REP', 'Повтор заказа'
    
    class OrderType(models.TextChoices):
        MPW = 'MPW', 'MPW',
        REP = 'REP', 'Повтор',
        ENG = 'ENG', 'Инженерный'

    class OrderStatus(models.TextChoices):
        NFW = 'NFW', 'Требуется уточнение',
        OVK = 'OVK', 'На проверке',  # На проверке у куратора
        OVC = 'OVC', 'На проверке',  #На проверке у исполнителя
        OA = 'OA', 'Принят',
        SA = 'SA', 'Подписание договора',
        CSA = 'CSA', 'Подписание договора', #Проверка договора куратором
        ESA = 'ESA', 'Подписание договора', #Проверка договора исполнителем
        OGDS = 'OGDS', 'Загрузка GDS',
        CGDS = 'CGDS', 'Загрузка GDS', #Проверка GDS куратором
        EGDS = 'EGDS', 'Загрузка GDS', #Проверка GDS исполнителем
        PO = 'PO', 'Оплата',
        POK = 'POK', 'Подтверждение оплаты', #Подтверждение оплаты куратором
        POC = 'POC', 'Подтверждение оплаты', #Подтверждение оплаты исполнителем
        MPO = 'MPO', 'Производство',
        SO = 'SO', 'Отгрузка',
        PS = 'PS', 'Пластины отправлены',
        CR = 'CR', 'Подтверждение получения пластин',
        EO = 'EO', 'Завершен',

    class DCRFProbingEMap(models.TextChoices):
        DC = 'DC Probing', 'DC проверка',
        DR = 'DC + RF Probing', 'DC + RF проверка',
        NO = 'No', 'Без проверки'

    class DicingMethod(models.TextChoices):
        DC = 'DC', 'Дисковая резка',
        LS = 'LS', 'Лазер',

    class WaferDeliverFormat(models.TextChoices):
        NotCut = 'Пластины неразделенные', 'Пластины неразделенные',
        Cut = 'Пластина разделенная на полимерном носителе', 'Пластина разделенная на полимерном носителе',
        Container = 'Кристаллы в таре', 'Кристаллы в таре',

    class ContainerForCrystals(models.TextChoices):
        СontainerForCrystalls = 'Тара для пластин', 'Тара для пластин'
        PlasticCells = 'Пластмассовые ячейки', 'Пластмассовые ячейки',
        GelPack = 'Gel-Pak', 'Gel-Pak',

    # repeat = models.BooleanField('Повтор',  blank=False, null=False,)

    # Номер заказа имеет формат FYYYYMMDD{№} где № это число из 5 символов начиная с 00001
    order_number = models.CharField(blank=False, null=False, max_length=14)
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False)
    customer_product_name = models.CharField('Имя запуска', blank=False, null=False, max_length=200,
                                            help_text="Пояснение для имени запуска")
    # order_start = models.CharField('Тип заказа',choices=OrderStart.choices,
    #                                  default=OrderStart.NEW, blank=False, null=False, 
    #                                  max_length=200)
    mask_name = models.CharField('Номер шаблона', blank=False, null=True, max_length=200)
    technical_process = models.ForeignKey(TechnicalProcess, on_delete=models.CASCADE, null=False, 
                                            verbose_name='Техпроцесс')
    platform_code = models.ForeignKey(Platform, on_delete=models.CASCADE, null=False, 
                                      verbose_name='Площадка', 
                                      help_text="Выбор доступных технологических площадок: KI - НИЦ 'Курчатовский институт', ZC - АО 'ЗНТЦ'")
    order_type = models.CharField('Тип запуска', choices=OrderType.choices, default=OrderType.ENG, blank=False,
                                  null=False, max_length=200, )
    product_count = models.IntegerField('Число проектов в запуске', blank=False, null=True,
                                        validators=[MinValueValidator(1)], 
                                        help_text="Количество уникальных проектов на пластине")
    formation_frame_by_customer = models.BooleanField('Формирование кадра заказчиком', blank=False,
                                                      null=False, default=False, 
                                                      help_text="Заказчик самостоятельно определяем расположение структур в кадре")
    substrate_type = models.CharField(max_length=15, choices=Substrate.MATERIAL_CHOICES, default='Si', verbose_name='Тип толщины подложки',
                                            help_text="Пояснение для типа подложки")
    selected_thickness = models.ForeignKey(Thickness, on_delete=models.CASCADE, verbose_name='Толщина')
    selected_diameter = models.ForeignKey(Diameter, on_delete=models.CASCADE, verbose_name='Диаметр')
    dc_rf_probing_e_map = models.CharField('Контроль электрических параметров на пластине',
                                           choices=DCRFProbingEMap.choices,
                                           default=DCRFProbingEMap.NO, blank=False,
                                           null=False, max_length=200,
                                           help_text="Будет ли проводиться зондовый контроль параметров на структурах, его тип")
    dc_rf_probing_inking = models.BooleanField('Маркировка брака по электрическим параметрам', blank=False,
                                               null=False, help_text="Маркировка баркованных структур по результатам зондового контроля")
    visual_inspection_inking = models.BooleanField('Визуальный контроль и маркировка брака', blank=False,
                                                   null=False, help_text="Визуальный контроль структур на пластине с последующей маркировкой бракованных")
    parametric_monitor_control = models.BooleanField('Предоставление данных контроля параметрического монитора',
                                                     blank=False, null=False, default=False, 
                                                     help_text="Пояснение для данных контроля параметрического монитора")
    experimental_structure = models.BooleanField('Экспериментальная структура', blank=False,
                                                 null=False, default=False, 
                                                help_text="Запуск экспериментальных структур заказчика, \
                                                        выходящих за рамки библиотеки стандартных элементов, без \
                                                        гарантии работоспособности таких структур.")
    dicing_method = models.CharField('Способ разделения пластины на кристаллы', choices=DicingMethod.choices,
                                     default=DicingMethod.DC, blank=False,
                                     null=False, max_length=200)
    tape_uv_support = models.BooleanField('УФ засветка полимерного носителя', blank=False,
                                        null=False, help_text="Засветка полимерного носителя, на который наклеена \
                                            пластина  для ослабления его клеющей способности для последующего \
                                            самостоятельного съёма структур силами потребителя")
    wafer_deliver_format = models.CharField('Вид поставки пластин', choices=WaferDeliverFormat.choices,
                                            default=WaferDeliverFormat.NotCut, blank=False,
                                            null=False, max_length=200, help_text="Выбор вида разделения пластины на \
                                            отдельные структуры перед отгрузкой, либо его отсутсвие")
    container_for_crystals = models.CharField('Вид тары для кристаллов', choices=ContainerForCrystals.choices,
                                            default=ContainerForCrystals.GelPack, blank=False,
                                            null=False, max_length=200, help_text="Выбор тары, в которой будут \
                                            поставляться структуры после разделения пластины")
    parametric_monitor_control = models.BooleanField('Предоставление данных контроля параметрического монитора',
                                                     blank=False,
                                                     null=False, default=False, )
    # Разделение пластины на кристаллы по схеме заказчика(значение pdf по нажатию чекбокса)
    multiplan_dicing_plan = models.BooleanField("Разделение пластины на кристаллы по схеме заказчика", blank=False,
                                                null=False, help_text="Потребитель сам определяет схему разделения \
                                                пластины на структуры и предоставляет на фабрику")
    multiplan_dicing_plan_file = models.FileField('Файл ', upload_to='uploads/dicing_plan/%Y/%m/%d/', blank=True,
                                                  null=True,
                                                  default='')
    package_servce = models.BooleanField("Корпусирование силами производителя", blank=False, null=False, 
                                        help_text="Заказ сборки и корпусирования микросхем силами производителя")
    delivery_premium_template = models.BooleanField("Ускоренный запуск производства фотошаблонов", blank=False,
                                                    null=False, help_text="Запуск шаблонов вне общей очереди ")
    delivery_premium_plate = models.BooleanField("Ускоренный запуск производства пластин", blank=False, null=False,
                                                 help_text="Запуск производстся пластин вне общей очереди")
    special_note = models.TextField('Заметка', blank=False, null=True, max_length=2000, help_text=None, )
    order_date = models.DateTimeField('Дата оплаты', blank=False, null=True)
    deadline_date = models.DateTimeField('Срок выполнения по договору', blank=False, null=True)
    is_paid = models.BooleanField('Заказ оплачен?', blank=True, null=True, default=False)
    contract_is_ready = models.BooleanField('Подписание договора', blank=False, null=False, default=False)
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
    

class TopicFileModel(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='help_files/')

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name="messages", on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True, default="")
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
    
    
class RegistrationRequest(models.Model):
    name = models.CharField('ФИО', blank=False, null=False, max_length=100)
    mail = models.CharField('Email', blank=False, null=False, max_length=50)
    number = models.CharField('Номер телефона', blank=False, null=False, max_length=12)
    company = models.CharField('Наименование организации', blank=False, null=False, max_length=50)
    privacy_file = models.FileField('Файл конфиденциальности', upload_to='uploads/privacy_file/', blank=True, null=True,)
    processing_data = models.BooleanField('Я согласен на обработку персональных данных', blank=False, null=False)
    
