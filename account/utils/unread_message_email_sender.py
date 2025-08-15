import threading
from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings

from account.models import Message
from ..utils.email_recipients import get_message_recipients

def unread_message_email_sender(message_id):
    def check():
        try:
            message = Message.objects.select_related('topic').get(id=message_id)

            recipients = get_message_recipients(message)

            if recipients:
                send_mail(
                    subject='Непрочитанное сообщение',
                    message=f'У вас есть непрочитанное сообщение в чате: {message.topic.name}\n\nТекст:\n{message.text}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipients,
                    fail_silently=False,
                )

        except Message.DoesNotExist:
            pass

    delay_seconds = 3600
    timer = threading.Timer(delay_seconds, check)
    timer.daemon = True
    timer.start()
