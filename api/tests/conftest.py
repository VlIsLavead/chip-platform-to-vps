import freezegun
import pytest
from rest_framework.test import APIClient
from django.core.management import call_command

from account.models import Profile, Order, Topic, Message


@pytest.fixture
def prepare_database(db):
    call_command('loaddata', 'test_order_data.json')


@pytest.fixture
def curator_1(prepare_database):
    return Profile.objects.get(pk=1)


@pytest.fixture
def curator_2(prepare_database):
    return Profile.objects.get(pk=3)


@pytest.fixture
def executor(prepare_database):
    return Profile.objects.get(pk=2)


@pytest.fixture
def customer(prepare_database):
    return Profile.objects.get(pk=4)


@pytest.fixture
def order(prepare_database):
    return Order.objects.get(pk=1)


@pytest.fixture
def topic(order):
    return Topic.objects.create(
        name='test topic',
        related_order=order
    )


@pytest.fixture
def message(topic, curator_1):
    return Message.objects.create(
        topic=topic,
        user=curator_1,
        text='Тестовое сообщение'
    )


@pytest.fixture
def api_client():
    return APIClient()
