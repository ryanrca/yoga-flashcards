import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from flashcards.models import Flashcard, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed flashcards from JSON or export flashcards to JSON for backup'

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
            help='Import flashcards and tags from JSON into the database (default mode)'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file']).resolve()

        if options['pull'] and options['push']:
            raise CommandError('Choose only one mode: --pull (export) or --push (import).')

        mode = 'pull' if options['pull'] else 'push'
        if mode == 'pull':
            self._export_to_json(file_path)
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
            front_image=card_data.get('front_image') or None,
            back_image=card_data.get('back_image') or None,
            created_by=admin_user,
            is_active=card_data.get('is_active', True),
        )

        for tag_name in card_data.get('tags', []):
            if tag_name in tag_map:
                flashcard.tags.add(tag_map[tag_name])

        return flashcard

    # Export (backup) ---------------------------------------------------
    def _export_to_json(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)

        tags = list(Tag.objects.all().order_by('name').values('name', 'description'))

        flashcards = []
        queryset = Flashcard.objects.all().select_related('created_by').prefetch_related('tags').order_by('version_group', 'version_number')
        for card in queryset:
            flashcards.append({
                'id': card.id,
                'title': card.title,
                'phrase': card.phrase,
                'definition': card.definition,
                'short_answer': card.short_answer,
                'front_image': str(card.front_image) if card.front_image else None,
                'back_image': str(card.back_image) if card.back_image else None,
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
