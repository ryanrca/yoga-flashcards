"""
Tests for `seed_initial_data --scorched-earth`.

Two things matter most: that it erases everything it claims to, including files
on disk, and that it leaves user accounts and their avatars alone.
"""
import json
from io import StringIO

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.storage import default_storage

from flashcards.models import (
    CardImage, CardImagePreference, CardUsageLog, DailyCard, Flashcard,
    ImageGenerationSettings, Tag,
)
from flashcards.services import CardImageService
from .factories import CardUsageLogFactory, DailyCardFactory, FlashcardFactory, TagFactory
from .test_card_images import PNG_BYTES
from users.tests.factories import UserFactory


def write_json(tmp_path, titles):
    payload = {
        'tags': [{'name': 'Yamas', 'description': 'Restraints'}],
        'flashcards': [{
            'title': t, 'phrase': 'p', 'short_answer': 's', 'definition': 'd',
            'front_image': None, 'back_image': None, 'tags': ['Yamas'], 'is_active': True,
        } for t in titles],
    }
    path = tmp_path / 'cards.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return str(path)


def run(path, *args, **kwargs):
    out = StringIO()
    call_command('seed_initial_data', '--scorched-earth', '-f', path, *args, stdout=out, **kwargs)
    return out.getvalue()


def populated_deck():
    """A deck with history, images, files, preferences and rotation state."""
    card = FlashcardFactory(title='Old Card')
    card.create_new_version(updated_by=card.created_by, title='Old Card')  # a second version
    image = CardImage.objects.create(
        version_group=card.version_group, card=card,
        status=CardImage.SUCCEEDED, prompt='p', model='m',
    )
    image.image.save('generated.png', ContentFile(PNG_BYTES), save=True)
    CardImageService.accept(image)
    CardImageService.set_model(card, 'black-forest-labs/flux.2-max')
    DailyCardFactory(card=card)
    CardUsageLogFactory(card=card)
    return card, image


@pytest.mark.django_db
class TestSafety:
    def test_refuses_without_confirm(self, tmp_path):
        FlashcardFactory(title='Old Card')
        path = write_json(tmp_path, ['New Card'])
        with pytest.raises(CommandError, match='--confirm'):
            run(path)
        assert Flashcard.objects.filter(title='Old Card').exists()

    def test_dry_run_changes_nothing(self, tmp_path):
        card, image = populated_deck()
        path = write_json(tmp_path, ['New Card'])
        output = run(path, '--dry-run')
        assert 'Dry run' in output
        assert Flashcard.objects.filter(pk=card.pk).exists()
        assert CardImage.objects.filter(pk=image.pk).exists()
        assert default_storage.exists(image.image.name)

    def test_refuses_an_empty_json(self, tmp_path):
        FlashcardFactory(title='Old Card')
        path = write_json(tmp_path, [])
        with pytest.raises(CommandError, match='Refusing to erase'):
            run(path, '--confirm')
        assert Flashcard.objects.filter(title='Old Card').exists()

    def test_modes_are_mutually_exclusive(self, tmp_path):
        path = write_json(tmp_path, ['A'])
        with pytest.raises(CommandError):
            call_command('seed_initial_data', '--scorched-earth', '--merge', '-f', path)


@pytest.mark.django_db
class TestErasesEverything:
    def test_removes_all_card_data(self, tmp_path):
        _, image = populated_deck()
        TagFactory(name='Leftover')
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')

        assert not Flashcard.objects.filter(title='Old Card').exists()
        assert not Tag.objects.filter(name='Leftover').exists()
        # The old image is gone. Rows that remain are the freshly queued ones,
        # which scorched earth creates on purpose.
        assert not CardImage.objects.filter(pk=image.pk).exists()
        assert not CardImage.objects.exclude(status=CardImage.QUEUED).exists()
        assert CardImagePreference.objects.count() == 0
        assert DailyCard.objects.count() == 0
        assert CardUsageLog.objects.count() == 0

    def test_removes_history_not_just_live_versions(self, tmp_path):
        card, _ = populated_deck()
        assert Flashcard.objects.filter(version_group=card.version_group).count() == 2
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')
        assert Flashcard.objects.filter(version_group=card.version_group).count() == 0

    def test_deletes_media_files_from_disk(self, tmp_path):
        _, image = populated_deck()
        name = image.image.name
        assert default_storage.exists(name)
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')
        assert not default_storage.exists(name)

    def test_deletes_uploaded_card_images_too(self, tmp_path):
        card = FlashcardFactory(title='Uploaded')
        card.front_image.save('front.png', ContentFile(PNG_BYTES), save=True)
        name = card.front_image.name
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')
        assert not default_storage.exists(name)

    def test_sweeps_orphaned_files_left_by_earlier_runs(self, tmp_path):
        orphan = default_storage.save('card_images/generated/orphan.png', ContentFile(PNG_BYTES))
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')
        assert not default_storage.exists(orphan)


    def test_stale_image_paths_in_the_json_are_ignored(self, tmp_path):
        """
        A JSON produced by --pull carries the media the deck had at the time.
        Those files are deleted by this very command, so honouring the paths
        would leave a "fresh" card pointing at something that no longer exists.
        """
        payload = {
            'tags': [{'name': 'Yamas', 'description': 'Restraints'}],
            'flashcards': [{
                'title': 'Carries Stale Paths', 'phrase': 'p', 'short_answer': 's',
                'definition': 'd',
                'front_image': 'flashcard_images/long_gone.jpg',
                'back_image': 'flashcard_images/also_gone.jpg',
                'tags': ['Yamas'], 'is_active': True,
            }],
        }
        path = tmp_path / 'stale.json'
        path.write_text(json.dumps(payload), encoding='utf-8')
        output = run(str(path), '--confirm')

        card = Flashcard.objects.get(title='Carries Stale Paths')
        assert not card.front_image, 'a scorched deck must start with no media'
        assert not card.back_image
        assert 'stale image path' in output.lower()


