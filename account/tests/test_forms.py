from django import forms
from account.forms import LoginForm

def test_login_form_valid_data():
    form = LoginForm(data={'username': 'user1', 'password': 'pass123456'})
    assert form.is_valid()

def test_login_form_empty_username():
    form = LoginForm(data={'username': '', 'password': 'pass123'})
    assert not form.is_valid()
    assert 'username' in form.errors

def test_login_form_empty_password():
    form = LoginForm(data={'username': 'user1', 'password': ''})
    assert not form.is_valid()
    assert 'password' in form.errors
