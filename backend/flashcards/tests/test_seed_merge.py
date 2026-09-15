"""
Tests for `seed_initial_data --merge`.

The point of merge mode is that adding new cards never detaches the generated
images from the cards that already exist, which is exactly what the default
--push mode does.
"""
import json

import pytest
from django.core.management import call_command
from django.core.files.base import ContentFile
from io import StringIO

from flashcards.models import CardImage, CardImagePreference, Flashcard, Tag
from flashcards.services import CardImageService
from .factories import FlashcardFactory, TagFactory
from .test_card_images import PNG_BYTES


def write_json(tmp_path, cards, tags=None):
    payload = {
        'tags': tags if tags is not None else [{'name': 'Yamas', 'description': 'Restraints'}],
        'flashcards': cards,
    }
    path = tmp_path / 'cards.json'
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return str(path)


def card_payload(title, **overrides):
    payload = {
        'title': title,
        'phrase': 'phrase',
        'short_answer': 'short',
        'definition': 'definition',
        'front_image': None,
        'back_image': None,
        'tags': ['Yamas'],
        'is_active': True,
    }
    payload.update(overrides)
    return payload


def run_merge(path, **kwargs):
    out = StringIO()
    call_command('seed_initial_data', '--merge', '-f', path, stdout=out, **kwargs)
    return out.getvalue()


@pytest.mark.django_db
class TestMergeAddsWithoutDestroying:
    def test_creates_cards_that_do_not_exist(self, tmp_path):
        path = write_json(tmp_path, [card_payload('Ahimsa'), card_payload('Satya')])
        run_merge(path)
        assert set(Flashcard.objects.filter(is_live=True).values_list('title', flat=True)) == {'Ahimsa', 'Satya'}

    def test_existing_cards_keep_their_version_group(self, tmp_path):
        card = FlashcardFactory(title='Ahimsa', phrase='p', short_answer='s', definition='d')
        original = card.version_group
        path = write_json(tmp_path, [card_payload('Ahimsa', phrase='p', short_answer='s', definition='d', tags=[]),
                                     card_payload('Brand New')])
        run_merge(path)
        card.refresh_from_db()
        assert card.version_group == original

    def test_generated_images_stay_attached(self, tmp_path):
        """The whole reason merge mode exists."""
        card = FlashcardFactory(title='Ahimsa')
        image = CardImage.objects.create(
            version_group=card.version_group, card=card,
            status=CardImage.SUCCEEDED, prompt='p', model='m',
        )
        image.image.save('x.png', ContentFile(PNG_BYTES), save=True)
        CardImageService.accept(image)

        path = write_json(tmp_path, [card_payload('Ahimsa'), card_payload('Brahman')])
        run_merge(path)

        live = Flashcard.objects.filter(title='Ahimsa', is_live=True).first()
        accepted = CardImageService.accepted_for(live.version_group)
        assert accepted is not None, 'the accepted image must still belong to the card'
        assert accepted.pk == image.pk

    def test_per_card_model_survives(self, tmp_path):
        card = FlashcardFactory(title='Ahimsa')
        CardImageService.set_model(card, 'black-forest-labs/flux.2-max')
        path = write_json(tmp_path, [card_payload('Ahimsa'), card_payload('Atman')])
        run_merge(path)
        live = Flashcard.objects.filter(title='Ahimsa', is_live=True).first()
        assert CardImageService.effective_model(live) == 'black-forest-labs/flux.2-max'

    def test_nothing_is_deleted(self, tmp_path):
        """A card missing from the JSON is left alone, not removed."""
        FlashcardFactory(title='Keeper')
        TagFactory(name='Untouched')
        path = write_json(tmp_path, [card_payload('Ahimsa')])
        run_merge(path)
        assert Flashcard.objects.filter(title='Keeper', is_live=True).exists()
        assert Tag.objects.filter(name='Untouched').exists()

    def test_new_tags_are_created(self, tmp_path):
        path = write_json(
            tmp_path,
            [card_payload('Brahman', tags=['Deities'])],
            tags=[{'name': 'Deities', 'description': 'Gods'}],
        )
        run_merge(path)
        assert Tag.objects.filter(name='Deities').exists()
        assert Flashcard.objects.get(title='Brahman').tags.filter(name='Deities').exists()


@pytest.mark.django_db
class TestMergeUpdates:
    def test_changed_text_creates_a_new_version(self, tmp_path):
        card = FlashcardFactory(title='Ahimsa', definition='old text')
        original = card.version_group
        path = write_json(tmp_path, [card_payload('Ahimsa', definition='new text', tags=[])])
        run_merge(path)

        live = Flashcard.objects.filter(title='Ahimsa', is_live=True).first()
        assert live.definition == 'new text'
        assert live.version_group == original
        assert live.version_number == 2
        # The previous wording is still in the history.
        assert Flashcard.objects.filter(version_group=original, definition='old text').exists()

    def test_unchanged_cards_are_left_alone(self, tmp_path):
        card = FlashcardFactory(title='Ahimsa', phrase='p', short_answer='s', definition='d')
        tag = TagFactory(name='Yamas')
        card.tags.set([tag])
        path = write_json(tmp_path, [card_payload('Ahimsa', phrase='p', short_answer='s', definition='d')])
        output = run_merge(path)
        card.refresh_from_db()
        assert card.version_number == 1
        assert '1 unchanged' in output

    def test_update_does_not_wipe_an_uploaded_image(self, tmp_path):
        """The JSON carries nulls for images; those must not overwrite a real upload."""
        card = FlashcardFactory(title='Ahimsa', definition='old')
        card.front_image.save('front.png', ContentFile(PNG_BYTES), save=True)
        path = write_json(tmp_path, [card_payload('Ahimsa', definition='new', tags=[])])
        run_merge(path)
        live = Flashcard.objects.filter(title='Ahimsa', is_live=True).first()
        assert live.front_image, 'the uploaded image should survive a text update'


@pytest.mark.django_db
class TestMergeDryRun:
    def test_dry_run_writes_nothing(self, tmp_path):
        FlashcardFactory(title='Ahimsa', definition='old')
        path = write_json(tmp_path, [card_payload('Ahimsa', definition='new'), card_payload('Brand New')])
        output = run_merge(path, dry_run=True)
        assert 'would create: Brand New' in output
        assert 'would update: Ahimsa' in output
        assert not Flashcard.objects.filter(title='Brand New').exists()
        assert Flashcard.objects.get(title='Ahimsa').definition == 'old'


@pytest.mark.django_db
class TestPushIsStillDestructive:
    def test_push_replaces_everything(self, tmp_path):
        """Documents the behaviour merge exists to avoid."""
        card = FlashcardFactory(title='Ahimsa')
        original = card.version_group
        path = write_json(tmp_path, [card_payload('Ahimsa')])
        out = StringIO()
        call_command('seed_initial_data', '--push', '-f', path, stdout=out)
        live = Flashcard.objects.filter(title='Ahimsa', is_live=True).first()
        assert live.version_group != original, 'push recreates cards, detaching their images'

    def test_modes_are_mutually_exclusive(self, tmp_path):
        from django.core.management.base import CommandError
        path = write_json(tmp_path, [card_payload('Ahimsa')])
        with pytest.raises(CommandError):
            call_command('seed_initial_data', '--merge', '--push', '-f', path)
