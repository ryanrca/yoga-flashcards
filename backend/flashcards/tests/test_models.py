"""
Tests for the flashcards app models.
"""
import pytest
import uuid
from flashcards.models import Flashcard, Tag, DailyCard, CardUsageLog
from .factories import FlashcardFactory, TagFactory, DailyCardFactory, CardUsageLogFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestTagModel:
    """Tests for the Tag model."""

    def test_create_tag(self):
        """Test creating a tag."""
        tag = TagFactory(name='Test Tag', description='A test tag')
        assert tag.pk is not None
        assert tag.name == 'Test Tag'
        assert tag.description == 'A test tag'

    def test_tag_str(self):
        """Test tag string representation."""
        tag = TagFactory(name='Yamas')
        assert str(tag) == 'Yamas'

    def test_tag_name_unique(self):
        """Test that tag names must be unique."""
        TagFactory(name='Unique Tag')
        with pytest.raises(Exception):
            TagFactory(name='Unique Tag')

    def test_tag_ordering(self):
        """Test tags are ordered by name."""
        TagFactory(name='Zebra')
        TagFactory(name='Alpha')
        TagFactory(name='Beta')
        tags = Tag.objects.all()
        assert tags[0].name == 'Alpha'
        assert tags[1].name == 'Beta'
        assert tags[2].name == 'Zebra'


@pytest.mark.django_db
class TestFlashcardModel:
    """Tests for the Flashcard model."""

    def test_create_flashcard(self):
        """Test creating a flashcard."""
        user = UserFactory()
        flashcard = FlashcardFactory(
            title='Ahimsa',
            phrase='Non-violence',
            definition='The practice of non-violence',
            created_by=user
        )
        assert flashcard.pk is not None
        assert flashcard.title == 'Ahimsa'
        assert flashcard.version_number == 1
        assert flashcard.is_live is True
        assert flashcard.is_active is True

    def test_flashcard_str_live(self):
        """Test flashcard string representation for live version."""
        flashcard = FlashcardFactory(title='Test Card', is_live=True)
        assert 'LIVE' in str(flashcard)

    def test_flashcard_str_old_version(self):
        """Test flashcard string representation for old version."""
        flashcard = FlashcardFactory(title='Test Card', is_live=False, version_number=2)
        assert 'v2' in str(flashcard)

    def test_flashcard_with_tags(self):
        """Test flashcard with tags."""
        tag1 = TagFactory(name='Yamas')
        tag2 = TagFactory(name='Sanskrit')
        flashcard = FlashcardFactory()
        flashcard.tags.add(tag1, tag2)
        assert flashcard.tags.count() == 2
        assert tag1 in flashcard.tags.all()
        assert tag2 in flashcard.tags.all()

    def test_flashcard_default_version_group(self):
        """Test flashcard gets unique version_group by default."""
        flashcard1 = FlashcardFactory()
        flashcard2 = FlashcardFactory()
        assert flashcard1.version_group != flashcard2.version_group
        assert isinstance(flashcard1.version_group, uuid.UUID)


@pytest.mark.django_db
class TestFlashcardVersioning:
    """Tests for flashcard versioning functionality."""

    def test_create_new_version(self):
        """Test creating a new version of a flashcard."""
        user = UserFactory()
        original = FlashcardFactory(
            title='Original Title',
            definition='Original definition',
            created_by=user,
            version_number=1,
            is_live=True
        )
        original_version_group = original.version_group

        new_version = original.create_new_version(
            updated_by=user,
            title='Updated Title',
            definition='Updated definition'
        )

        # Check new version
        assert new_version.pk != original.pk
        assert new_version.title == 'Updated Title'
        assert new_version.definition == 'Updated definition'
        assert new_version.version_number == 2
        assert new_version.is_live is True
        assert new_version.version_group == original_version_group

        # Check original is no longer live
        original.refresh_from_db()
        assert original.is_live is False

    def test_create_new_version_preserves_tags(self):
        """Test that creating a new version preserves tags."""
        user = UserFactory()
        tag = TagFactory(name='Preserved Tag')
        original = FlashcardFactory(created_by=user)
        original.tags.add(tag)

        new_version = original.create_new_version(updated_by=user, title='New Title')

        assert tag in new_version.tags.all()

    def test_create_new_version_with_new_tags(self):
        """Test creating a new version with different tags."""
        user = UserFactory()
        old_tag = TagFactory(name='Old Tag')
        new_tag = TagFactory(name='New Tag')
        original = FlashcardFactory(created_by=user)
        original.tags.add(old_tag)

        new_version = original.create_new_version(
            updated_by=user,
            title='New Title',
            tags=[new_tag]
        )

        assert old_tag not in new_version.tags.all()
        assert new_tag in new_version.tags.all()

    def test_get_version_history(self):
        """Test getting version history."""
        user = UserFactory()
        original = FlashcardFactory(created_by=user, version_number=1, is_live=True)

        # Create multiple versions
        v2 = original.create_new_version(updated_by=user, title='Version 2')
        v3 = v2.create_new_version(updated_by=user, title='Version 3')

        history = v3.get_version_history()

        assert history.count() == 3
        # Should be ordered by version_number descending
        assert history[0].version_number == 3
        assert history[1].version_number == 2
        assert history[2].version_number == 1

    def test_revert_to_version(self):
        """Test reverting to a previous version."""
        user = UserFactory()
        original = FlashcardFactory(
            title='Original',
            definition='Original definition',
            created_by=user,
            version_number=1,
            is_live=True
        )

        v2 = original.create_new_version(
            updated_by=user,
            title='Version 2',
            definition='V2 definition'
        )

        # Revert to original
        reverted = original.revert_to_this_version(reverted_by=user)

        assert reverted.title == 'Original'
        assert reverted.definition == 'Original definition'
        assert reverted.version_number == 3  # New version created
        assert reverted.is_live is True
        assert reverted.version_group == original.version_group

        # V2 should no longer be live
        v2.refresh_from_db()
        assert v2.is_live is False

    def test_only_one_live_version(self):
        """Test that only one version can be live at a time."""
        user = UserFactory()
        original = FlashcardFactory(created_by=user, is_live=True)

        original.create_new_version(updated_by=user, title='V2')
        original.create_new_version(updated_by=user, title='V3')

        live_versions = Flashcard.objects.filter(
            version_group=original.version_group,
            is_live=True
        )
        assert live_versions.count() == 1


