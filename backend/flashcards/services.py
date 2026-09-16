import logging
import random
import uuid
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    Flashcard, DailyCard, CardUsageLog, CardImage, ImageGenerationSettings,
    CardImagePreference,
)
from .openrouter import OpenRouterClient, OpenRouterError

logger = logging.getLogger(__name__)


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
        # Only select from live versions of active cards
        active_cards = Flashcard.objects.filter(is_active=True, is_live=True)
        
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
            # Every card has been used in this cycle. _get_current_cycle() rolls the
            # cycle number forward on the next call, so just pick from all cards.
            return random.choice(active_cards)

    @staticmethod
    def _get_current_cycle():
        """Get the current cycle number."""
        latest_log = CardUsageLog.objects.order_by('-cycle_number').first()
        if latest_log:
            # Check if all active live cards have been used in this cycle
            active_card_count = Flashcard.objects.filter(is_active=True, is_live=True).count()
            used_in_current_cycle = CardUsageLog.objects.filter(
                cycle_number=latest_log.cycle_number
            ).count()
            
            if used_in_current_cycle >= active_card_count:
                return latest_log.cycle_number + 1
            else:
                return latest_log.cycle_number
        else:
            return 1


class CardImageService:
    """
    Orchestrates AI image generation for cards.

    Two rules shape everything here:

    1. The bot generates each card's first image exactly once. Auto-queueing
       looks for card families with *no* image rows at all, so a failed or
       rejected image is never silently retried into an infinite loop.
    2. History is append-only. Regenerating adds a row; nothing is edited or
       deleted, so every prompt and every image stays inspectable.
    """

    MAX_DEFINITION_CHARS = 400
    NO_TEXT_RULE = (
        'Do not render any text, letters, words or numbers in the image.'
    )

    # ---------- prompt building ----------

    @classmethod
    def build_prompt_seed(cls, card):
        """Derive the card-specific half of the prompt from the card's own text."""
        parts = [f'An illustration for a yoga study flashcard titled "{card.title}".']
        if card.phrase:
            parts.append(f'The Sanskrit term is "{card.phrase}".')
        if card.short_answer:
            parts.append(f'It means: {card.short_answer.strip()}')
        if card.definition:
            definition = card.definition.strip()
            if len(definition) > cls.MAX_DEFINITION_CHARS:
                definition = definition[: cls.MAX_DEFINITION_CHARS].rsplit(' ', 1)[0] + '...'
            parts.append(f'Context: {definition}')
        tags = [tag.name for tag in card.tags.all()]
        if tags:
            parts.append(f'Theme: {", ".join(tags)}.')
        parts.append(
            'Depict the concept symbolically through scenery, objects or a single '
            'figure. Suitable for print on a study card. ' + cls.NO_TEXT_RULE
        )
        return ' '.join(parts)

    @staticmethod
    def compose_prompt(seed, look_and_feel):
        """Join the card seed with the style guidance that applies to it."""
        seed = (seed or '').strip()
        look_and_feel = (look_and_feel or '').strip()
        if not look_and_feel:
            return seed
        return f'{seed}\n\nStyle: {look_and_feel}'

    # ---------- per-card model ----------

    @staticmethod
    def _version_group_of(card_or_group):
        return getattr(card_or_group, 'version_group', card_or_group)

    @classmethod
    def effective_model(cls, card_or_group):
        """
        The model a new generation for this card would use.

        Per-card choice wins over the global default, so one card can be tried
        against a different model without disturbing the rest of the deck.
        """
        version_group = cls._version_group_of(card_or_group)
        chosen = (
            CardImagePreference.objects
            .filter(version_group=version_group)
            .values_list('model', flat=True)
            .first()
        )
        if chosen and chosen.strip():
            return chosen.strip()
        return ImageGenerationSettings.load().model

    @classmethod
    def set_model(cls, card, model, user=None):
        """
        Remember a model choice for this card family.

        Blank clears the choice and returns the card to the global default.
        """
        preference, _ = CardImagePreference.objects.update_or_create(
            version_group=cls._version_group_of(card),
            defaults={'model': (model or '').strip(), 'updated_by': user},
        )
        return preference

    @classmethod
    def preview_prompt(cls, card, look_and_feel_override=''):
        """
        The prompt and model a new generation would use right now.

        `model_source` lets the UI say whether the model came from this card or
        from the global default, so changing it is an informed decision.
        """
        config = ImageGenerationSettings.load()
        look = (look_and_feel_override or '').strip() or config.look_and_feel
        seed = cls.build_prompt_seed(card)
        model = cls.effective_model(card)
        return {
            'prompt_seed': seed,
            'look_and_feel': look,
            'prompt': cls.compose_prompt(seed, look),
            'model': model,
            'model_source': 'card' if model != config.model else 'global',
            'global_model': config.model,
        }

    # ---------- queueing ----------

    @classmethod
    def queue(cls, card, prompt=None, look_and_feel_override='', model=None,
              requested_by=None, is_auto=False):
        """
        Add a generation to the queue. Always creates a new row.

        An explicit `prompt` is stored verbatim, so an admin can rewrite it
        completely; otherwise it is composed from the card text plus the
        effective look and feel.
        """
        config = ImageGenerationSettings.load()
        look = (look_and_feel_override or '').strip() or config.look_and_feel
        seed = cls.build_prompt_seed(card)
        resolved_prompt = (prompt or '').strip() or cls.compose_prompt(seed, look)

        # An explicit model is also remembered for this card, so choosing one and
        # regenerating is a single action rather than two. The bot passes none,
        # so automatic queueing never silently rewrites someone's choice.
        explicit_model = (model or '').strip()
        if explicit_model:
            cls.set_model(card, explicit_model, user=requested_by)
            resolved_model = explicit_model
        else:
            resolved_model = cls.effective_model(card)

        return CardImage.objects.create(
            version_group=card.version_group,
            card=card,
            status=CardImage.QUEUED,
            prompt=resolved_prompt,
            prompt_seed=seed,
            look_and_feel=look,
            look_and_feel_override=(look_and_feel_override or '').strip(),
            model=resolved_model,
            requested_by=requested_by,
            is_auto=is_auto,
        )

    @classmethod
    def queue_missing(cls, limit=None):
        """
        Queue a first image for every card family that has never had one.

        This is the "generate each new image once" guarantee: the exclusion is
        on *any* existing row for the version group, regardless of its status.
        A card whose generation failed permanently, or whose image was rejected,
        is not picked up again -- an admin regenerates it deliberately.
        """
        config = ImageGenerationSettings.load()
        if not (config.enabled and config.auto_generate_new_cards):
            return []

        cards = (
            Flashcard.objects.filter(is_active=True, is_live=True)
            .exclude(version_group__in=CardImage.objects.values('version_group'))
            .prefetch_related('tags')
            .order_by('created_at')
        )
        if limit is not None:
            cards = cards[:limit]

        return [cls.queue(card, is_auto=True) for card in cards]

    # ---------- running ----------

    @classmethod
    def claim_next(cls):
        """
        Atomically take the oldest queued row and mark it as generating.

        SELECT ... FOR UPDATE SKIP LOCKED means two bot runs cannot claim the
        same row, so a slow generation never gets sent to the provider twice.
        (SQLite ignores SKIP LOCKED; the transaction still serialises writes.)
        """
        with transaction.atomic():
            image = (
                CardImage.objects.select_for_update(skip_locked=True)
                .filter(status=CardImage.QUEUED)
                .order_by('created_at')
                .first()
            )
            if image is None:
                return None
            image.status = CardImage.GENERATING
            image.started_at = timezone.now()
            image.attempts += 1
            image.save(update_fields=['status', 'started_at', 'attempts', 'updated_at'])
            return image

    @classmethod
    def run(cls, image, client=None):
        """Generate one claimed image. Returns the updated row."""
        config = ImageGenerationSettings.load()
        client = client or OpenRouterClient()

        try:
            result = client.generate_image(image.prompt, image.model)
        except OpenRouterError as exc:
            return cls._record_failure(image, str(exc), config.max_attempts)

        filename = f'{slugify(image.card.title if image.card else "card") or "card"}-{uuid.uuid4().hex[:8]}.{result.extension}'
        image.image.save(filename, ContentFile(result.content), save=False)
        image.status = CardImage.SUCCEEDED
        image.error = ''
        image.finished_at = timezone.now()
        image.cost_usd = result.cost_usd
        image.provider_response_id = result.response_id
        image.save(update_fields=[
            'image', 'status', 'error', 'finished_at', 'cost_usd',
            'provider_response_id', 'updated_at',
        ])
        return image

    @classmethod
    def _record_failure(cls, image, message, max_attempts):
        """
        Requeue only while attempts remain, then stop for good.

        The attempt counter is incremented at claim time, so this caps the
        number of provider calls per row at max_attempts -- the other half of
        the no-runaway guarantee.
        """
        image.error = message[:2000]
        image.finished_at = timezone.now()
        if image.attempts < max_attempts:
            image.status = CardImage.QUEUED
        else:
            image.status = CardImage.FAILED
        image.save(update_fields=['error', 'status', 'finished_at', 'updated_at'])
        logger.warning(
            'Card image %s failed (attempt %s/%s): %s',
            image.pk, image.attempts, max_attempts, message[:200],
        )
        return image

    @classmethod
    def reset_stale(cls, older_than_minutes=30):
        """
        Return rows stranded in `generating` to the queue.

        A crashed or killed bot leaves rows mid-flight; without this they would
        block forever. Bounded by max_attempts like any other retry.
        """
        cutoff = timezone.now() - timedelta(minutes=older_than_minutes)
        stale = CardImage.objects.filter(status=CardImage.GENERATING, started_at__lt=cutoff)
        return stale.update(status=CardImage.QUEUED, updated_at=timezone.now())

    # ---------- acceptance ----------

    # "Accepted" is no longer a flag on the image. The card points at the image
    # it shows, so the pointer IS the acceptance, and setting it is the whole
    # operation.
    #
    # That deletes an invariant this code used to enforce by hand. One accepted
    # image per card family needed a transaction and select_for_update here,
    # purely because MySQL has no partial unique index to express it
    # declaratively. A row cannot hold two foreign keys, so the rule is now
    # structural and the machinery is gone.

    @staticmethod
    def _live_card(version_group):
        return Flashcard.objects.filter(
            version_group=version_group, is_live=True
        ).first()

    @classmethod
    def accept(cls, image, user=None):
        """
        Point the card's live version at this image.

        Older versions keep whatever they were showing: a version records the
        image chosen at the time, and an edit carries the pointer forward
        through create_new_version.

        `user` is accepted and ignored. Acceptance used to be audited on the
        image via accepted_by; there is no natural home for that now, because
        accepting does not create a card version. Kept in the signature so the
        call sites did not all have to change.
        """
        if image.status != CardImage.SUCCEEDED or not image.image:
            raise ValueError('Only a successfully generated image can be accepted.')
        card = cls._live_card(image.version_group)
        if card is None:
            raise ValueError('That card family no longer has a live version.')
        card.front_image = image
        card.save(update_fields=['front_image', 'updated_at'])
        return image

    @classmethod
    def unaccept(cls, image):
        """
        Stop showing this image. The row and its file are kept.

        Only the live version is cleared. An older version that pointed at this
        image keeps pointing at it, because that is what it was showing at the
        time and history is not rewritten.
        """
        Flashcard.objects.filter(
            version_group=image.version_group, is_live=True, front_image=image
        ).update(front_image=None)
        return image

    @staticmethod
    def accepted_for(version_group):
        """The image the live version of this card family is showing, or None."""
        card = Flashcard.objects.filter(
            version_group=version_group, is_live=True
        ).only('front_image').first()
        return card.front_image if card else None
