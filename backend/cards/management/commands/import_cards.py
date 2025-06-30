import csv
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from cards.models import Card, Tag, CardVersion


class Command(BaseCommand):
    help = 'Import cards from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual changes)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username to assign as creator (default: admin)',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        username = options['user']
        
        # Get the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY-RUN mode - no changes will be made')
            )
        
        created_count = 0
        updated_count = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate required columns
                required_columns = ['title', 'phrase', 'definition']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = [col for col in required_columns if col not in reader.fieldnames]
                    raise CommandError(f'Missing required columns: {missing}')
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        title = row['title'].strip()
                        phrase = row['phrase'].strip()
                        definition = row['definition'].strip()
                        tags_str = row.get('tags', '').strip()
                        
                        if not title or not phrase or not definition:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Row {row_num}: Skipping - missing required fields'
                                )
                            )
                            continue
                        
                        # Check if card already exists (by title and phrase)
                        existing_card = Card.objects.filter(
                            title=title, 
                            phrase=phrase,
                            deleted_at__isnull=True
                        ).first()
                        
                        if existing_card:
                            # Update existing card
                            if not dry_run:
                                existing_card.definition = definition
                                existing_card.save()
                                
                                # Create new version if text changed
                                last_version = existing_card.versions.first()
                                version_number = last_version.version_number + 1 if last_version else 1
                                
                                CardVersion.objects.create(
                                    card=existing_card,
                                    title=title,
                                    phrase=phrase,
                                    definition=definition,
                                    created_by=user,
                                    version_number=version_number
                                )
                            
                            updated_count += 1
                            self.stdout.write(f'Row {row_num}: Updated card "{title}"')
                        else:
                            # Create new card
                            if not dry_run:
                                card = Card.objects.create(
                                    title=title,
                                    phrase=phrase,
                                    definition=definition,
                                    created_by=user
                                )
                                
                                # Create initial version
                                CardVersion.objects.create(
                                    card=card,
                                    title=title,
                                    phrase=phrase,
                                    definition=definition,
                                    created_by=user,
                                    version_number=1
                                )
                            else:
                                card = None
                            
                            created_count += 1
                            self.stdout.write(f'Row {row_num}: Created card "{title}"')
                        
                        # Handle tags
                        if tags_str and not dry_run:
                            tag_names = [name.strip() for name in tags_str.split(',') if name.strip()]
                            tags = []
                            for tag_name in tag_names:
                                tag, created = Tag.objects.get_or_create(name=tag_name)
                                tags.append(tag)
                            
                            target_card = existing_card if existing_card else card
                            if target_card:
                                target_card.tags.set(tags)
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Row {row_num}: Error processing row - {str(e)}'
                            )
                        )
                        continue
        
        except FileNotFoundError:
            raise CommandError(f'File "{csv_file}" not found')
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN COMPLETE: Would create {created_count} cards, '
                    f'update {updated_count} cards'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import complete: Created {created_count} cards, '
                    f'updated {updated_count} cards'
                )
            )
