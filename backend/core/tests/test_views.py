"""
Tests for the core app views and API endpoints.
"""
import pytest
from rest_framework import status
from flashcards.tests.factories import FlashcardFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check_returns_healthy(self, api_client):
        """Test health check returns healthy status."""
        response = api_client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['status'] == 'healthy'

    def test_health_check_is_public(self, api_client):
        """Test health check is publicly accessible."""
        response = api_client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestDailyCardEndpoint:
    """Tests for the daily card endpoint."""

    def test_daily_card_is_public(self, api_client):
        """Test daily card endpoint is publicly accessible."""
        user = UserFactory()
        FlashcardFactory(created_by=user, is_live=True, is_active=True)

        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK

    def test_daily_card_returns_card_data(self, api_client):
        """Test daily card returns complete card data."""
        user = UserFactory()
        flashcard = FlashcardFactory(
            created_by=user,
            title='Test Card',
            phrase='Test phrase',
            definition='Test definition',
            is_live=True,
            is_active=True
        )

        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'phrase' in response.data
        assert 'definition' in response.data

    def test_daily_card_no_cards_available(self, api_client):
        """Test daily card returns 404 when no cards exist."""
        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_daily_card_same_throughout_day(self, api_client):
        """Test daily card returns same card throughout the day."""
        user = UserFactory()
        FlashcardFactory(created_by=user, is_live=True, is_active=True)
        FlashcardFactory(created_by=user, is_live=True, is_active=True)

        response1 = api_client.get('/api/dailycard/')
        response2 = api_client.get('/api/dailycard/')

        assert response1.data['id'] == response2.data['id']

    def test_daily_card_includes_tags(self, api_client):
        """Test daily card includes tag information."""
        from flashcards.tests.factories import TagFactory
        user = UserFactory()
        tag = TagFactory(name='Yamas')
        flashcard = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        flashcard.tags.add(tag)

        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK
        assert 'tags' in response.data
        assert len(response.data['tags']) == 1
        assert response.data['tags'][0]['name'] == 'Yamas'

    def test_daily_card_only_selects_live_active(self, api_client):
        """Test daily card only selects from live active cards."""
        user = UserFactory()
        # Create invalid cards
        FlashcardFactory(created_by=user, is_live=False, is_active=True)
        FlashcardFactory(created_by=user, is_live=True, is_active=False)

        # No valid cards available
        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Add a valid card
        valid = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # Clear any cached daily card (force new selection)
        from flashcards.models import DailyCard
        DailyCard.objects.all().delete()

        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == valid.id
