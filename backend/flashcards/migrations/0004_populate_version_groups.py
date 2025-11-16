from django.db import migrations
import uuid


def populate_version_groups(apps, schema_editor):
    """Set unique version_group for each existing card."""
    Flashcard = apps.get_model('flashcards', 'Flashcard')
    
    # Get all unique version_group values to see if they're all the same
    for card in Flashcard.objects.all():
        # Always regenerate to ensure uniqueness
        card.version_group = uuid.uuid4()
        card.is_live = True
        card.version_number = 1
        card.save()


def reverse_populate(apps, schema_editor):
    """Reverse migration - nothing to do."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0003_rename_version_flashcard_version_number_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_version_groups, reverse_populate),
    ]
