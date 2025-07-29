from functools import wraps
from django.shortcuts import render
from account.models import Order, Profile
from ..access_rules.access_rules import ACCESS_RULES, check_view_permission, check_edit_permission

def restrict_by_status(order_kwarg='order_id'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                user_profile = Profile.objects.select_related('role').get(user=request.user)
            except Profile.DoesNotExist:
                return render(request, 'account/forbidden.html', {
                    'reason': 'У вашего пользователя отсутствует профиль или роль.'
                }, status=403)

            order_id = kwargs.get(order_kwarg)
            if not order_id:
                return render(request, 'account/forbidden.html', {
                    'reason': 'Номер заказа не был передан.'
                }, status=403)

            try:
                order = Order.objects.select_related('creator').get(id=order_id)
            except Order.DoesNotExist:
                return render(request, 'account/forbidden.html', {
                    'reason': f'Заказ с номером {order_id} не найден.'
                }, status=403)

            # TODO отрефакторить, отвязаться от метаданных в коде
            if view_func.__name__ == 'check_the_order':
                if not check_view_permission(user_profile, order):
                    return render(request, 'account/forbidden.html', {
                        'reason': 'Вы не можете просматривать этот заказ.'
                    }, status=403)
                return view_func(request, *args, **kwargs)

            if not check_edit_permission(user_profile, order):
                return render(request, 'account/forbidden.html', {
                    'reason': 'Вы не можете редактировать этот заказ.'
                }, status=403)

            allowed_roles = ACCESS_RULES.get(order.order_status, [])
            if user_profile.role.name not in allowed_roles:
                return render(request, 'account/forbidden.html', {
                    'reason': 'Вы не имеете доступ к этой странице.'
                }, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
