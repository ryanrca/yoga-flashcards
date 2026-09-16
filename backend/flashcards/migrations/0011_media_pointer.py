"""
Cards point at media instead of storing it.

Hand-written rather than generated. makemigrations proposed `AlterField` on
flashcard.front_image and back_image, which would try to turn a varchar column
holding media paths into a bigint foreign key. MySQL cannot cast that, and even
where it could the paths would be destroyed. So the new columns are added
alongside, backfilled, and then swapped into place.

Ordering matters in two spots: the RunPython step reads `is_accepted`, so it has
to run before that field is dropped, and the index on (version_group,
is_accepted) has to be removed before the column it covers.
"""
from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    Flashcard = apps.get_model('flashcards', 'Flashcard')
    CardImage = apps.get_model('flashcards', 'CardImage')

    # Anything a person uploaded becomes a row in the media table, because media
    # now lives in exactly one place. Status is written as a literal: historical
    # models carry no class constants.
    for field, pointer in (('front_image', 'front_media'), ('back_image', 'back_media')):
        rows = Flashcard.objects.exclude(**{field: ''}).exclude(**{f'{field}__isnull': True})
        for card in rows:
            path = getattr(card, field)
            if not path:
                continue
            media, _ = CardImage.objects.get_or_create(
                version_group=card.version_group,
                image=path,
                defaults={'status': 'uploaded', 'prompt': '', 'model': ''},
            )
            Flashcard.objects.filter(pk=card.pk).update(**{pointer: media})

    # An accepted image becomes the live version's pointer. Only the live one:
    # the old schema recorded acceptance per card family, not per version, so
    # there is nothing to say what an older version was showing.
    for image in CardImage.objects.filter(is_accepted=True):
        Flashcard.objects.filter(
            version_group=image.version_group, is_live=True
        ).update(front_media=image)


def backwards(apps, schema_editor):
    """
    Best effort. The paths come back, but which image was accepted does not:
    that fact now lives on the card, and going back collapses it into a path.
    """
    Flashcard = apps.get_model('flashcards', 'Flashcard')
    for pointer, field in (('front_media', 'front_image'), ('back_media', 'back_image')):
        rows = Flashcard.objects.exclude(**{f'{pointer}__isnull': True}).select_related(pointer)
        for card in rows:
            media = getattr(card, pointer)
            if media and media.image:
                Flashcard.objects.filter(pk=card.pk).update(**{field: media.image})


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0010_sitesettings'),
    ]

    operations = [
        # 1. New pointers alongside the old columns.
        migrations.AddField(
            model_name='flashcard',
            name='front_media',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+', to='flashcards.cardimage',
                help_text='The media shown on the front of this card version.',
            ),
        ),
        migrations.AddField(
            model_name='flashcard',
            name='back_media',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+', to='flashcards.cardimage',
                help_text='The media shown on the back of this card version.',
            ),
        ),

        # 2. Move the data across while both shapes exist.
        migrations.RunPython(forwards, backwards),

        # 3. Drop the old path columns and take their names.
        migrations.RemoveField(model_name='flashcard', name='front_image'),
        migrations.RemoveField(model_name='flashcard', name='back_image'),
        migrations.RenameField(
            model_name='flashcard', old_name='front_media', new_name='front_image',
        ),
        migrations.RenameField(
            model_name='flashcard', old_name='back_media', new_name='back_image',
        ),

        # 4. Acceptance is the pointer now, so the flag and its audit fields go.
        #    The index comes off first: it covers is_accepted.
        migrations.RemoveIndex(
            model_name='cardimage',
            name='flashcards__version_aa3b7f_idx',
        ),
        migrations.RemoveField(model_name='cardimage', name='is_accepted'),
        migrations.RemoveField(model_name='cardimage', name='accepted_at'),
        migrations.RemoveField(model_name='cardimage', name='accepted_by'),

        # 5. Uploads have no prompt and no model, and are a status of their own.
        migrations.AlterField(
            model_name='cardimage',
            name='prompt',
            field=models.TextField(
                blank=True,
                help_text='The full prompt sent to the model, look and feel included. Blank for uploads.',
            ),
        ),
        migrations.AlterField(
            model_name='cardimage',
            name='model',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='cardimage',
            name='status',
            field=models.CharField(
                choices=[
                    ('queued', 'Queued'), ('generating', 'Generating'),
                    ('succeeded', 'Succeeded'), ('failed', 'Failed'),
                    ('uploaded', 'Uploaded'),
                ],
                db_index=True, default='queued', max_length=12,
            ),
        ),
    ]
