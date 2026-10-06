import pytest


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(username="admin", email="admin@example.com", password="pass")


@pytest.fixture
def admin_client(client, superuser):
    client.force_login(superuser)
    return client
