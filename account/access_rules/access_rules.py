from account.models import Order, Platform

ACCESS_RULES = {
    Order.OrderStatus.NFW: ['Заказчик'],
    Order.OrderStatus.OVK: ['Куратор'],
    Order.OrderStatus.OVC: ['Исполнитель'],
    Order.OrderStatus.OA: ['Заказчик'],
    Order.OrderStatus.SA: ['Заказчик'],
    Order.OrderStatus.CSA: ['Куратор'],
    Order.OrderStatus.ESA: ['Исполнитель'],
    Order.OrderStatus.OGDS: ['Заказчик'],
    Order.OrderStatus.CGDS: ['Куратор'],
    Order.OrderStatus.EGDS: ['Исполнитель'],
    Order.OrderStatus.PO: ['Заказчик'],
    Order.OrderStatus.POK: ['Куратор'],
    Order.OrderStatus.POC: ['Исполнитель'],
    Order.OrderStatus.MPO: ['Исполнитель'],
    Order.OrderStatus.SO: ['Исполнитель'],
    Order.OrderStatus.PS: ['Куратор'],
    Order.OrderStatus.CR: ['Заказчик'],
}

def check_view_permission(user_profile, order):
    user_role = user_profile.role.name
    user_company = user_profile.company_name
    
    if order.creator.user.id == user_profile.user.id:
        return True
    
    if user_company == order.creator.company_name:
        return True
    
    if user_role == 'Куратор':
        return True
    
    if user_role == 'Исполнитель':
        try:
            user_platform = Platform.objects.get(platform_code=user_company)
            if user_platform.id == order.platform_code_id:
                return True
        except Platform.DoesNotExist:
            return False
    
    return False

def check_edit_permission(user_profile, order):
    """Проверка прав на редактирование заказа"""
    user_role = user_profile.role.name
    
    if order.creator.user.id == user_profile.user.id:
        return True
    
    if user_role == 'Куратор':
        return True
    
    if user_role == 'Исполнитель':
        try:
            user_platform = Platform.objects.get(platform_code=user_profile.company_name)
            if user_platform.id == order.platform_code_id:
                return True
        except Platform.DoesNotExist:
            return False
    
    return False