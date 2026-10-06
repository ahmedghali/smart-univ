"""Charge chaque route sans paramètre : aucune ne doit renvoyer d'erreur serveur."""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse


def _routes(resolver=None, namespace=""):
    resolver = resolver or get_resolver()
    for entry in resolver.url_patterns:
        if isinstance(entry, URLResolver):
            ns = f"{namespace}{entry.namespace}:" if entry.namespace else namespace
            yield from _routes(entry, ns)
        elif isinstance(entry, URLPattern) and entry.name and not entry.pattern.converters:
            if "<" not in str(entry.pattern) and "(?P" not in str(entry.pattern):
                yield f"{namespace}{entry.name}"


ROUTES = sorted(set(r for r in _routes() if not r.startswith("admin:")))


@pytest.mark.django_db
@pytest.mark.parametrize("route", ROUTES)
def test_anonymous_get_does_not_crash(client, route):
    response = client.get(reverse(route))
    assert response.status_code < 500


@pytest.mark.django_db
@pytest.mark.parametrize("route", ROUTES)
def test_superuser_get_does_not_crash(admin_client, route):
    response = admin_client.get(reverse(route))
    assert response.status_code < 500
