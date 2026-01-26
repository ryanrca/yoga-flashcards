"""
Tests for the flashcards app services.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch
from flashcards.models import Flashcard, DailyCard, CardUsageLog
from flashcards.services import DailyCardService
from .factories import FlashcardFactory, DailyCardFactory, CardUsageLogFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestDailyCardService:
    """Tests for the DailyCardService."""

    def test_get_daily_card_creates_new(self):
        """Test getting daily card when none exists for today."""
        user = UserFactory()
        FlashcardFactory(created_by=user, is_live=True, is_active=True)

        card = DailyCardService.get_daily_card()

        assert card is not None
        assert DailyCard.objects.filter(date=date.today()).exists()

    def test_get_daily_card_returns_existing(self):
        """Test getting daily card returns existing card for today."""
        user = UserFactory()
        flashcard = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        DailyCard.objects.create(card=flashcard, date=date.today())

        card = DailyCardService.get_daily_card()

        assert card == flashcard
        assert DailyCard.objects.filter(date=date.today()).count() == 1

    def test_get_daily_card_no_cards_available(self):
        """Test getting daily card when no cards exist."""
        card = DailyCardService.get_daily_card()
        assert card is None

    def test_get_daily_card_only_uses_live_active(self):
        """Test daily card only selects from live active cards."""
        user = UserFactory()
        # Create inactive and non-live cards
        FlashcardFactory(created_by=user, is_live=False, is_active=True)
        FlashcardFactory(created_by=user, is_live=True, is_active=False)
        # Create one valid card
        valid_card = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        card = DailyCardService.get_daily_card()

        assert card == valid_card

    def test_daily_card_logs_usage(self):
        """Test that selecting a daily card creates a usage log."""
        user = UserFactory()
        FlashcardFactory(created_by=user, is_live=True, is_active=True)

        card = DailyCardService.get_daily_card()

        assert CardUsageLog.objects.filter(
            card=card,
            used_date=date.today()
        ).exists()

    def test_select_next_card_excludes_used_in_cycle(self):
        """Test that cards used in current cycle are excluded."""
        user = UserFactory()
        used_card = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        unused_card = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # Mark used_card as already used in cycle 1
        CardUsageLog.objects.create(
            card=used_card,
            used_date=date.today() - timedelta(days=1),
            cycle_number=1
        )

        # Should select unused_card
        selected = DailyCardService._select_next_card()
        assert selected == unused_card

    def test_cycle_increments_when_all_cards_used(self):
        """Test cycle increments when all cards have been used."""
        user = UserFactory()
        card1 = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        card2 = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # Mark both cards as used in cycle 1
        CardUsageLog.objects.create(
            card=card1,
            used_date=date.today() - timedelta(days=2),
            cycle_number=1
        )
        CardUsageLog.objects.create(
            card=card2,
            used_date=date.today() - timedelta(days=1),
            cycle_number=1
        )

        # Get current cycle (should be 2 since all cards used)
        cycle = DailyCardService._get_current_cycle()
        assert cycle == 2

    def test_get_current_cycle_starts_at_one(self):
        """Test cycle starts at 1 when no logs exist."""
        cycle = DailyCardService._get_current_cycle()
        assert cycle == 1

    def test_all_cards_used_before_repeat(self):
        """Test that all cards are used before any repeats."""
        user = UserFactory()
        cards = [FlashcardFactory(created_by=user, is_live=True, is_active=True) for _ in range(3)]

        selected_ids = set()

        # Select cards until we've used all of them
        for i in range(3):
            # Clear today's daily card to allow new selection
            DailyCard.objects.filter(date=date.today()).delete()

            card = DailyCardService.get_daily_card()
            assert card is not None
            selected_ids.add(card.id)

            # Manually update the date for next iteration simulation
            if i < 2:
                DailyCard.objects.filter(card=card).update(
                    date=date.today() - timedelta(days=i+1)
                )
                CardUsageLog.objects.filter(card=card, used_date=date.today()).update(
                    used_date=date.today() - timedelta(days=i+1)
                )

        # All 3 cards should have been selected
        assert len(selected_ids) == 3

    @patch('flashcards.services.random.choice')
    def test_random_selection(self, mock_choice):
        """Test that card selection uses random.choice."""
        user = UserFactory()
        card = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        mock_choice.return_value = card

        selected = DailyCardService._select_next_card()

        assert mock_choice.called
        assert selected == card


@pytest.mark.django_db
class TestDailyCardServiceEdgeCases:
    """Edge case tests for DailyCardService."""

    def test_handles_deleted_daily_card_reference(self):
        """Test service handles when referenced card is deleted."""
        user = UserFactory()
        card1 = FlashcardFactory(created_by=user, is_live=True, is_active=True)
        card2 = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # Create daily card
        DailyCard.objects.create(card=card1, date=date.today())

        # Soft delete the card
        card1.is_active = False
        card1.save()

        # Service should still return the existing daily card
        result = DailyCardService.get_daily_card()
        assert result == card1

    def test_multiple_calls_same_day_return_same_card(self):
        """Test multiple calls on same day return same card."""
        user = UserFactory()
        FlashcardFactory(created_by=user, is_live=True, is_active=True)
        FlashcardFactory(created_by=user, is_live=True, is_active=True)

        card1 = DailyCardService.get_daily_card()
        card2 = DailyCardService.get_daily_card()
        card3 = DailyCardService.get_daily_card()

        assert card1 == card2 == card3

    def test_new_card_added_mid_cycle(self):
        """Test behavior when new card added during a cycle."""
        user = UserFactory()
        existing_card = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # Use the existing card
        CardUsageLog.objects.create(
            card=existing_card,
            used_date=date.today() - timedelta(days=1),
            cycle_number=1
        )

        # Add new card
        new_card = FlashcardFactory(created_by=user, is_live=True, is_active=True)

        # New card should be selected (unused in current cycle)
        selected = DailyCardService._select_next_card()
        assert selected == new_card
