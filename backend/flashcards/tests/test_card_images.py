"""
Tests for AI card image generation.

The provider is always faked: no test makes a network call.
"""
import base64

import pytest
from django.core.files.base import ContentFile
from rest_framework import status

from flashcards.models import CardImage, ImageGenerationSettings
from flashcards.openrouter import OpenRouterClient, OpenRouterError
from flashcards.services import CardImageService
from .factories import CardImageFactory, FlashcardFactory, TagFactory
from users.tests.factories import UserFactory

# A real 1x1 PNG, so anything that inspects the file gets valid image bytes.
PNG_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)
PNG_BYTES = base64.b64decode(PNG_B64)


class FakeImage:
    def __init__(self, cost=0.03):
        self.content = PNG_BYTES
        self.content_type = 'image/png'
        self.cost_usd = cost
        self.response_id = 'gen-123'
        self.extension = 'png'


class FakeClient:
    """Stand-in for OpenRouterClient that records what it was asked to do."""

    def __init__(self, error=None):
        self.error = error
        self.calls = []
        self.is_configured = True

    def generate_image(self, prompt, model):
        self.calls.append({'prompt': prompt, 'model': model})
        if self.error:
            raise OpenRouterError(self.error)
        return FakeImage()


def succeeded_image(card, **kwargs):
    image = CardImageFactory(card=card, status=CardImage.SUCCEEDED, **kwargs)
    image.image.save('test.png', ContentFile(PNG_BYTES), save=True)
    return image


@pytest.mark.django_db
class TestPromptSeeding:
    """The prompt is seeded from the card's own text."""

    def test_seed_uses_card_text(self):
        tag = TagFactory(name='Yamas')
        card = FlashcardFactory(
            title='Ahimsa', phrase='अहिंसा',
            short_answer='Non-violence; do no harm.',
            definition='The practice of justice and non-violence toward all beings.',
            tags=[tag],
        )
        seed = CardImageService.build_prompt_seed(card)
        assert 'Ahimsa' in seed
        assert 'अहिंसा' in seed
        assert 'Non-violence' in seed
        assert 'justice and non-violence' in seed
        assert 'Yamas' in seed
        # The card carries its own typography; the image must not add lettering.
        assert 'Do not render any text' in seed

    def test_seed_handles_card_without_phrase(self):
        card = FlashcardFactory(title='Yoga', phrase='', short_answer='', definition='Union.')
        seed = CardImageService.build_prompt_seed(card)
        assert 'Yoga' in seed
        assert 'Sanskrit term' not in seed

    def test_long_definition_is_truncated(self):
        card = FlashcardFactory(definition='word ' * 400)
        seed = CardImageService.build_prompt_seed(card)
        assert '...' in seed
        assert len(seed) < 1200

    def test_global_look_and_feel_is_appended(self):
        config = ImageGenerationSettings.load()
        config.look_and_feel = 'Bold woodcut print, two colours.'
        config.save()
        card = FlashcardFactory()
        image = CardImageService.queue(card)
        assert 'Bold woodcut print, two colours.' in image.prompt
        assert image.look_and_feel == 'Bold woodcut print, two colours.'

    def test_per_image_override_replaces_global(self):
        config = ImageGenerationSettings.load()
        config.look_and_feel = 'Global style.'
        config.save()
        card = FlashcardFactory()
        image = CardImageService.queue(card, look_and_feel_override='Just this one: charcoal sketch.')
        assert 'charcoal sketch' in image.prompt
        assert 'Global style.' not in image.prompt
        assert image.effective_look_and_feel == 'Just this one: charcoal sketch.'

    def test_explicit_prompt_is_stored_verbatim(self):
        card = FlashcardFactory()
        image = CardImageService.queue(card, prompt='A single lotus on still water.')
        assert image.prompt == 'A single lotus on still water.'
        # The seed is still recorded, so the admin can see what it would have been.
        assert image.prompt_seed


