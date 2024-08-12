from django.db import models
from django.conf import settings


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
    NDA_signature = models.BooleanField('Подписанное NDA', blank=False, null=False, )

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Профиль {self.user.username}'


class Order(models.Model):
    class Platform_codes(models.TextChoices):
        MT = 'MT', 'MT',
        KI = 'KI', 'KI',

    class Order_types(models.TextChoices):
        MPW = 'MPW', 'MPW',
        REP = 'REP', 'Повтор',
        ENG = 'ENG', 'Инженерный'

    class Order_statuses(models.TextChoices):
        CTP = 'CTP', 'Проверка топологии',
        PSF = 'PSF', 'Формирование запуска',
        PRD = 'PRD', 'Производство'
        SHP = 'SHP', 'Отгрузка'
        SHD = 'SHD', 'Отгружен'

    user_creator = models.ForeignKey(Profile, on_delete=models.CASCADE, null=False, )
    platform_code = models.CharField('Код площадки', choices=Platform_codes.choices, default=Platform_codes.MT,
                                     blank=False, null=False, max_length=200)
    order_type = models.CharField('Тип заказа', choices=Order_types.choices, default=Order_types.ENG, blank=False,
                                  null=False, max_length=200)
    order_date = models.DateTimeField('Дата заказа(оплаты)', blank=False, null=False)
    runtime = models.DateTimeField('Срок выполнения по договору', blank=False, null=False)
    payment_status = models.BooleanField('Статус оплаты', blank=False, null=False, )
    order_status = models.CharField('Статус заказа', choices=Order_statuses.choices, default=Order_statuses.CTP,
                                    blank=False, null=False, max_length=200)

    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
