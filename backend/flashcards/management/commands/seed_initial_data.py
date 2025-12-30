from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from flashcards.models import Flashcard, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Erase and recreate initial data for the yoga flashcards application'

    def handle(self, *args, **options):
        # Clear existing data
        self.stdout.write('Clearing existing flashcards and tags...')
        Flashcard.objects.all().delete()
        Tag.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Cleared existing data'))

        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists() and not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: admin@example.com / admin123')
            )
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
            {'name': 'Yamas', 'description': 'Ethical restraints - how we relate to others'},
            {'name': 'Niyamas', 'description': 'Personal observances - how we relate to ourselves'},
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

        # Initial flashcard data
        flashcard_data = [
            # The 8 Limbs of Yoga
            {
                'title': 'Yamas',
                'phrase': 'यम',
                'short_answer': 'Ethical restraints or "how we relate to others".',
                'definition': 'These are the social disciplines that guide our interactions with the world around us. They include five specific practices (Ahimsa, Satya, Asteya, Brahmacarya, and Aparigraha) that help us act with awareness rather than reacting out of habit or vice.',
                'tags': ['8 Limbs']
            },
            {
                'title': 'Niyamas',
                'phrase': 'नियम',
                'short_answer': 'Personal observances or "how we relate to ourselves".',
                'definition': 'These are internal practices and disciplines meant to improve our own character and being. They consist of Sauca, Samtosa, Tapas, Svadhaya, and Isharapranidhana, focusing on internal cleanliness, contentment, and devotion.',
                'tags': ['8 Limbs']
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
                'short_answer': 'Cleanliness; purity of body and mind.',
                'definition': 'This includes internal cleanliness (proper eating and breathing) and external cleanliness in our physical environment. It is about getting rid of "rubbish" in the body through healthy habits.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Samtosa',
                'phrase': 'संतोष',
                'short_answer': 'Contentment; being okay with what is.',
                'definition': 'To be content with what we already have and to accept outcomes even when they don\'t meet our expectations. It is the appreciation of what did happen rather than focusing on what we wanted to happen.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Tapas',
                'phrase': 'तपस्',
                'short_answer': 'Discipline or "heat"; keeping the body fit.',
                'definition': 'The activity of "heating" the body through posture and breath to cleanse it. It is the effort and discipline required to maintain health and burn away impurities.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Svadhaya',
                'phrase': 'स्वाध्याय',
                'short_answer': 'Self-study; inquiry and examination.',
                'definition': 'This is the study of ancient texts and the examination of one\'s own inner dialogue. It is an inquiry into who is "living in you" and identifying the labels we carry that are not our true identity.',
                'tags': ['Niyamas']
            },
            {
                'title': 'Isharapranidhana',
                'phrase': 'ईश्वरप्रणिधान',
                'short_answer': 'Surrender to a higher power.',
                'definition': 'Literally meaning to "lay all your actions at the feet of God," it involves offering the "fruits of your labor" to something larger than yourself. It is the realization that you are not the most important thing and surrendering to the divine.',
                'tags': ['Niyamas']
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
