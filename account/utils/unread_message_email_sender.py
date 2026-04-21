from datetime import timedelta
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings
from account.models import Message, UserTopic
from .email_recipients import send_email_about_unread_message
import time

def send_unread_messages():
    """Получает данные из email_recipients, работает с cron"""
    import sys
    print("=== STEP 1: Function started ===", flush=True)
    
    today_start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    threshold = now() - timedelta(hours=1)
    
    print(f"=== STEP 2: today_start={today_start}, threshold={threshold}", flush=True)

    messages = (
        Message.objects
        .filter(created_at__gte=today_start, created_at__lte=threshold, email_sent=False)
        .select_related('topic')
    )
    
    print(f"=== STEP 3: Found {messages.count()} messages", flush=True)

    recipients_dict = {}

    for message in messages:
        print(f"=== STEP 4: Processing message {message.id}", flush=True)
        
        user_topics = UserTopic.objects.filter(topic=message.topic)
        print(f"=== STEP 5: UserTopic count = {user_topics.count()}", flush=True)

        still_unread = False
        for ut in user_topics:
            last_read = ut.last_read_message
            if not last_read or last_read.id < message.id:
                still_unread = True
                break

        if not still_unread:
            print(f"=== STEP 6: Message {message.id} - all users read it", flush=True)
            message.email_sent = True
            message.save(update_fields=['email_sent'])
            continue

        print(f"=== STEP 7: Message {message.id} - still unread", flush=True)
        
        recipients = send_email_about_unread_message(message)
        print(f"=== STEP 8: Recipients = {recipients}", flush=True)
        
        for recipient in recipients:
            recipients_dict.setdefault(recipient, []).append(message)

    print(f"=== STEP 9: recipients_dict = {recipients_dict}", flush=True)

    for recipient, msgs in recipients_dict.items():
        full_text = ""
        for msg in msgs:
            full_text += f"Чат: {msg.topic.name}\nТекст: {msg.text}\n\n"

        print(f"=== STEP 10: Sending email to {recipient}", flush=True)

        try:
            send_mail(
                subject="Непрочитанные сообщения",
                message=full_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            print(f"=== STEP 11: Email sent to {recipient}", flush=True)
        except Exception as e:
            print(f"=== STEP 11 ERROR: {e}", flush=True)

        time.sleep(5)

        for msg in msgs:
            msg.email_sent = True
            msg.save(update_fields=['email_sent'])
    
    print("=== STEP 12: Function finished ===", flush=True)