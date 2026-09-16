import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import transaction

from flashcards.models import (
    Flashcard, Tag, CardImage, CardImagePreference, DailyCard, CardUsageLog,
    ImageGenerationSettings,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Seed flashcards from JSON, merge new ones in without deleting, '
        'or export flashcards to JSON for backup'
    )

    def add_arguments(self, parser):
        default_path = Path(__file__).resolve().parent / 'data' / 'flashcards.json'
        parser.add_argument(
            '-f', '--file',
            dest='file',
            default=str(default_path),
            help='Path to flashcards JSON file (default: management/commands/data/flashcards.json)'
        )
        parser.add_argument(
            '--pull',
            action='store_true',
            help='Export flashcards and tags from the database to JSON'
        )
        parser.add_argument(
            '--push',
            action='store_true',
            help='Replace ALL flashcards and tags with the JSON contents (default mode). Destructive.'
        )
        parser.add_argument(
            '--merge',
            action='store_true',
            help=(
                'Add new cards and update changed ones without deleting anything. '
                'Existing cards keep their version_group, so generated images stay attached.'
            )
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what --merge or --scorched-earth would do without writing anything.'
        )
        parser.add_argument(
            '--scorched-earth',
            action='store_true',
            help=(
                'Erase every card, version, tag, generated image, per-card setting and '
                'media file, then reseed from JSON as if the app were new. Requires --confirm.'
            )
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Required to actually run --scorched-earth. Without it the command refuses.'
        )
        parser.add_argument(
            '--reset-settings',
            action='store_true',
            help='With --scorched-earth, also reset the global look and feel and model to defaults.'
        )
        parser.add_argument(
            '--no-queue-images',
            action='store_true',
            help='With --scorched-earth, do not queue image generation for the reseeded cards.'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file']).resolve()

        chosen = [m for m in ('pull', 'push', 'merge', 'scorched_earth') if options[m]]
        if len(chosen) > 1:
            raise CommandError(
                'Choose only one mode: --pull (export), --push (replace), --merge (add and '
                'update) or --scorched-earth (erase everything and reseed).'
            )

        mode = chosen[0] if chosen else 'push'
        if mode == 'pull':
            self._export_to_json(file_path)
        elif mode == 'merge':
            self._merge_from_json(file_path, dry_run=options['dry_run'])
        elif mode == 'scorched_earth':
            self._scorched_earth(
                file_path,
                confirm=options['confirm'],
                dry_run=options['dry_run'],
                reset_settings=options['reset_settings'],
                queue_images=not options['no_queue_images'],
            )
        else:
            self._import_from_json(file_path)

    # Import (seed) -----------------------------------------------------
    def _import_from_json(self, file_path: Path):
        data = self._load_json(file_path)
        flashcards_data = data.get('flashcards', [])
        tags_data = data.get('tags', [])

        if not flashcards_data:
            raise CommandError('No flashcards found in the JSON file.')

        # An export written by --pull contains every version of every card. Import
        # creates one flat live row per entry, so without this filter a pull/push
        # round trip would resurrect superseded versions as duplicate live cards.
        # Entries with no is_live key (hand-written seed data) are kept.
        skipped = [c for c in flashcards_data if c.get('is_live') is False]
        if skipped:
            flashcards_data = [c for c in flashcards_data if c.get('is_live') is not False]
            self.stdout.write(f'Skipping {len(skipped)} superseded version(s) from the export')

        self.stdout.write(self.style.WARNING(
            'Replacing ALL flashcards and tags. Existing cards get new version_group '
            'values, which detaches any generated images from them. Use --merge to add '
            'cards without this.'
        ))
        self.stdout.write('Clearing existing flashcards and tags...')
        Flashcard.objects.all().delete()
        Tag.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        admin_user = self._ensure_admin_user()
        self._ensure_test_users()

        tag_map = self._create_tags(tags_data)

        created_count = 0
        for card_data in flashcards_data:
            flashcard = self._create_flashcard(card_data, admin_user, tag_map)
            created_count += 1
            self.stdout.write(f'Created flashcard: {flashcard.title}')

        self.stdout.write(self.style.SUCCESS(f'Import complete. Created {created_count} flashcards.'))

    def _ensure_admin_user(self):
        if not User.objects.filter(username='admin').exists() and not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin@example.com / admin123'))
        else:
            try:
                admin_user = User.objects.get(username='admin')
                if admin_user.email != 'admin@example.com':
                    admin_user.email = 'admin@example.com'
                    admin_user.save()
                    self.stdout.write('Updated admin user email to admin@example.com')
                else:
                    self.stdout.write('Admin user already exists')
            except User.DoesNotExist:
                admin_user = User.objects.get(email='admin@example.com')
                self.stdout.write('Admin user already exists')
        return admin_user

    def _ensure_test_users(self):
        test_users = [
            {
                'username': 'admin1',
                'email': 'admin1@example.com',
                'password': 'admin1',
                'role': 'admin',
                'first_name': 'Test',
                'last_name': 'Admin'
            },
            {
                'username': 'curator1',
                'email': 'curator1@example.com',
                'password': 'curator1',
                'role': 'curator',
                'first_name': 'Test',
                'last_name': 'Curator'
            },
            {
                'username': 'user1',
                'email': 'user1@example.com',
                'password': 'user1',
                'role': 'user',
                'first_name': 'Test',
                'last_name': 'User'
            }
        ]

        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists() and not User.objects.filter(email=user_data['email']).exists():
                if user_data['role'] == 'admin':
                    User.objects.create_superuser(**user_data)
                else:
                    User.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(f'Created {user_data["role"]} user: {user_data["email"]} / {user_data["password"]}'))
            else:
                try:
                    existing_user = User.objects.get(username=user_data['username'])
                    if existing_user.email != user_data['email']:
                        existing_user.email = user_data['email']
                        existing_user.save()
                        self.stdout.write(f'Updated {user_data["username"]} email to {user_data["email"]}')
                    else:
                        self.stdout.write(f'User {user_data["email"]} already exists')
                except User.DoesNotExist:
                    self.stdout.write(f'User {user_data["email"]} already exists')

    def _create_tags(self, tags_data):
        tag_map = {}
        for tag_info in tags_data:
            name = tag_info.get('name')
            if not name:
                continue
            description = tag_info.get('description', '')
            tag, _ = Tag.objects.get_or_create(name=name, defaults={'description': description})
            if description and tag.description != description:
                tag.description = description
                tag.save(update_fields=['description'])
            tag_map[name] = tag
            self.stdout.write(f'Ensured tag: {name}')
        return tag_map

    def _create_flashcard(self, card_data, admin_user, tag_map):
        flashcard = Flashcard.objects.create(
            title=card_data.get('title', ''),
            phrase=card_data.get('phrase', ''),
            short_answer=card_data.get('short_answer', ''),
            definition=card_data.get('definition', ''),
            created_by=admin_user,
            is_active=card_data.get('is_active', True),
        )

        # Images are set after the card exists: a media row is keyed to the
        # card's version_group, which is only assigned when the card is created.
        front = self._media_for_path(card_data.get('front_image'), flashcard)
        back = self._media_for_path(card_data.get('back_image'), flashcard)
        if front or back:
            flashcard.front_image = front
            flashcard.back_image = back
            flashcard.save(update_fields=['front_image', 'back_image'])

        for tag_name in card_data.get('tags', []):
            if tag_name in tag_map:
                flashcard.tags.add(tag_map[tag_name])

        return flashcard

    @staticmethod
    def _media_for_path(path, card):
        """
        Turn a media path from the JSON into a row in the media table.

        The seed format is unchanged - it still carries plain paths - because
        only the location of the pointer moved, not the files. The row is marked
        UPLOADED: a path sitting in a seed file did not come from the bot, and
        there is no prompt or model to record for it.
        """
        path = (path or '').strip()
        if not path:
            return None
        media, _ = CardImage.objects.get_or_create(
            version_group=card.version_group,
            image=path,
            defaults={'status': CardImage.UPLOADED},
        )
        return media

    # Merge (additive) --------------------------------------------------
    def _merge_from_json(self, file_path: Path, dry_run=False):
        """
        Add new cards and update changed ones. Never deletes.

        Existing cards are matched by title and keep their version_group, so
        generated images, accepted images and per-card model choices stay
        attached. A changed card goes through create_new_version(), which is the
        app's own convention for edits, so the old text stays in the history.
        """
        data = self._load_json(file_path)
        flashcards_data = [
            c for c in data.get('flashcards', []) if c.get('is_live') is not False
        ]
        if not flashcards_data:
            raise CommandError('No flashcards found in the JSON file.')

        admin_user = self._ensure_admin_user() if not dry_run else None
        tag_map = {} if dry_run else self._create_tags(data.get('tags', []))
        if dry_run:
            existing_tags = set(Tag.objects.values_list('name', flat=True))
            for tag_info in data.get('tags', []):
                if tag_info.get('name') and tag_info['name'] not in existing_tags:
                    self.stdout.write(f'  would create tag: {tag_info["name"]}')

        live = {
            card.title: card
            for card in Flashcard.objects.filter(is_active=True, is_live=True).prefetch_related('tags')
        }

        created = updated = unchanged = 0
        for card_data in flashcards_data:
            title = (card_data.get('title') or '').strip()
            if not title:
                continue
            existing = live.get(title)

            if existing is None:
                if dry_run:
                    self.stdout.write(f'  would create: {title}')
                else:
                    self._create_flashcard(card_data, admin_user, tag_map)
                    self.stdout.write(self.style.SUCCESS(f'Created: {title}'))
                created += 1
                continue

            changes = self._card_differences(existing, card_data)
            if not changes:
                unchanged += 1
                continue

            if dry_run:
                self.stdout.write(f'  would update: {title} ({", ".join(changes)})')
            else:
                self._update_flashcard(existing, card_data, admin_user, tag_map)
                self.stdout.write(f'Updated: {title} ({", ".join(changes)})')
            updated += 1

        summary = (
            f'{created} created, {updated} updated, {unchanged} unchanged. '
            'Nothing was deleted.'
        )
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Dry run: {summary} No changes were written.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Merge complete. {summary}'))

    @staticmethod
    def _card_differences(card, card_data):
        """Which text fields differ. Images are ignored; the JSON rarely carries them."""
        incoming_tags = sorted(t for t in (card_data.get('tags') or []))
        current_tags = sorted(t.name for t in card.tags.all())
        fields = {
            'phrase': ((card.phrase or ''), (card_data.get('phrase') or '')),
            'short_answer': ((card.short_answer or ''), (card_data.get('short_answer') or '')),
            'definition': ((card.definition or ''), (card_data.get('definition') or '')),
        }
        changed = [name for name, (current, incoming) in fields.items() if current.strip() != incoming.strip()]
        if current_tags != incoming_tags:
            changed.append('tags')
        return changed

    def _update_flashcard(self, card, card_data, admin_user, tag_map):
        """
        Record the change as a new version of the same card.

        Deliberately does not touch front_image/back_image: the JSON carries
        nulls for almost every card, and copying those over would wipe images
        someone uploaded.
        """
        tags = [tag_map[name] for name in (card_data.get('tags') or []) if name in tag_map]
        return card.create_new_version(
            updated_by=admin_user or card.created_by,
            title=card_data.get('title', card.title),
            phrase=card_data.get('phrase', card.phrase),
            definition=card_data.get('definition', card.definition),
            short_answer=card_data.get('short_answer', card.short_answer),
            tags=tags,
        )

    # Scorched earth ----------------------------------------------------
    #
    # Card media lives in exactly two directories. `avatars/` belongs to
    # UserProfile and is deliberately NOT in this list: wiping the deck must
    # never touch people's profile pictures.
    CARD_MEDIA_DIRS = ('card_images/generated', 'flashcard_images')

    def _scorched_earth(self, file_path: Path, confirm=False, dry_run=False,
                        reset_settings=False, queue_images=True):
        """
        Erase every trace of the current deck and reseed from JSON.

        Removes cards and all their versions, tags, generated images and their
        files, per-card model choices, the daily-card picks and the usage log
        that drives rotation. Users, their avatars and their accounts are left
        alone, and so is the global image configuration unless --reset-settings
        is passed.

        Afterwards every card is version 1 with no media, and each is queued for
        a fresh image.
        """
        data = self._load_json(file_path)
        flashcards_data = [c for c in data.get('flashcards', []) if c.get('is_live') is not False]
        if not flashcards_data:
            raise CommandError('No flashcards found in the JSON file. Refusing to erase.')

        inventory = {
            'flashcards (all versions)': Flashcard.objects.count(),
            'tags': Tag.objects.count(),
            'generated images': CardImage.objects.count(),
            'per-card model choices': CardImagePreference.objects.count(),
            'daily card picks': DailyCard.objects.count(),
            'card usage log rows': CardUsageLog.objects.count(),
        }
        media_files = self._card_media_files()
        # Some names come from database references to files that are already
        # gone, so only count the ones actually present on disk.
        present = [n for n in media_files if default_storage.exists(n)]

        self.stdout.write(self.style.WARNING('Scorched earth. This will delete:'))
        for label, count in inventory.items():
            self.stdout.write(f'  {count:>5}  {label}')
        self.stdout.write(f'  {len(present):>5}  media files on disk')
        self.stdout.write(f'  and reseed {len(flashcards_data)} cards from {file_path.name}')
        self.stdout.write('  preserved: user accounts, profile avatars'
                          + ('' if reset_settings else ', global image settings'))

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run: nothing was deleted or written.'))
            return

        if not confirm:
            raise CommandError(
                'Refusing to erase without --confirm. Re-run with --scorched-earth --confirm, '
                'or add --dry-run to see the plan.'
            )

        # Database first, in one transaction, so a failure leaves the deck intact.
        # Files are removed afterwards: the filesystem is not transactional, and
        # an orphaned file is a far smaller problem than a missing row.
        with transaction.atomic():
            CardImage.objects.all().delete()
            CardImagePreference.objects.all().delete()
            DailyCard.objects.all().delete()
            CardUsageLog.objects.all().delete()
            # Cascades clean the flashcard/tag and favourite-card join tables.
            Flashcard.objects.all().delete()
            Tag.objects.all().delete()
            if reset_settings:
                ImageGenerationSettings.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Database cleared.'))

        removed = self._delete_card_media(media_files)
        self.stdout.write(self.style.SUCCESS(f'Removed {removed} media file(s).'))

        admin_user = self._ensure_admin_user()
        self._ensure_test_users()
        tag_map = self._create_tags(data.get('tags', []))

        # Image paths are stripped deliberately. A JSON produced by --pull carries
        # whatever media the deck had at the time, and every one of those files has
        # just been deleted -- honouring them would leave a "fresh" card pointing at
        # something that no longer exists.
        cards = [
            self._create_flashcard(dict(card_data, front_image=None, back_image=None),
                                   admin_user, tag_map)
            for card_data in flashcards_data
        ]
        carried = sum(1 for c in flashcards_data if c.get('front_image') or c.get('back_image'))
        if carried:
            self.stdout.write(
                f'Ignored stale image path(s) on {carried} card(s) in the JSON; '
                'a scorched deck starts with no media.'
            )
        self.stdout.write(self.style.SUCCESS(f'Reseeded {len(cards)} cards at version 1 with no media.'))

        queued = 0
        if queue_images:
            # Imported here to keep the module import graph shallow.
            from flashcards.services import CardImageService

            config = ImageGenerationSettings.load()
            for card in cards:
                CardImageService.queue(card, is_auto=True)
                queued += 1
            self.stdout.write(self.style.SUCCESS(f'Queued {queued} card(s) for image generation.'))
            if not config.enabled:
                self.stdout.write(self.style.WARNING(
                    'Image generation is disabled in the global settings, so the bot will not '
                    'process this queue until it is switched back on.'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'Scorched earth complete. {len(cards)} cards, '
            f'{len(tag_map)} tags, {queued} generation(s) queued.'
        ))

    def _card_media_files(self):
        """
        Every card media file currently on disk.

        Union of what the database references and whatever else is sitting in
        the two card media directories, so images orphaned by an earlier run get
        cleared too. Strictly limited to those directories.
        """
        # One media table means one place to look. This used to sweep the
        # CardImage rows and then both Flashcard image columns separately,
        # because a file could be referenced from either.
        names = set()
        for path in CardImage.objects.exclude(image='').values_list('image', flat=True):
            if path:
                names.add(path)
        for directory in self.CARD_MEDIA_DIRS:
            try:
                _, files = default_storage.listdir(directory)
            except (FileNotFoundError, NotADirectoryError, OSError):
                continue
            for name in files:
                names.add(f'{directory}/{name}')
        return sorted(names)

    def _delete_card_media(self, names):
        """Delete the given media files, refusing anything outside the card directories."""
        media_root = Path(settings.MEDIA_ROOT).resolve()
        removed = 0
        for name in names:
            if not any(name.startswith(f'{d}/') for d in self.CARD_MEDIA_DIRS):
                self.stdout.write(self.style.WARNING(f'  skipped (outside card media): {name}'))
                continue
            # Belt and braces: never follow a path out of MEDIA_ROOT.
            try:
                resolved = (media_root / name).resolve()
                resolved.relative_to(media_root)
            except ValueError:
                self.stdout.write(self.style.WARNING(f'  skipped (escapes MEDIA_ROOT): {name}'))
                continue
            try:
                if default_storage.exists(name):
                    default_storage.delete(name)
                    removed += 1
            except OSError as exc:
                self.stdout.write(self.style.WARNING(f'  could not delete {name}: {exc}'))
        return removed

    # Export (backup) ---------------------------------------------------
    def _export_to_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)

        tags = list(Tag.objects.all().order_by('name').values('name', 'description'))

        flashcards = []
        queryset = (
            Flashcard.objects.all()
            .select_related('created_by', 'front_image', 'back_image')
            .prefetch_related('tags')
            .order_by('version_group', 'version_number')
        )
        for card in queryset:
            flashcards.append({
                'id': card.id,
                'title': card.title,
                'phrase': card.phrase,
                'definition': card.definition,
                'short_answer': card.short_answer,
                # Still a plain path, so the JSON format did not change when the
                # pointer moved onto a media row.
                'front_image': card.front_image.image.name if (card.front_image and card.front_image.image) else None,
                'back_image': card.back_image.image.name if (card.back_image and card.back_image.image) else None,
                'tags': [tag.name for tag in card.tags.all()],
                'is_active': card.is_active,
                'version_group': str(card.version_group),
                'version_number': card.version_number,
                'is_live': card.is_live,
                'created_by': card.created_by.username if card.created_by else None,
                'created_at': card.created_at.isoformat(),
                'updated_at': card.updated_at.isoformat(),
            })

        payload = {
            'tags': tags,
            'flashcards': flashcards,
        }

        with file_path.open('w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f'Exported {len(flashcards)} flashcards to {file_path}'))

    # Helpers -----------------------------------------------------------
    def _load_json(self, file_path: Path):
        if not file_path.exists():
            raise CommandError(f'JSON file not found: {file_path}')
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
