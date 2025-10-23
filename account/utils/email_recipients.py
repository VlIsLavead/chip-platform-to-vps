from django.contrib.auth import get_user_model
from account.models import UserTopic

User = get_user_model()

TARGET_CURATOR_IDS = [5, 16]  # Специальные ID кураторов для отправки сообщения

def get_message_recipients(message):
    """
    Возвращает email-адреса кураторов из TARGET_CURATOR_IDS,
    если они не прочитали сообщение.
    """
    topic = message.topic

    user_topics = UserTopic.objects.filter(
        topic=topic,
        user__id__in=TARGET_CURATOR_IDS,
        user__role='Куратор'
    )

    recipient_emails = []
    for user_topic in user_topics:
        user = user_topic.user
        last_read = user_topic.last_read_message

        if not last_read or last_read.id < message.id:
            if user.email:
                recipient_emails.append(user.email)

    return recipient_emails
