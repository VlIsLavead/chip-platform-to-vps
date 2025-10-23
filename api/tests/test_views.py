import pytest
from rest_framework import status


@pytest.mark.freeze_time('2025-10-10')
def test_curator_can_view_messages(api_client, curator_1, message):
    api_client.force_authenticate(user=curator_1.user)

    response = api_client.get(path=f'/api/topics/{message.topic_id}/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        'id': 1,
        'created_at': '2025-10-10T03:00:00+03:00',
        'text': 'Тестовое сообщение',
        'user': 'tester',
    }]


def test_customer_cannot_view_foreign_topic(api_client, customer, message):
    api_client.force_authenticate(user=customer.user)

    response = api_client.get(path=f'/api/topics/{message.topic_id}/')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_inactive_user_cannot_access_messages(api_client, curator_1, message):
    curator_1.user.is_active = False
    curator_1.user.save()
    api_client.force_authenticate(user=curator_1.user)

    response = api_client.get(path=f'/api/topics/{message.topic_id}/')

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_curator_can_view_all_chats(api_client, curator_1, topic):
    api_client.force_authenticate(user=curator_1.user)

    response = api_client.get('/api/chats/')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        'id': 1,
        'is_private': False,
        'last_message': None,
        'message_count': 0,
        'name': 'test topic',
        'related_order_id': 1,
    }]


def test_customer_sees_only_his_company_chats(api_client, customer):
    api_client.force_authenticate(user=customer.user)

    response = api_client.get('/api/chats/')

    assert response.json() == []


def test_inactive_user_cannot_access_chats(api_client, executor):
    executor.user.is_active = False
    executor.user.save()
    api_client.force_authenticate(user=executor.user)

    response = api_client.get('/api/chats/')

    assert response.status_code == status.HTTP_403_FORBIDDEN
