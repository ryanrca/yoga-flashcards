from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cards.models import Card, Tag, CardVersion


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **options):
        # Create admin user if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write('Created admin user with password: admin123')
        else:
            admin_user = User.objects.get(username='admin')
            # Reset password in case it was changed
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Reset admin password to: admin123')
        sample_tags = [
            'Asana', 'Pranayama', 'Philosophy', 'Sanskrit', 'Anatomy'
        ]
        
        tags = []
        for tag_name in sample_tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {tag_name}')
        
        # Create sample cards
        sample_cards = [
            {
                'title': 'Downward Facing Dog',
                'phrase': 'Adho Mukha Svanasana',
                'definition': 'A foundational yoga pose that strengthens the arms and legs while stretching the hamstrings and calves.',
                'tags': [tags[0], tags[3]]  # Asana, Sanskrit
            },
            {
                'title': 'Three-Part Breath',
                'phrase': 'Dirga Pranayama',
                'definition': 'A breathing technique that involves deep breathing into the belly, ribs, and chest in three distinct parts.',
                'tags': [tags[1], tags[3]]  # Pranayama, Sanskrit
            },
            {
                'title': 'Eight Limbs of Yoga',
                'phrase': 'Ashtanga',
                'definition': 'The eight-fold path of yoga as outlined by Patanjali in the Yoga Sutras, including ethical guidelines, physical practices, and spiritual disciplines.',
                'tags': [tags[2], tags[3]]  # Philosophy, Sanskrit
            },
            {
                'title': 'Warrior I',
                'phrase': 'Virabhadrasana I',
                'definition': 'A standing pose that strengthens the legs and opens the hips and chest, named after the fierce warrior Virabhadra.',
                'tags': [tags[0], tags[3]]  # Asana, Sanskrit
            },
            {
                'title': 'Sun Salutation',
                'phrase': 'Surya Namaskara',
                'definition': 'A flowing sequence of poses that warms up the body and honors the sun, traditionally practiced at sunrise.',
                'tags': [tags[0], tags[3]]  # Asana, Sanskrit
            }
        ]
        
        for card_data in sample_cards:
            # Check if card already exists
            existing_card = Card.objects.filter(
                title=card_data['title'],
                deleted_at__isnull=True
            ).first()
            
            if not existing_card:
                card = Card.objects.create(
                    title=card_data['title'],
                    phrase=card_data['phrase'],
                    definition=card_data['definition'],
                    created_by=admin_user
                )
                
                # Add tags
                card.tags.set(card_data['tags'])
                
                # Create initial version
                CardVersion.objects.create(
                    card=card,
                    title=card.title,
                    phrase=card.phrase,
                    definition=card.definition,
                    created_by=admin_user,
                    version_number=1
                )
                
                self.stdout.write(f'Created card: {card.title}')
            else:
                self.stdout.write(f'Card already exists: {card_data["title"]}')
        
        self.stdout.write(
            self.style.SUCCESS('Sample data seeding complete!')
        )