@pytest.mark.django_db
class TestGenerateOnlyOnce:
    """The bot generates each card's first image exactly once."""

    def test_queues_one_image_per_card(self):
        FlashcardFactory.create_batch(3)
        queued = CardImageService.queue_missing()
        assert len(queued) == 3
        assert CardImage.objects.count() == 3

    def test_second_run_queues_nothing(self):
        FlashcardFactory.create_batch(3)
        CardImageService.queue_missing()
        assert CardImageService.queue_missing() == []
        assert CardImage.objects.count() == 3

    def test_failed_card_is_not_requeued_automatically(self):
        """A permanently failed image must not be picked up again by the bot."""
        card = FlashcardFactory()
        CardImageFactory(card=card, status=CardImage.FAILED, attempts=3)
        assert CardImageService.queue_missing() == []

    def test_rejected_image_is_not_requeued_automatically(self):
        card = FlashcardFactory()
        succeeded_image(card, is_accepted=False)
        assert CardImageService.queue_missing() == []

    def test_new_card_gets_queued(self):
        existing = FlashcardFactory()
        CardImageService.queue_missing()
        fresh = FlashcardFactory()
        queued = CardImageService.queue_missing()
        assert [image.version_group for image in queued] == [fresh.version_group]
        assert existing.version_group not in [image.version_group for image in queued]

    def test_editing_a_card_does_not_requeue_it(self):
        """Editing creates a new Flashcard row; images follow the version group."""
        card = FlashcardFactory()
        CardImageService.queue_missing()
        card.create_new_version(updated_by=card.created_by, title='Edited title')
        assert CardImageService.queue_missing() == []

    def test_auto_queue_respects_settings(self):
        FlashcardFactory()
        config = ImageGenerationSettings.load()
        config.auto_generate_new_cards = False
        config.save()
        assert CardImageService.queue_missing() == []

        config.auto_generate_new_cards = True
        config.enabled = False
        config.save()
        assert CardImageService.queue_missing() == []

    def test_limit_bounds_the_queue(self):
        FlashcardFactory.create_batch(5)
        assert len(CardImageService.queue_missing(limit=2)) == 2


@pytest.mark.django_db
class TestClaimAndRun:
    def test_claim_marks_generating_and_counts_the_attempt(self):
        card = FlashcardFactory()
        CardImageService.queue(card)
        claimed = CardImageService.claim_next()
        assert claimed.status == CardImage.GENERATING
        assert claimed.attempts == 1
        assert claimed.started_at is not None

    def test_claim_does_not_return_the_same_row_twice(self):
        CardImageService.queue(FlashcardFactory())
        first = CardImageService.claim_next()
        assert CardImageService.claim_next() is None
        assert first is not None

    def test_claim_returns_none_when_queue_is_empty(self):
        assert CardImageService.claim_next() is None

    def test_run_saves_the_image(self):
        card = FlashcardFactory()
        CardImageService.queue(card)
        image = CardImageService.claim_next()
        client = FakeClient()
        image = CardImageService.run(image, client=client)
        assert image.status == CardImage.SUCCEEDED
        assert image.image
        assert image.cost_usd is not None
        assert image.error == ''
        assert len(client.calls) == 1
        assert client.calls[0]['model'] == 'black-forest-labs/flux.2-pro'

    def test_failure_requeues_while_attempts_remain(self):
        CardImageService.queue(FlashcardFactory())
        image = CardImageService.claim_next()
        image = CardImageService.run(image, client=FakeClient(error='boom'))
        assert image.status == CardImage.QUEUED
        assert 'boom' in image.error

    def test_failure_stops_permanently_at_max_attempts(self):
        """The other half of no-runaway: a bounded number of provider calls."""
        config = ImageGenerationSettings.load()
        config.max_attempts = 2
        config.save()
        CardImageService.queue(FlashcardFactory())
        client = FakeClient(error='boom')

        for _ in range(5):
            image = CardImageService.claim_next()
            if image is None:
                break
            CardImageService.run(image, client=client)

        image = CardImage.objects.get()
        assert image.status == CardImage.FAILED
        assert image.attempts == 2
        assert len(client.calls) == 2

    def test_stale_generating_rows_are_requeued(self):
        from datetime import timedelta
        from django.utils import timezone

        image = CardImageFactory(status=CardImage.GENERATING)
        CardImage.objects.filter(pk=image.pk).update(
            started_at=timezone.now() - timedelta(hours=2)
        )
        assert CardImageService.reset_stale(older_than_minutes=30) == 1
        image.refresh_from_db()
        assert image.status == CardImage.QUEUED


