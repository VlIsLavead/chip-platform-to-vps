from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from account.models import Message, UserTopic
from .email_recipients import get_message_recipients
import time

def send_unread_messages():
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    threshold = now() - timedelta(hours=1)

    messages = (
        Message.objects
        .filter(created_at__gte=today_start, created_at__lte=threshold, email_sent=False)
        .select_related('topic')
    )

    recipients_dict = {}

    for message in messages:
        user_topics = UserTopic.objects.filter(topic=message.topic)

        still_unread = False
        for ut in user_topics:
            last_read = ut.last_read_message
            if not last_read or last_read.id < message.id:
                still_unread = True
                break

        if not still_unread:
            message.email_sent = True
            message.save(update_fields=['email_sent'])
            continue

        recipients = get_message_recipients(message)
        for recipient in recipients:
            recipients_dict.setdefault(recipient, []).append(message)

    for recipient, msgs in recipients_dict.items():
        full_text = ""
        for msg in msgs:
            full_text += f"Чат: {msg.topic.name}\nТекст: {msg.text}\n\n"

        try:
            send_mail(
                subject="Непрочитанные сообщения",
                message=full_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
            )
        except Exception as e:
            print(f"Ошибка при отправке письма {recipient}: {e}")
            continue

        time.sleep(5)

        for msg in msgs:
            msg.email_sent = True
            msg.save(update_fields=['email_sent'])