from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from flashcards.models import Flashcard, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial data for the yoga flashcards application'

    def handle(self, *args, **options):
        # Create superuser if it doesn't exist (check both username and email for backward compatibility)
        if not User.objects.filter(username='admin').exists() and not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser(
                username='admin',  # Still need username for Django, but login will use email
                email='admin@example.com',
                password='admin123',
                role='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: admin@example.com / admin123')
            )
        else:
            # Update existing admin user's email if needed
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

        # Create test users for different roles
        test_users = [
            {
                'username': 'admin1',  # Internal username generated from email
                'email': 'admin1@example.com',
                'password': 'admin1',
                'role': 'admin',
                'first_name': 'Test',
                'last_name': 'Admin'
            },
            {
                'username': 'curator1',  # Internal username generated from email
                'email': 'curator1@example.com',
                'password': 'curator1',
                'role': 'curator',
                'first_name': 'Test',
                'last_name': 'Curator'
            },
            {
                'username': 'user1',  # Internal username generated from email
                'email': 'user1@example.com',
                'password': 'user1',
                'role': 'user',
                'first_name': 'Test',
                'last_name': 'User'
            }
        ]

        for user_data in test_users:
            # Check if user exists by either username or email
            if not User.objects.filter(username=user_data['username']).exists() and not User.objects.filter(email=user_data['email']).exists():
                if user_data['role'] == 'admin':
                    user = User.objects.create_superuser(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        role=user_data['role'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name']
                    )
                else:
                    user = User.objects.create_user(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        role=user_data['role'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name']
                    )
                self.stdout.write(
                    self.style.SUCCESS(f'Created {user_data["role"]} user: {user_data["email"]} / {user_data["password"]}')
                )
            else:
                # Update existing user's email if needed
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

        # Create initial tags
        tag_data = [
            {'name': '8 Limbs', 'description': 'The eight limbs of yoga according to Patanjali'},
            {'name': 'Yamas', 'description': 'The first limb - ethical restraints'},
            {'name': 'Niyamas', 'description': 'The second limb - observances'},
        ]

        created_tags = {}
        for tag_info in tag_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_info['name'],
                defaults={'description': tag_info['description']}
            )
            created_tags[tag_info['name']] = tag
            if created:
                self.stdout.write(f'Created tag: {tag.name}')
            else:
                self.stdout.write(f'Tag already exists: {tag.name}')

        # Initial flashcard data
        flashcard_data = [
            # 8 Limbs of Yoga
            {
                'title': 'Yama',
                'phrase': 'यम',
                'definition': 'The first limb of yoga, consisting of ethical restraints and moral disciplines that guide our interactions with others and the world.',
                'tags': ['8 Limbs', 'Yamas']
            },
            {
                'title': 'Niyama',
                'phrase': 'नियम',
                'definition': 'The second limb of yoga, consisting of observances and practices that guide our relationship with ourselves.',
                'tags': ['8 Limbs', 'Niyamas']
            },
            {
                'title': 'Asana',
                'phrase': 'आसन',
                'definition': 'The third limb of yoga, referring to the physical postures and seat for meditation.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Pranayama',
                'phrase': 'प्राणायाम',
                'definition': 'The fourth limb of yoga, the practice of breath control and extension of life force energy.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Pratyahara',
                'phrase': 'प्रत्याहार',
                'definition': 'The fifth limb of yoga, withdrawal of the senses from external objects to turn attention inward.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Dharana',
                'phrase': 'धारणा',
                'definition': 'The sixth limb of yoga, concentration and focused attention on a single object or point.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Dhyana',
                'phrase': 'ध्यान',
                'definition': 'The seventh limb of yoga, meditation and sustained awareness without effort.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Samadhi',
                'phrase': 'समाधि',
                'definition': 'The eighth and final limb of yoga, union and absorption in the object of meditation.',
                'tags': ['8 Limbs']
            },
            
            # The 5 Yamas
            {
                'title': 'Ahimsa',
                'phrase': 'अहिंसा',
                'definition': 'Non-violence and non-harming in thought, word, and action toward all living beings.',
                'tags': ['Yamas']
            },
            {
                'title': 'Satya',
                'phrase': 'सत्य',
                'definition': 'Truthfulness and honesty in speech and thought, living in alignment with truth.',
                'tags': ['Yamas']
            },
            {
                'title': 'Asteya',
                'phrase': 'अस्तेय',
                'definition': 'Non-stealing, not taking what is not freely given, including time, energy, and material possessions.',
                'tags': ['Yamas']
            },
            {
                'title': 'Brahmacharya',
                'phrase': 'ब्रह्मचर्य',
                'definition': 'Moderation and conservation of energy, traditionally celibacy, but more broadly mindful use of sexual energy.',
                'tags': ['Yamas']
            },
            {
                'title': 'Aparigraha',
                'phrase': 'अपरिग्रह',
                'definition': 'Non-possessiveness and non-attachment, freedom from greed and the desire to accumulate.',
                'tags': ['Yamas']
            },
            
            # The 5 Niyamas
            {
                'title': 'Saucha',
                'phrase': 'शौच',
                'definition': 'Cleanliness and purity of body, mind, and environment, both external and internal purification.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Santosha',
                'phrase': 'संतोष',
                'definition': 'Contentment and satisfaction with what is, finding joy and peace in the present moment.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Tapas',
                'phrase': 'तपस्',
                'definition': 'Disciplined practice and austerity, the burning enthusiasm and self-discipline to maintain practice.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Svadhyaya',
                'phrase': 'स्वाध्याय',
                'definition': 'Self-study and study of sacred texts, introspection and learning about the true Self.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Ishvara Pranidhana',
                'phrase': 'ईश्वर प्रणिधान',
                'definition': 'Surrender to the Divine, devotion and dedication of all actions to a higher power.',
                'tags': ['Niyamas']
            },
        ]

        created_count = 0
        for card_data in flashcard_data:
            # Check if card already exists
            if not Flashcard.objects.filter(title=card_data['title'], is_active=True).exists():
                flashcard = Flashcard.objects.create(
                    title=card_data['title'],
                    phrase=card_data['phrase'],
                    definition=card_data['definition'],
                    created_by=admin_user
                )
                
                # Add tags
                for tag_name in card_data['tags']:
                    flashcard.tags.add(created_tags[tag_name])
                
                created_count += 1
                self.stdout.write(f'Created flashcard: {flashcard.title}')
            else:
                self.stdout.write(f'Flashcard already exists: {card_data["title"]}')

        self.stdout.write(
            self.style.SUCCESS(f'Initial data setup completed. Created {created_count} flashcards.')
        )