@pytest.mark.django_db
class TestAcceptance:
    def test_accept_marks_the_image(self):
        card = FlashcardFactory()
        image = succeeded_image(card)
        admin = UserFactory(role='admin')
        CardImageService.accept(image, user=admin)
        image.refresh_from_db()
        assert image.is_accepted
        assert image.accepted_by == admin

    def test_accepting_unaccepts_the_previous_one(self):
        card = FlashcardFactory()
        first = succeeded_image(card)
        second = succeeded_image(card)
        CardImageService.accept(first)
        CardImageService.accept(second)
        first.refresh_from_db()
        second.refresh_from_db()
        assert not first.is_accepted
        assert second.is_accepted
        assert CardImage.objects.filter(
            version_group=card.version_group, is_accepted=True
        ).count() == 1

    def test_cannot_accept_an_image_that_never_generated(self):
        image = CardImageFactory(status=CardImage.QUEUED)
        with pytest.raises(ValueError):
            CardImageService.accept(image)

    def test_history_survives_regeneration(self):
        card = FlashcardFactory()
        CardImageService.queue(card, prompt='first attempt')
        CardImageService.queue(card, prompt='second attempt')
        prompts = list(
            CardImage.objects.filter(version_group=card.version_group)
            .order_by('created_at').values_list('prompt', flat=True)
        )
        assert prompts == ['first attempt', 'second attempt']


