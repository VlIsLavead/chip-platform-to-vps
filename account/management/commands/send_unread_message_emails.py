import sys
from django.core.management.base import BaseCommand
from account.utils.unread_message_email_sender import send_unread_messages

class Command(BaseCommand):
    help = 'Send emails for unread messages after 1 hour'

    def handle(self, *args, **options):
        self.stdout.write("Starting send_unread_messages...")
        self.stdout.flush()
        
        # Перенаправляем stdout чтобы видеть print
        send_unread_messages()
        
        self.stdout.write("send_unread_messages completed")
        self.stdout.flush()