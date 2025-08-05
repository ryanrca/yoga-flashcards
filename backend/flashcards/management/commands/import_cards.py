import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from flashcards.models import Flashcard, Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Import flashcards from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without making changes',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username of the creating user (default: admin)',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        username = options['user']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = ['title', 'definition']
                if not all(col in reader.fieldnames for col in required_columns):
                    raise CommandError(f'CSV must contain columns: {", ".join(required_columns)}')

                imported_count = 0
                updated_count = 0

                for row_num, row in enumerate(reader, start=2):
                    try:
                        title = row['title'].strip()
                        phrase = row.get('phrase', '').strip()
                        definition = row['definition'].strip()
                        tag_names = row.get('tags', '').strip()

                        if not title or not definition:
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: Skipping - missing title or definition')
                            )
                            continue

                        if dry_run:
                            self.stdout.write(f'Would import: {title}')
                            if tag_names:
                                self.stdout.write(f'  Tags: {tag_names}')
                            continue

                        # Check if card already exists
                        existing_card = Flashcard.objects.filter(
                            title=title, 
                            is_active=True
                        ).first()

                        if existing_card:
                            # Update existing card (create new version)
                            new_version = existing_card.create_new_version(
                                title=title,
                                phrase=phrase,
                                definition=definition,
                                created_by=user
                            )
                            updated_count += 1
                            self.stdout.write(f'Updated: {title} (new version {new_version.version})')
                        else:
                            # Create new card
                            flashcard = Flashcard.objects.create(
                                title=title,
                                phrase=phrase,
                                definition=definition,
                                created_by=user
                            )
                            imported_count += 1
                            self.stdout.write(f'Created: {title}')

                        # Handle tags
                        if tag_names:
                            tag_list = [name.strip() for name in tag_names.split(',')]
                            for tag_name in tag_list:
                                if tag_name:
                                    tag, created = Tag.objects.get_or_create(name=tag_name)
                                    if existing_card:
                                        new_version.tags.add(tag)
                                    else:
                                        flashcard.tags.add(tag)
                                    
                                    if created:
                                        self.stdout.write(f'  Created tag: {tag_name}')

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error processing - {str(e)}')
                        )

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'Dry run completed. Found {imported_count} new cards to import.')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Import completed. Created {imported_count} new cards, updated {updated_count} existing cards.'
                        )
                    )

        except FileNotFoundError:
            raise CommandError(f'File "{csv_file}" not found')
        except Exception as e:
            raise CommandError(f'Error processing CSV: {str(e)}')
