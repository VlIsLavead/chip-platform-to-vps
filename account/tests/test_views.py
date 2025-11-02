import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_login_get_request(client):
    response = client.get(reverse('login'))

    assert response.status_code == 200
    assert b'<form' in response.content

@pytest.mark.django_db
def test_login_success(client):
    user = User.objects.create_user(username='testuser', password='testpass123')
    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'testpass123'
    })

    assert response.status_code == 302
    assert response.url == '/'

    response = client.get('/')
    assert response.wsgi_request.user.is_authenticated

@pytest.mark.django_db
def test_login_invalid_password(client):
    User.objects.create_user(username='testuser', password='correctpass')
    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'wrongpass'
    })

    assert response.status_code == 200
    assert b'Invalid login' in response.content

@pytest.mark.django_db
def test_login_inactive_user(client):
    user = User.objects.create_user(username='testuser', password='testpass123')
    user.is_active = False
    user.save()

    response = client.post(reverse('login'), {
        'username': 'testuser',
        'password': 'testpass123'
    })

    assert response.status_code == 200
    assert b'Invalid login' in response.content

@pytest.mark.django_db
def test_login_invalid_username(client):
    response = client.post(reverse('login'), {
        'username': 'nonexistent',
        'password': 'whatever'
    })

    assert response.status_code == 200
    assert b'Invalid login' in response.content
