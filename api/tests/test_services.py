import pytest
from rest_framework.exceptions import NotFound, PermissionDenied

from account.models import Profile, Role, Topic, User
from api.services.topic_access import get_accessible_topics


def test_curator_sees_all_topics(order, curator_1):
    topic = Topic.objects.create(related_order=order)

    qs = get_accessible_topics(curator_1)

    assert topic in qs


def test_executor_sees_only_platform_topics(order, executor):
    topic = Topic.objects.create(related_order=order)

    qs = get_accessible_topics(executor)

    assert topic in qs


def test_customer_does_not_see_other_company_orders(order, customer):
    topic = Topic.objects.create(related_order=order)

    qs = get_accessible_topics(customer)

    assert topic not in qs


def test_executor_with_wrong_platform(executor):
    bad_executor = Profile.objects.create(
        user=User.objects.create(username='bad_executor'),
        role=executor.role,
        company_name='WRONG'
    )

    with pytest.raises(NotFound):
        get_accessible_topics(bad_executor)


def test_unknown_role_raises_permission_denied(prepare_database):
    strange_user = User.objects.create(username='strange')
    strange_role = Role.objects.create(name ='Тестировщик')
    strange = Profile.objects.create(
        user = strange_user,
        role = strange_role,
        company_name = 'SomeCo'
    )

    with pytest.raises(PermissionDenied):
        get_accessible_topics(strange)
