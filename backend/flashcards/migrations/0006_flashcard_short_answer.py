# Generated migration for adding short_answer field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0005_fix_version_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='flashcard',
            name='short_answer',
            field=models.TextField(blank=True, null=True, help_text='Brief answer or key points'),
        ),
    ]
