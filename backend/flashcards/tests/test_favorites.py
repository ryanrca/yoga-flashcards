"""
Tests for favourites: the toggle endpoint, the filtered list, and the counter.

The behaviours worth protecting here are the ones that are invisible in the
happy path: that an ordinary user is allowed to favourite at all, that the
counter is a lifetime tally rather than a live count, and that a favourite
belongs to the card *family* so editing a card cannot silently lose it.
"""
import pytest
from rest_framework import status

from flashcards.models import Favorite
from users.tests.factories import UserFactory

from .factories import FlashcardFactory


@pytest.mark.django_db
class TestFavoriteToggle:
    """POST /api/cards/{id}/favorite/"""

    def test_requires_authentication(self, api_client, flashcard):
        response = api_client.post(f'/api/cards/{flashcard.id}/favorite/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Favorite.objects.exists()

    def test_an_ordinary_user_may_favorite(self, authenticated_client, flashcard):
        """
        Guards the get_permissions wiring specifically.

        Every action not named in that method falls through to the else branch,
        which requires a curator. If `favorite` ever drops out of the
        IsAuthenticated list, favouriting silently becomes staff-only - which
        defeats the entire feature - and no other test would catch it.
        """
        response = authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['favorited'] is True
        assert response.data['favorite_count'] == 1

    def test_favoriting_creates_one_row_keyed_on_the_version_group(
        self, authenticated_client, user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        favorite = Favorite.objects.get(user=user)
        assert favorite.version_group == flashcard.version_group

    def test_a_second_click_removes_the_favorite(
        self, authenticated_client, user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        response = authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['favorited'] is False
        assert not Favorite.objects.filter(
            user=user, version_group=flashcard.version_group
        ).exists()

    def test_count_is_a_lifetime_tally_and_never_decrements(
        self, authenticated_client, flashcard
    ):
        """
        Unfavouriting deliberately leaves the counter alone, so favorite_count
        and "how many people have this saved right now" diverge the first time
        anyone removes one. That divergence is the intended design, not drift.
        """
        add = authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        assert add.data['favorite_count'] == 1

        remove = authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        assert remove.data['favorite_count'] == 1

        flashcard.refresh_from_db()
        assert flashcard.favorite_count == 1

        # Favouriting again counts again - it is a tally of events, not holders.
        again = authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        assert again.data['favorited'] is True
        assert again.data['favorite_count'] == 2

    def test_two_users_favoriting_both_count(self, api_client, flashcard):
        for _ in range(2):
            api_client.force_authenticate(user=UserFactory(role='user'))
            api_client.post(f'/api/cards/{flashcard.id}/favorite/')

        flashcard.refresh_from_db()
        assert flashcard.favorite_count == 2
        assert Favorite.objects.filter(version_group=flashcard.version_group).count() == 2

    def test_one_users_favorite_is_invisible_to_another(self, api_client, flashcard):
        mine = UserFactory(role='user')
        theirs = UserFactory(role='user')

        api_client.force_authenticate(user=mine)
        api_client.post(f'/api/cards/{flashcard.id}/favorite/')

        api_client.force_authenticate(user=theirs)
        response = api_client.get('/api/cards/')

        card = next(c for c in response.data['results'] if c['id'] == flashcard.id)
        assert card['is_favorited'] is False
        # The tally is a property of the card, so it is the same for everyone.
        assert card['favorite_count'] == 1


@pytest.mark.django_db
class TestFavoritesFilter:
    """GET /api/cards/?favorites=true"""

    def test_returns_only_the_callers_favorites(
        self, authenticated_client, admin_user
    ):
        saved = FlashcardFactory(created_by=admin_user, title='Saved card')
        FlashcardFactory(created_by=admin_user, title='Ignored card')

        authenticated_client.post(f'/api/cards/{saved.id}/favorite/')
        response = authenticated_client.get('/api/cards/?favorites=true')

        assert response.status_code == status.HTTP_200_OK
        assert [c['title'] for c in response.data['results']] == ['Saved card']

    def test_is_empty_before_anything_is_saved(self, authenticated_client, flashcards):
        response = authenticated_client.get('/api/cards/?favorites=true')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []

    def test_removing_a_favorite_drops_it_from_the_list(
        self, authenticated_client, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        response = authenticated_client.get('/api/cards/?favorites=true')
        assert response.data['results'] == []

    def test_search_still_applies_inside_favorites(
        self, authenticated_client, admin_user
    ):
        """
        The filter narrows the same queryset rather than replacing it, so the
        search box on /favorites has to keep working.
        """
        ahimsa = FlashcardFactory(created_by=admin_user, title='Ahimsa')
        santosha = FlashcardFactory(created_by=admin_user, title='Santosha')

        authenticated_client.post(f'/api/cards/{ahimsa.id}/favorite/')
        authenticated_client.post(f'/api/cards/{santosha.id}/favorite/')

        response = authenticated_client.get('/api/cards/?favorites=true&search=Ahimsa')

        assert [c['title'] for c in response.data['results']] == ['Ahimsa']

    def test_unauthenticated_callers_are_refused(self, api_client):
        response = api_client.get('/api/cards/?favorites=true')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestFavoritesFollowCardVersions:
    """
    The point of keying on version_group rather than a card id.

    Editing a card creates a new Flashcard row and retires the old one, so an
    id-keyed favourite would vanish the moment a curator fixed a typo.
    """

    def test_favorite_survives_an_edit_and_resolves_to_the_live_version(
        self, authenticated_client, admin_user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        new_version = flashcard.create_new_version(
            updated_by=admin_user, title='Edited title'
        )

        response = authenticated_client.get('/api/cards/?favorites=true')
        results = response.data['results']

        assert len(results) == 1
        # The user is taken to the newest version, never the one they saved.
        assert results[0]['id'] == new_version.id
        assert results[0]['title'] == 'Edited title'
        assert results[0]['is_favorited'] is True

    def test_the_retired_version_is_not_listed_as_well(
        self, authenticated_client, admin_user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        flashcard.create_new_version(updated_by=admin_user, title='Edited title')

        response = authenticated_client.get('/api/cards/?favorites=true')

        assert len(response.data['results']) == 1
        assert flashcard.id not in [c['id'] for c in response.data['results']]

    def test_the_tally_carries_forward_to_the_new_version(
        self, authenticated_client, admin_user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        # The endpoint incremented the counter with an UPDATE, so this in-memory
        # instance is stale. A real edit re-reads the row first; the refresh is
        # what makes this test match that.
        flashcard.refresh_from_db()
        new_version = flashcard.create_new_version(updated_by=admin_user)

        assert new_version.favorite_count == 1

    def test_unfavoriting_works_from_the_new_version(
        self, authenticated_client, admin_user, user, flashcard
    ):
        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')
        new_version = flashcard.create_new_version(updated_by=admin_user)

        response = authenticated_client.post(f'/api/cards/{new_version.id}/favorite/')

        assert response.data['favorited'] is False
        assert not Favorite.objects.filter(
            user=user, version_group=flashcard.version_group
        ).exists()


@pytest.mark.django_db
class TestFavoriteSerialization:
    """is_favorited on the card payload."""

    def test_is_favorited_is_false_for_anonymous_callers(self, api_client, flashcard):
        """The daily card is public, so it is serialized without a logged-in user."""
        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_favorited'] is False

    def test_is_favorited_reflects_the_callers_own_state(
        self, authenticated_client, flashcard
    ):
        before = authenticated_client.get(f'/api/cards/{flashcard.id}/')
        assert before.data['is_favorited'] is False

        authenticated_client.post(f'/api/cards/{flashcard.id}/favorite/')

        after = authenticated_client.get(f'/api/cards/{flashcard.id}/')
        assert after.data['is_favorited'] is True
        assert after.data['favorite_count'] == 1