@pytest.mark.django_db
class TestPreservesWhatItShould:
    def test_leaves_users_and_avatars_alone(self, tmp_path):
        """Avatars live in a different directory and belong to people, not cards."""
        from users.models import UserProfile

        user = UserFactory(role='curator')
        profile = UserProfile.objects.create(user=user)
        profile.avatar.save('face.png', ContentFile(PNG_BYTES), save=True)
        avatar = profile.avatar.name

        populated_deck()
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')

        user.refresh_from_db()
        profile.refresh_from_db()
        assert user.is_active
        assert default_storage.exists(avatar), 'a profile avatar must survive a deck wipe'

    def test_keeps_global_image_settings_by_default(self, tmp_path):
        config = ImageGenerationSettings.load()
        config.look_and_feel = 'Ink wash on rice paper.'
        config.model = 'black-forest-labs/flux.2-max'
        config.save()

        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm')

        config = ImageGenerationSettings.load()
        assert config.look_and_feel == 'Ink wash on rice paper.'
        assert config.model == 'black-forest-labs/flux.2-max'

    def test_reset_settings_restores_defaults(self, tmp_path):
        config = ImageGenerationSettings.load()
        config.look_and_feel = 'Ink wash on rice paper.'
        config.save()
        path = write_json(tmp_path, ['New Card'])
        run(path, '--confirm', '--reset-settings')
        assert ImageGenerationSettings.load().look_and_feel == ImageGenerationSettings.DEFAULT_LOOK_AND_FEEL


@pytest.mark.django_db
class TestReseeds:
    def test_cards_come_back_as_version_one_with_no_media(self, tmp_path):
        populated_deck()
        path = write_json(tmp_path, ['Alpha', 'Beta', 'Gamma'])
        run(path, '--confirm')

        cards = Flashcard.objects.all()
        assert cards.count() == 3, 'one row per card, no history'
        for card in cards:
            assert card.version_number == 1
            assert card.is_live and card.is_active
            assert not card.front_image
            assert not card.back_image

    def test_every_card_is_queued_for_an_image(self, tmp_path):
        path = write_json(tmp_path, ['Alpha', 'Beta', 'Gamma'])
        run(path, '--confirm')
        queued = CardImage.objects.filter(status=CardImage.QUEUED)
        assert queued.count() == 3
        assert all(image.is_auto for image in queued)
        # Each queue row points at a card that actually exists.
        groups = set(Flashcard.objects.values_list('version_group', flat=True))
        assert set(queued.values_list('version_group', flat=True)) == groups

    def test_no_queue_images_skips_generation(self, tmp_path):
        path = write_json(tmp_path, ['Alpha'])
        run(path, '--confirm', '--no-queue-images')
        assert CardImage.objects.count() == 0

    def test_queues_even_when_auto_generate_is_off(self, tmp_path):
        """The operator asked for a queue explicitly; the bot toggle governs the bot."""
        config = ImageGenerationSettings.load()
        config.auto_generate_new_cards = False
        config.save()
        path = write_json(tmp_path, ['Alpha'])
        run(path, '--confirm')
        assert CardImage.objects.filter(status=CardImage.QUEUED).count() == 1

    def test_warns_when_generation_is_disabled(self, tmp_path):
        config = ImageGenerationSettings.load()
        config.enabled = False
        config.save()
        path = write_json(tmp_path, ['Alpha'])
        output = run(path, '--confirm')
        assert 'disabled' in output.lower()

    def test_tags_are_recreated(self, tmp_path):
        path = write_json(tmp_path, ['Alpha'])
        run(path, '--confirm')
        assert Tag.objects.filter(name='Yamas').exists()
        assert Flashcard.objects.get(title='Alpha').tags.filter(name='Yamas').exists()

    def test_admin_and_test_users_still_exist_afterwards(self, tmp_path):
        from users.models import User
        path = write_json(tmp_path, ['Alpha'])
        run(path, '--confirm')
        assert User.objects.filter(email='admin@example.com').exists()
