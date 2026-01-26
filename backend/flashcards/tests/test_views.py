"""
Tests for the flashcards app views and API endpoints.
"""
import pytest
from rest_framework import status
from flashcards.models import Flashcard, Tag
from .factories import FlashcardFactory, TagFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestFlashcardListView:
    """Tests for flashcard list endpoint."""

    def test_list_requires_authentication(self, api_client):
        """Test that listing flashcards requires authentication."""
        response = api_client.get('/api/cards/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_flashcards(self, authenticated_client, flashcards):
        """Test listing flashcards as authenticated user."""
        response = authenticated_client.get('/api/cards/')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 5

    def test_list_only_shows_live_active_cards(self, authenticated_client, admin_user):
        """Test that only live and active cards are listed."""
        FlashcardFactory(created_by=admin_user, is_live=True, is_active=True)
        FlashcardFactory(created_by=admin_user, is_live=False, is_active=True)  # Not live
        FlashcardFactory(created_by=admin_user, is_live=True, is_active=False)  # Not active

        response = authenticated_client.get('/api/cards/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_search_flashcards_by_title(self, authenticated_client, admin_user):
        """Test searching flashcards by title."""
        FlashcardFactory(created_by=admin_user, title='Ahimsa Non-Violence')
        FlashcardFactory(created_by=admin_user, title='Satya Truthfulness')

        response = authenticated_client.get('/api/cards/?search=Ahimsa')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Ahimsa Non-Violence'

    def test_search_flashcards_by_definition(self, authenticated_client, admin_user):
        """Test searching flashcards by definition."""
        FlashcardFactory(created_by=admin_user, title='Card 1', definition='Practice of non-violence')
        FlashcardFactory(created_by=admin_user, title='Card 2', definition='Practice of truthfulness')

        response = authenticated_client.get('/api/cards/?search=non-violence')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_tag_id(self, authenticated_client, admin_user):
        """Test filtering flashcards by tag ID."""
        tag = TagFactory(name='Yamas')
        card_with_tag = FlashcardFactory(created_by=admin_user)
        card_with_tag.tags.add(tag)
        FlashcardFactory(created_by=admin_user)  # Card without tag

        response = authenticated_client.get(f'/api/cards/?tags={tag.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_tag_name(self, authenticated_client, admin_user):
        """Test filtering flashcards by tag name."""
        tag = TagFactory(name='Sanskrit')
        card_with_tag = FlashcardFactory(created_by=admin_user)
        card_with_tag.tags.add(tag)
        FlashcardFactory(created_by=admin_user)

        response = authenticated_client.get('/api/cards/?tags=Sanskrit')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


@pytest.mark.django_db
class TestFlashcardCreateView:
    """Tests for flashcard create endpoint."""

    def test_create_requires_curator(self, authenticated_client):
        """Test that creating flashcards requires curator role."""
        data = {
            'title': 'New Card',
            'phrase': 'Test phrase',
            'definition': 'Test definition'
        }
        response = authenticated_client.post('/api/cards/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_create(self, curator_client):
        """Test curator can create flashcards."""
        data = {
            'title': 'New Card',
            'phrase': 'Test phrase',
            'definition': 'Test definition'
        }
        response = curator_client.post('/api/cards/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Card'
        assert response.data['version_number'] == 1
        assert response.data['is_live'] is True

    def test_admin_can_create(self, admin_client):
        """Test admin can create flashcards."""
        data = {
            'title': 'Admin Card',
            'phrase': 'Admin phrase',
            'definition': 'Admin definition'
        }
        response = admin_client.post('/api/cards/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_with_tags(self, curator_client):
        """Test creating flashcard with tags using tag_names."""
        data = {
            'title': 'Card with Tags',
            'phrase': 'Phrase',
            'definition': 'Definition',
            'tag_names': ['Test Tag', 'Another Tag']
        }
        response = curator_client.post('/api/cards/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['tags']) == 2

    def test_create_missing_required_fields(self, curator_client):
        """Test creating flashcard without required fields."""
        data = {'title': 'Only Title'}
        response = curator_client.post('/api/cards/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestFlashcardUpdateView:
    """Tests for flashcard update endpoint."""

    def test_update_requires_curator(self, authenticated_client, flashcard):
        """Test that updating flashcards requires curator role."""
        data = {'title': 'Updated Title'}
        response = authenticated_client.put(f'/api/cards/{flashcard.id}/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_update(self, curator_client, admin_user):
        """Test curator can update flashcards (creates new version)."""
        original = FlashcardFactory(
            created_by=admin_user,
            title='Original Title',
            definition='Original definition'
        )
        original_id = original.id

        data = {
            'title': 'Updated Title',
            'phrase': original.phrase,
            'definition': 'Updated definition'
        }
        response = curator_client.put(f'/api/cards/{original.id}/', data)
        assert response.status_code == status.HTTP_200_OK
        # Should create a new version with different ID
        assert response.data['id'] != original_id
        assert response.data['title'] == 'Updated Title'
        assert response.data['version_number'] == 2

    def test_update_marks_old_version_not_live(self, curator_client, admin_user):
        """Test updating marks old version as not live."""
        original = FlashcardFactory(created_by=admin_user, is_live=True)
        original_id = original.id

        data = {
            'title': 'Updated',
            'phrase': original.phrase,
            'definition': original.definition
        }
        curator_client.put(f'/api/cards/{original.id}/', data)

        original.refresh_from_db()
        assert original.is_live is False


@pytest.mark.django_db
class TestFlashcardDeleteView:
    """Tests for flashcard delete endpoint."""

    def test_delete_requires_curator(self, authenticated_client, flashcard):
        """Test that deleting flashcards requires curator role."""
        response = authenticated_client.delete(f'/api/cards/{flashcard.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_delete(self, curator_client, admin_user):
        """Test curator can delete flashcards."""
        flashcard = FlashcardFactory(created_by=admin_user)
        flashcard_id = flashcard.id
        response = curator_client.delete(f'/api/cards/{flashcard_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Card should no longer appear in list (either deleted or soft-deleted)
        list_response = curator_client.get('/api/cards/')
        card_ids = [c['id'] for c in list_response.data['results']]
        assert flashcard_id not in card_ids


@pytest.mark.django_db
class TestFlashcardVersionsView:
    """Tests for flashcard versions endpoint."""

    def test_versions_requires_curator(self, authenticated_client, flashcard):
        """Test that viewing versions requires curator role."""
        response = authenticated_client.get(f'/api/cards/{flashcard.id}/versions/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_view_versions(self, curator_client, admin_user):
        """Test curator can view version history."""
        original = FlashcardFactory(created_by=admin_user)
        v2 = original.create_new_version(updated_by=admin_user, title='V2')

        # Use the live version's ID to access versions
        response = curator_client.get(f'/api/cards/{v2.id}/versions/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestFlashcardRevertView:
    """Tests for flashcard revert endpoint."""

    def test_revert_requires_curator(self, authenticated_client, flashcard):
        """Test that reverting requires curator role."""
        response = authenticated_client.post(
            f'/api/cards/{flashcard.id}/revert_version/',
            {'version_id': flashcard.id}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_revert(self, curator_client, admin_user):
        """Test curator can revert to previous version."""
        original = FlashcardFactory(
            created_by=admin_user,
            title='Original',
            definition='Original def'
        )
        v2 = original.create_new_version(
            updated_by=admin_user,
            title='Version 2',
            definition='V2 def'
        )

        response = curator_client.post(
            f'/api/cards/{v2.id}/revert_version/',
            {'version_id': original.id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Original'
        assert response.data['version_number'] == 3

    def test_revert_requires_version_id(self, curator_client, flashcard):
        """Test revert requires version_id."""
        response = curator_client.post(f'/api/cards/{flashcard.id}/revert_version/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_revert_invalid_version_group(self, curator_client, admin_user):
        """Test revert fails with version from different card."""
        card1 = FlashcardFactory(created_by=admin_user)
        card2 = FlashcardFactory(created_by=admin_user)

        response = curator_client.post(
            f'/api/cards/{card1.id}/revert_version/',
            {'version_id': card2.id}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTagListView:
    """Tests for tag list endpoint."""

    def test_list_tags_public(self, api_client):
        """Test that listing tags is public."""
        TagFactory.create_batch(3)
        response = api_client.get('/api/tags/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_tags_ordered_by_name(self, api_client):
        """Test tags are ordered by name."""
        TagFactory(name='Zebra')
        TagFactory(name='Alpha')
        TagFactory(name='Beta')

        response = api_client.get('/api/tags/')
        names = [t['name'] for t in response.data['results']]
        assert names == ['Alpha', 'Beta', 'Zebra']


@pytest.mark.django_db
class TestTagCreateView:
    """Tests for tag create endpoint."""

    def test_create_requires_curator(self, authenticated_client):
        """Test that creating tags requires curator role."""
        data = {'name': 'New Tag'}
        response = authenticated_client.post('/api/tags/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_curator_can_create_tag(self, curator_client):
        """Test curator can create tags."""
        data = {'name': 'New Tag', 'description': 'A new tag'}
        response = curator_client.post('/api/tags/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Tag'

    def test_create_duplicate_tag_fails(self, curator_client):
        """Test creating duplicate tag fails."""
        TagFactory(name='Existing')
        data = {'name': 'Existing'}
        response = curator_client.post('/api/tags/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTagUpdateDeleteView:
    """Tests for tag update and delete endpoints."""

    def test_curator_can_update_tag(self, curator_client):
        """Test curator can update tags."""
        tag = TagFactory(name='Old Name')
        data = {'name': 'New Name', 'description': 'Updated'}
        response = curator_client.put(f'/api/tags/{tag.id}/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'New Name'

    def test_curator_can_delete_tag(self, curator_client):
        """Test curator can delete tags."""
        tag = TagFactory()
        response = curator_client.delete(f'/api/tags/{tag.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag.id).exists()
