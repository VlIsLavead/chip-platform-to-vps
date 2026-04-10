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
                
                # Пытаемся получить комментарий из POST запроса или из истории
                comment = None
                if request.method == 'POST':
                    comment = request.POST.get('comment', '').strip()
                
                # Если комментарий не нашли в POST, пробуем найти в последней записи истории
                if not comment:
                    last_history = order.status_history.filter(new_status=new_status).first()
                    if last_history and last_history.comment:
                        comment = last_history.comment
                
                _create_status_message(order, old_status, new_status, profile, comment)
                
        except Order.DoesNotExist:
            pass
        
        return response
    
    return wrapped_view


def _create_status_message(order, old_status, new_status, profile, comment=None):
    topic, created = Topic.objects.get_or_create(
        related_order=order,
        defaults={
            'name': f"Чат по заказу #{order.order_number}",
        }
    )
    
    status_choices = dict(Order.OrderStatus.choices)
    old_status_name = status_choices.get(old_status, old_status)
    new_status_name = status_choices.get(new_status, new_status)
    
    # Формируем сообщение с комментарием, если он есть
    if comment:
        message_text = f"Статус заказа изменен: {old_status_name} → {new_status_name}<br>Комментарий: {comment}"
    else:
        message_text = f"Статус заказа изменен: {old_status_name} → {new_status_name}"
    
    Message.objects.create(
        topic=topic,
        user=profile,
        text=message_text
    )