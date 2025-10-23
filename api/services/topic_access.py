from rest_framework.exceptions import PermissionDenied, NotFound
from account.models import Profile, Order, Topic, Platform

class RoleConstants:
    CUSTOMER = 'Заказчик'
    CURATOR = 'Куратор'
    EXECUTOR = 'Исполнитель'


class ErrorMessages:
    PLATFORM_NOT_FOUND = 'Платформа не найдена'
    ACCESS_DENIED = 'Нет доступа'


def get_accessible_topics(profile):
    role_name = profile.role.name

    if role_name == RoleConstants.CUSTOMER:
        users_in_company = Profile.objects.filter(
            company_name=profile.company_name
        ).values_list('user', flat=True)
        orders = Order.objects.filter(creator__user__in=users_in_company)
        return Topic.objects.filter(related_order__in=orders)

    elif role_name == RoleConstants.CURATOR:
        return Topic.objects.all()

    elif role_name == RoleConstants.EXECUTOR:
        try:
            code_company = Platform.objects.get(platform_code=profile.company_name)
            orders = Order.objects.filter(platform_code_id=code_company)
            return Topic.objects.filter(related_order__in=orders)
        except Platform.DoesNotExist:
            raise NotFound(ErrorMessages.PLATFORM_NOT_FOUND)

    else:
        raise PermissionDenied(ErrorMessages.ACCESS_DENIED)
