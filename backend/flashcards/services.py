import random
from datetime import date, timedelta
from django.db.models import Q
from .models import Flashcard, DailyCard, CardUsageLog


class DailyCardService:
    """Service for managing daily card selection."""

    @staticmethod
    def get_daily_card():
        """Get or create the daily card for today."""
        today = date.today()
        
        # Check if we already have a daily card for today
        try:
            daily_card = DailyCard.objects.get(date=today)
            return daily_card.card
        except DailyCard.DoesNotExist:
            pass
        
        # Select a new daily card
        card = DailyCardService._select_next_card()
        if card:
            # Create daily card record
            DailyCard.objects.create(card=card, date=today)
            
            # Log usage
            current_cycle = DailyCardService._get_current_cycle()
            CardUsageLog.objects.create(
                card=card,
                used_date=today,
                cycle_number=current_cycle
            )
            
            return card
        
        return None

    @staticmethod
    def _select_next_card():
        """Select the next card to be the daily card."""
        active_cards = Flashcard.objects.filter(is_active=True)
        
        if not active_cards.exists():
            return None
        
        current_cycle = DailyCardService._get_current_cycle()
        
        # Get cards that haven't been used in the current cycle
        used_card_ids = CardUsageLog.objects.filter(
            cycle_number=current_cycle
        ).values_list('card_id', flat=True)
        
        unused_cards = active_cards.exclude(id__in=used_card_ids)
        
        if unused_cards.exists():
            # Return a random unused card
            return random.choice(unused_cards)
        else:
            # All cards have been used, start a new cycle
            new_cycle = current_cycle + 1
            return random.choice(active_cards)

    @staticmethod
    def _get_current_cycle():
        """Get the current cycle number."""
        latest_log = CardUsageLog.objects.order_by('-cycle_number').first()
        if latest_log:
            # Check if all active cards have been used in this cycle
            active_card_count = Flashcard.objects.filter(is_active=True).count()
            used_in_current_cycle = CardUsageLog.objects.filter(
                cycle_number=latest_log.cycle_number
            ).count()
            
            if used_in_current_cycle >= active_card_count:
                return latest_log.cycle_number + 1
            else:
                return latest_log.cycle_number
        else:
            return 1