@pytest.mark.django_db
class TestVisibility:
    """Images reach non-admins only once accepted; prompts never do."""

    def test_unaccepted_image_is_not_exposed(self, api_client):
        card = FlashcardFactory()
        succeeded_image(card)
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/cards/{card.id}/')
        assert response.data['generated_image'] is None

    def test_accepted_image_is_exposed(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card)
        CardImageService.accept(image)
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        response = api_client.get(f'/api/cards/{card.id}/')
        assert response.data['generated_image']
        assert '.png' in response.data['generated_image']

    def test_card_payload_never_contains_a_prompt(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card, prompt='secret prompt text')
        CardImageService.accept(image)
        user = UserFactory(role='user')
        api_client.force_authenticate(user=user)
        body = str(api_client.get(f'/api/cards/{card.id}/').data)
        assert 'secret prompt text' not in body
        assert 'prompt' not in api_client.get(f'/api/cards/{card.id}/').data

    def test_daily_card_exposes_the_accepted_image(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card)
        CardImageService.accept(image)
        response = api_client.get('/api/dailycard/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['generated_image']
        assert 'prompt' not in response.data


@pytest.mark.django_db
class TestImageApiPermissions:
    """Everything image-related is admin-only, including for curators."""

    def _card_with_image(self):
        card = FlashcardFactory()
        return card, succeeded_image(card)

    @pytest.mark.parametrize('role', ['user', 'curator'])
    def test_non_admin_cannot_list_card_images(self, api_client, role):
        card, _ = self._card_with_image()
        api_client.force_authenticate(user=UserFactory(role=role))
        response = api_client.get(f'/api/cards/{card.id}/images/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('role', ['user', 'curator'])
    def test_non_admin_cannot_queue_generation(self, api_client, role):
        card, _ = self._card_with_image()
        api_client.force_authenticate(user=UserFactory(role=role))
        response = api_client.post(f'/api/cards/{card.id}/images/', {}, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('role', ['user', 'curator'])
    def test_non_admin_cannot_accept(self, api_client, role):
        _, image = self._card_with_image()
        api_client.force_authenticate(user=UserFactory(role=role))
        response = api_client.post(f'/api/card-images/{image.id}/accept/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('role', ['user', 'curator'])
    def test_non_admin_cannot_read_settings(self, api_client, role):
        api_client.force_authenticate(user=UserFactory(role=role))
        assert api_client.get('/api/image-settings/').status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_read_images(self, api_client):
        card, _ = self._card_with_image()
        response = api_client.get(f'/api/cards/{card.id}/images/')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestImageApi:
    def test_admin_sees_history_and_prompt_preview(self, api_client):
        card = FlashcardFactory(title='Ahimsa')
        succeeded_image(card, prompt='an earlier prompt')
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.get(f'/api/cards/{card.id}/images/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['images']) == 1
        assert response.data['images'][0]['prompt'] == 'an earlier prompt'
        assert 'Ahimsa' in response.data['preview']['prompt']
        assert response.data['preview']['model'] == 'black-forest-labs/flux.2-pro'

    def test_admin_queues_generation_without_calling_the_provider(self, api_client):
        card = FlashcardFactory()
        admin = UserFactory(role='admin')
        api_client.force_authenticate(user=admin)
        response = api_client.post(
            f'/api/cards/{card.id}/images/',
            {'prompt': 'custom prompt', 'model': 'black-forest-labs/flux.2-max'},
            format='json',
        )
        assert response.status_code == status.HTTP_201_CREATED
        image = CardImage.objects.get()
        assert image.status == CardImage.QUEUED
        assert image.prompt == 'custom prompt'
        assert image.model == 'black-forest-labs/flux.2-max'
        assert image.requested_by == admin
        assert not image.is_auto

    def test_queueing_is_refused_when_generation_is_disabled(self, api_client):
        config = ImageGenerationSettings.load()
        config.enabled = False
        config.save()
        card = FlashcardFactory()
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.post(f'/api/cards/{card.id}/images/', {}, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT
        assert CardImage.objects.count() == 0

    def test_accept_endpoint(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card)
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.post(f'/api/card-images/{image.id}/accept/')
        assert response.status_code == status.HTTP_200_OK
        image.refresh_from_db()
        assert image.is_accepted

    def test_unaccept_endpoint_keeps_the_row(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card)
        CardImageService.accept(image)
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.post(f'/api/card-images/{image.id}/unaccept/')
        assert response.status_code == status.HTTP_200_OK
        image.refresh_from_db()
        assert not image.is_accepted
        assert CardImage.objects.filter(pk=image.pk).exists()

    def test_regenerate_creates_a_new_row(self, api_client):
        card = FlashcardFactory()
        image = succeeded_image(card, prompt='original prompt')
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.post(f'/api/card-images/{image.id}/regenerate/', {}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert CardImage.objects.filter(version_group=card.version_group).count() == 2
        assert response.data['prompt'] == 'original prompt'
        assert response.data['status'] == CardImage.QUEUED

    def test_settings_round_trip(self, api_client):
        admin = UserFactory(role='admin')
        api_client.force_authenticate(user=admin)
        response = api_client.put(
            '/api/image-settings/',
            {'look_and_feel': 'Ink wash on rice paper.', 'model': 'black-forest-labs/flux.2-max'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        config = ImageGenerationSettings.load()
        assert config.look_and_feel == 'Ink wash on rice paper.'
        assert config.model == 'black-forest-labs/flux.2-max'
        assert config.updated_by == admin

    def test_settings_reject_absurd_max_attempts(self, api_client):
        api_client.force_authenticate(user=UserFactory(role='admin'))
        response = api_client.put('/api/image-settings/', {'max_attempts': 99}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestOpenRouterParsing:
    """Response parsing, without touching the network."""

    def test_parses_images_endpoint_shape(self):
        payload = {
            'data': [{'b64_json': PNG_B64, 'media_type': 'image/png'}],
            'usage': {'cost': 0.03},
            'id': 'gen-abc',
        }
        result = OpenRouterClient._parse(payload)
        assert result.content == PNG_BYTES
        assert result.extension == 'png'
        assert result.cost_usd == 0.03
        assert result.response_id == 'gen-abc'

    def test_parses_chat_completions_shape(self):
        """Some image models answer through chat completions instead."""
        payload = {
            'choices': [{
                'message': {
                    'images': [{'image_url': {'url': f'data:image/webp;base64,{PNG_B64}'}}]
                }
            }],
        }
        result = OpenRouterClient._parse(payload)
        assert result.content == PNG_BYTES
        assert result.extension == 'webp'

    def test_response_without_an_image_raises(self):
        with pytest.raises(OpenRouterError):
            OpenRouterClient._parse({'choices': [{'message': {'content': 'sorry'}}]})

    def test_client_without_a_key_refuses_to_call(self, settings):
        settings.OPENROUTER_API_KEY = ''
        client = OpenRouterClient()
        assert not client.is_configured
        with pytest.raises(OpenRouterError):
            client.generate_image('prompt', 'model')
