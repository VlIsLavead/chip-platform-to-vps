from functools import wraps
from ..models import Order, Topic, Message, Profile

def log_order_status_change(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        order_id = kwargs.get('order_id')
        
        if not order_id:
            return view_func(request, *args, **kwargs)
        
        try:
            order = Order.objects.get(id=order_id)
            old_status = order.order_status
        except Order.DoesNotExist:
            return view_func(request, *args, **kwargs)
        
        response = view_func(request, *args, **kwargs)
        
        try:
            order.refresh_from_db()
            new_status = order.order_status
            
            if old_status != new_status:
                try:
                    profile = Profile.objects.get(user=request.user)
                except Profile.DoesNotExist:
                    profile = order.creator
                
                _create_status_message(order, old_status, new_status, profile)
                
        except Order.DoesNotExist:
            pass
        
        return response
    
    return wrapped_view


def _create_status_message(order, old_status, new_status, profile):
    topic, created = Topic.objects.get_or_create(
        related_order=order,
        defaults={
            'name': f"Чат по заказу #{order.order_number}",
        }
    )
    
    user_display = "Система"
    if profile and profile.user:
        user_display = profile.user.get_full_name() or profile.user.username
    
    status_choices = dict(Order.OrderStatus.choices)
    old_status_name = status_choices.get(old_status, old_status)
    new_status_name = status_choices.get(new_status, new_status)
    
    message_text = (
        f"Статус заказа был изменен на: {new_status_name}"
    )
    
    Message.objects.create(
        topic=topic,
        user=profile,
        text=message_text
    )