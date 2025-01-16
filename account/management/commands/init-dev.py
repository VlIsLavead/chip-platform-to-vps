from django.core.management import call_command
from django.core.management.base import BaseCommand

fixtures = [
    'account.role.json',
    'auth.user.json',
    'account.profile.json',

    'account.platform.json',

    'account.technicalprocess.json',
    'account.substrate.json',
    'account.order.json',
    'account.topic.json',
]


class Command(BaseCommand):
    help = 'Prime the db with dev data'

    def add_arguments(self, parser):
        parser.add_argument('--some-param', nargs='+', type=int)

    def handle(self, *args, **options):
        for f in fixtures:
            call_command('loaddata', f)