@pytest.mark.django_db
class TestDailyCardModel:
    """Tests for the DailyCard model."""

    def test_create_daily_card(self):
        """Test creating a daily card."""
        from datetime import date
        flashcard = FlashcardFactory()
        daily = DailyCard.objects.create(card=flashcard, date=date.today())
        assert daily.pk is not None
        assert daily.card == flashcard

    def test_daily_card_date_unique(self):
        """Test that only one daily card per date."""
        from datetime import date
        today = date.today()
        flashcard1 = FlashcardFactory()
        flashcard2 = FlashcardFactory()

        DailyCard.objects.create(card=flashcard1, date=today)
        with pytest.raises(Exception):
            DailyCard.objects.create(card=flashcard2, date=today)

    def test_daily_card_str(self):
        """Test daily card string representation."""
        from datetime import date
        flashcard = FlashcardFactory(title='Test Card')
        daily = DailyCard.objects.create(card=flashcard, date=date.today())
        assert 'Test Card' in str(daily)
        assert str(date.today()) in str(daily)


@pytest.mark.django_db
class TestCardUsageLogModel:
    """Tests for the CardUsageLog model."""

    def test_create_usage_log(self):
        """Test creating a card usage log."""
        from datetime import date
        flashcard = FlashcardFactory()
        log = CardUsageLog.objects.create(
            card=flashcard,
            used_date=date.today(),
            cycle_number=1
        )
        assert log.pk is not None
        assert log.cycle_number == 1

    def test_usage_log_unique_constraint(self):
        """Test unique constraint on card, date, cycle."""
        from datetime import date
        today = date.today()
        flashcard = FlashcardFactory()

        CardUsageLog.objects.create(card=flashcard, used_date=today, cycle_number=1)
        with pytest.raises(Exception):
            CardUsageLog.objects.create(card=flashcard, used_date=today, cycle_number=1)

    def test_usage_log_different_cycles_allowed(self):
        """Test same card can be logged in different cycles."""
        from datetime import date
        today = date.today()
        flashcard = FlashcardFactory()

        log1 = CardUsageLog.objects.create(card=flashcard, used_date=today, cycle_number=1)
        log2 = CardUsageLog.objects.create(card=flashcard, used_date=today, cycle_number=2)

        assert log1.pk is not None
        assert log2.pk is not None


@pytest.mark.django_db
class TestVersionFieldPreservation:
    """Regression tests for fields being dropped when a new version is made."""

    def test_create_new_version_preserves_short_answer(self):
        """short_answer carries onto the new version when not being changed."""
        card = FlashcardFactory(short_answer='Non-violence; do no harm.')
        new_version = card.create_new_version(
            updated_by=card.created_by,
            title='Ahimsa (revised)',
        )
        assert new_version.short_answer == 'Non-violence; do no harm.'

    def test_create_new_version_updates_short_answer(self):
        """An explicit short_answer still overrides the old value."""
        card = FlashcardFactory(short_answer='Old summary')
        new_version = card.create_new_version(
            updated_by=card.created_by,
            short_answer='New summary',
        )
        assert new_version.short_answer == 'New summary'

    def test_revert_preserves_short_answer(self):
        """Reverting copies short_answer from the target version."""
        card = FlashcardFactory(short_answer='Original summary')
        card.create_new_version(updated_by=card.created_by, short_answer='Changed summary')
        reverted = card.revert_to_this_version(reverted_by=card.created_by)
        assert reverted.short_answer == 'Original summary'
        assert reverted.is_live is True
