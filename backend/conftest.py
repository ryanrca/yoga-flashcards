"""
Pytest configuration and shared fixtures for the yoga flashcards backend tests.
"""
import pytest
from django.test import Client
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return an API client for making requests."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an API client authenticated as admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def curator_client(api_client, curator_user):
    """Return an API client authenticated as curator."""
    api_client.force_authenticate(user=curator_user)
    return api_client


# User fixtures
@pytest.fixture
def user(db):
    """Create a regular user."""
    from users.tests.factories import UserFactory
    return UserFactory(role='user')


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from users.tests.factories import UserFactory
    return UserFactory(role='admin', is_staff=True)


@pytest.fixture
def curator_user(db):
    """Create a curator user."""
    from users.tests.factories import UserFactory
    return UserFactory(role='curator')


# Flashcard fixtures
@pytest.fixture
def tag(db):
    """Create a single tag."""
    from flashcards.tests.factories import TagFactory
    return TagFactory()


@pytest.fixture
def tags(db):
    """Create multiple tags."""
    from flashcards.tests.factories import TagFactory
    return [TagFactory() for _ in range(3)]


@pytest.fixture
def flashcard(db, admin_user):
    """Create a single flashcard."""
    from flashcards.tests.factories import FlashcardFactory
    return FlashcardFactory(created_by=admin_user)


@pytest.fixture
def flashcards(db, admin_user):
    """Create multiple flashcards."""
    from flashcards.tests.factories import FlashcardFactory
    return [FlashcardFactory(created_by=admin_user) for _ in range(5)]


@pytest.fixture
def flashcard_with_tags(db, admin_user, tags):
    """Create a flashcard with tags."""
    from flashcards.tests.factories import FlashcardFactory
    flashcard = FlashcardFactory(created_by=admin_user)
    flashcard.tags.set(tags)
    return flashcard
