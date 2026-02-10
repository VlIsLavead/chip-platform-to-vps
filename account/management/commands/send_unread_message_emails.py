from django.core.management.base import BaseCommand
from account.utils.unread_message_email_sender import send_unread_messages

class Command(BaseCommand):
    help = 'Send emails for unread messages after 1 hour'

    def handle(self, *args, **options):
        send_unread_messages()