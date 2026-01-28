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
            help='Path to flashcards JSON file (default: management/data/flashcards.json)'
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

        created_tags = {}
        for tag_info in tag_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_info['name'],
                defaults={'description': tag_info['description']}
            )
            created_tags[tag_info['name']] = tag
            if created:
                self.stdout.write(f'Created tag: {tag.name}')

        # Initial flashcard data
        flashcard_data = [
            # The 8 Limbs of Yoga
            {
                'title': 'Yamas',
                'phrase': 'यम',
                'short_answer': 'Ethical restraints on "how we relate to others".',
                'definition': 'Yamas are the social disciplines or restraints that guide our interactions with the world around us with specific practices: (Ahimsa, Satya, Asteya, Brahmacarya, and Aparigraha) that help us act with awareness rather than reacting out of habit or vice. Sometimes called the "Do nots".',
                'tags': ['8 Limbs']
                # ready
            },
            {
                'title': 'Niyamas',
                'phrase': 'नियम',
                'short_answer': 'Personal observances or "how we relate to ourselves".',
                'definition': 'These are internal practices meant to improve our own character and being. They consist of Sauca, Samtosa, Tapas, Svadhaya, and Isharapranidhana. These habits, behaviors, and observances outline guidance for healthy living, spiritual enlightenment, and existence with liberation and ease. These are the "To Do\'s".',
                'tags': ['8 Limbs']
                # ready
            },
            {
                'title': 'Asana',
                'phrase': 'आसन',
                'short_answer': 'Physical postures; literally meaning "to sit" or "being seated".',
                'definition': 'Originally referring to sitting with a master to receive knowledge, it has evolved into the physical practice of postures. The goal is to find a balance between Sthira (steadiness/effort) and Sukha (comfort/ease) so the body is alert but unstressed.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Pranayama',
                'phrase': 'प्राणायाम',
                'short_answer': 'Breath control and the regulation of life force.',
                'definition': 'This practice involves joining the breath with movement to integrate the body and mind. It includes techniques like Ujjayi (calming) or Kapalabhati (energizing) to help the mind become slower, deeper, and more focused.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Pratyahara',
                'phrase': 'प्रत्याहार',
                'short_answer': 'Withdrawal of the senses; not chasing the "shiny object".',
                'definition': 'It is the practice of filtering out external distractions to focus inward. For example, when a siren goes off during savasana, you use Pratyahara to stay present in your practice rather than following the noise.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Dharana',
                'phrase': 'धारणा',
                'short_answer': 'Concentration; holding the mind in one direction.',
                'definition': 'We create the conditions to focus the mind\'s attention on a single object, like the breath, a candle, or a mandala. This prevents the "monkey mind" from jumping in many different directions.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Dhyana',
                'phrase': 'ध्यान',
                'short_answer': 'Meditation; a continuous flow of concentration.',
                'definition': 'In this state, the mind moves in one direction like a quiet river. You perceive an object and focus only on it, forming a deep communication where nothing else is happening.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Samadhi',
                'phrase': 'समाधि',
                'short_answer': 'Union; becoming one with the object of meditation.',
                'definition': 'This is the experience of realizing non-dualistic existence, seeing things clearly without the Maya (illusion). It is pure flow where you are no longer a separate physical creature but are united with the divine or the fabric of the universe.',
                'tags': ['8 Limbs']
            },

            # The 5 Yamas
            {
                'title': 'Ahimsa',
                'phrase': 'अहिंसा',
                'short_answer': 'Non-violence; do no harm.',
                'definition': 'This is the practice of justice and non-violence toward all beings. In yoga class, it means finding a balance with Satya—for example, not pushing yourself or a student so hard that it causes injury, but also not avoiding the truth of where growth is needed.',
                'tags': ['Yamas']
            },
            {
                'title': 'Satya',
                'phrase': 'सत्य',
                'short_answer': 'Truthfulness.',
                'definition': 'This involves being honest with ourselves and others. As a teacher, it means providing "radical candor" or a "+1 nudge" to help students see their flaws and grow, provided the feedback comes from a sincere, caring place.',
                'tags': ['Yamas']
            },
            {
                'title': 'Asteya',
                'phrase': 'अस्तेय',
                'short_answer': 'Non-stealing.',
                'definition': 'Beyond just not taking physical objects, it involves not stealing others\' time or energy. It is a reminder to avoid vices and distractions, focusing instead on what we have earned.',
                'tags': ['Yamas']
            },
            {
                'title': 'Brahmacarya',
                'phrase': 'ब्रह्मचर्य',
                'short_answer': 'Responsible behavior; moderation of the senses.',
                'definition': 'Often interpreted as respect for family life and not overdoing sexual pleasure, it is a subtle call to move toward the truth through responsible, disciplined behavior.',
                'tags': ['Yamas']
            },
            {
                'title': 'Aparigraha',
                'phrase': 'अपरिग्रह',
                'short_answer': 'Non-greed or non-attachment; only taking what is necessary.',
                'definition': 'This means not taking advantage of a situation and only taking what you have earned. It is the practice of non-coveting, which helps us stay away from addiction and ego-centrism.',
                'tags': ['Yamas']
            },

            # The 5 Niyamas
            {
                'title': 'Sauca',
                'phrase': 'शौच',
                'short_answer': 'Purity, cleanliness, and clarity of body and mind.',
                'definition': 'Purity of mind, speach and body. Keeping physical cleanliness through asanas, pranayama, and proper eating, and maintaining cleanliness in our physical environment. Purity of speech comes from being truthful and using words that are not hurtful, or distressing to others or self. Purity of thoughts through reflection, meditation, and calmness. It is about getting rid of "rubbish" in the mind and body through healthy habits.',
                'tags': ['Niyamas']
                # Ready
            },
            {
                'title': 'Santosha',
                'phrase': 'संतोष',
                'short_answer': 'Contentment; being okay with what is.',
                'definition': 'To be content with what we already have and to accept outcomes even when they don\'t meet our expectations. It is the appreciation of our current situtation rather than focusing on how we wish it to be.',
                'tags': ['Niyamas']
                # Ready
            },
            {
                'title': 'Tapas',
                'phrase': 'तपस्',
                'short_answer': 'The passion, motivation and discipline that drives spiritual or physical pratice.',
                'definition': 'The activity of "heating" the body through asana and pranayama to cleanse it. Includes, the discipline and actions toward spiritual rituals and healthy habits, to sustain a healthy lifestyle and burn away impurities physically and spiritually.',
                'tags': ['Niyamas']
                # Ready
            },
            {
                'title': 'Svadhyaya',
                'phrase': 'स्वाध्याय',
                'short_answer': 'The pratice of self-study, self examination, and spirtual inquiry.',
                'definition': 'The study of ancient texts and the examination of one\'s own inner dialogue. It is an inquiry into who is "living in you" and identifying the labels we carry that are not our true identity. It is the endless pursuit of learning about ourselves and spiritual frameworks.',
                'tags': ['Niyamas']
                # Ready
            },
            {
                'title': 'Isvara-pranidhana',
                'phrase': 'ईश्वरप्रणिधान',
                'short_answer': 'Devotion to the "absolute Brahma", who is free from all hinderences and karma. Devotion to A higher power.',
                'definition': 'Some interpertitation mean to "lay all your actions at the feet of God," by offering the "fruits of your devotion" to something larger than yourself. It is the realization and acceptance of the part of ourselves that does not change, and surrendering to the divine part of us that is uneffected by our samskara.',
                'tags': ['Niyamas']
                # needs a second pass
            },
            {
                'title': 'Yoga',
                'phrase': '',
                'short_answer': 'To "yoke" or "union" - to become one with our core essence.',
                'definition': 'Yoga is a vast group of physical, mental, spiritual practices and philosophy originating in ancient India, aimed at controlling body and mind in order to attain liberation (moksha), health and connection with the universe. Yoga means to unify with all possible states of awareness, whether ordinary or extraordinary.',
                'tags': ['8 Limbs']
                # Ready
            },

        ]

        created_count = 0
        for card_data in flashcard_data:
            flashcard = Flashcard.objects.create(
                title=card_data['title'],
                phrase=card_data['phrase'],
                short_answer=card_data['short_answer'],
                definition=card_data['definition'],
                created_by=admin_user
            )

            # Add tags
            for tag_name in card_data['tags']:
                flashcard.tags.add(created_tags[tag_name])

            created_count += 1
            self.stdout.write(f'Created flashcard: {flashcard.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Initial data setup completed. Created {created_count} flashcards.')
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
