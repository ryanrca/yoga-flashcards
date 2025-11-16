from django.db import migrations
import uuid


def fix_duplicate_version_groups(apps, schema_editor):
    """Ensure each card has a unique version_group."""
    Flashcard = apps.get_model('flashcards', 'Flashcard')
    
    # Assign a unique version_group to each live card
    for card in Flashcard.objects.filter(is_live=True):
        card.version_group = uuid.uuid4()
        card.version_number = 1
        card.save()


def reverse_fix(apps, schema_editor):
    """Reverse migration - nothing to do."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0004_populate_version_groups'),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_version_groups, reverse_fix),
    ]
