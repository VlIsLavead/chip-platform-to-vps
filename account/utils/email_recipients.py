from django.contrib.auth import get_user_model
from account.models import UserTopic

User = get_user_model()

def get_message_recipients(message):
    topic = message.topic

    user_topics = UserTopic.objects.filter(
        topic=topic,
    )

    recipient_emails = []
    for user_topic in user_topics:
        user = user_topic.user
        
        try:
            django_user = User.objects.get(id=user.id)
            # 3 ID - выбранные кураторы для тестирования отправления сообщений
            # на почту, в дальнейшем сообщения будут рассылаться всем пользователям
            if django_user.id not in [5, 29, 16]:
                continue
            if django_user.email:
                last_read = user_topic.last_read_message
                if not last_read or last_read.id < message.id:
                    recipient_emails.append(django_user.email)
        except User.DoesNotExist:
            continue
        
    return recipient_emails
