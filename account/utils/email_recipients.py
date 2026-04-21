import threading
from django.core.mail import send_mail
from django.conf import settings
from account.models import Message, UserTopic


def send_email_about_unread_message(message):
    """Возвращает список email-ов получателей (не отправляет письма)"""
    """Используется для unread_message_email_sender(cron)"""
    topic = message.topic
    
    user_topics = UserTopic.objects.filter(topic=topic).select_related('user__user')
    
    recipients = []
    for ut in user_topics:
        if ut.user.id == message.user.id:
            continue
        
        last_read = ut.last_read_message
        if not last_read or last_read.id < message.id:
            email = ut.user.user.email
            if email and email not in recipients:
                recipients.append(email)
    
    return recipients


# def send_email_about_unread_message(message_id):
#     """Отправляет email всем участникам чата при создании нового сообщения"""
    
#     def send():
#         try:
#             message = Message.objects.select_related('topic', 'user__user').get(id=message_id)
#             topic = message.topic
            
#             user_topics = UserTopic.objects.filter(topic=topic).select_related('user__user')
            
#             recipients = []
#             for ut in user_topics:
#                 if ut.user.id == message.user.id:
#                     continue
                
#                 last_read = ut.last_read_message
#                 if not last_read or last_read.id < message.id:
#                     email = ut.user.user.email
#                     if email and email not in recipients:
#                         recipients.append(email)
            
#             if not recipients:
#                 return
            
#             for email in recipients:
#                 send_mail(
#                     subject=f'Новое сообщение в чате {topic.name}',
#                     message=f'У вас есть новое сообщение в чате: {topic.name}\n\nОтправитель: {message.user.user.username}\n\nТекст:\n{message.text}',
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     recipient_list=[email],
#                     fail_silently=False,
#                 )
                
#         except Exception:
#             pass
    
#     timer = threading.Timer(1, send)
#     timer.daemon = True
#     timer.start()