"""
The image bot.

Run it on a schedule (a Kubernetes CronJob, or cron calling `manage.py`). Two
jobs per run:

1. Queue a first image for any card family that has never had one.
2. Process queued rows, one OpenRouter call each.

Every run is bounded by --limit, every row is bounded by max_attempts, and rows
are claimed with SELECT ... FOR UPDATE SKIP LOCKED, so overlapping runs cannot
double-generate and a failing card cannot loop forever.
"""
from django.core.management.base import BaseCommand, CommandError

from flashcards.models import CardImage, Flashcard, ImageGenerationSettings
from flashcards.openrouter import OpenRouterClient
from flashcards.services import CardImageService


class Command(BaseCommand):
    help = 'Generate AI images for cards that do not have one, and drain the generation queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=5,
            help='Maximum generations to run in this pass (default: 5)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be queued, with prompts. Changes nothing and calls nothing.',
        )
        parser.add_argument(
            '--card-id', type=int,
            help='Queue and generate for one specific card, even if it already has images',
        )
        parser.add_argument(
            '--no-auto-queue', action='store_true',
            help='Only drain rows already queued; do not look for cards missing an image',
        )
        parser.add_argument(
            '--stale-minutes', type=int, default=30,
            help='Return rows stuck in "generating" for this long to the queue (default: 30)',
        )

    def handle(self, *args, **options):
        limit = max(0, options['limit'])
        config = ImageGenerationSettings.load()

        if not config.enabled:
            self.stdout.write(self.style.WARNING(
                'Image generation is disabled in the global settings. Nothing to do.'
            ))
            return

        if options['dry_run']:
            return self._dry_run(options, limit)

        client = OpenRouterClient()
        if not client.is_configured:
            raise CommandError(
                'OPENROUTER_API_KEY is not set. Set it in the environment before running the bot.'
            )

        requeued = CardImageService.reset_stale(options['stale_minutes'])
        if requeued:
            self.stdout.write(f'Returned {requeued} stalled generation(s) to the queue.')

        if options['card_id']:
            card = self._get_card(options['card_id'])
            CardImageService.queue(card)
            self.stdout.write(f'Queued a generation for "{card.title}".')
        elif not options['no_auto_queue']:
            queued = CardImageService.queue_missing(limit=limit)
            self.stdout.write(f'Queued {len(queued)} card(s) that had no image yet.')

        succeeded = failed = 0
        for _ in range(limit):
            image = CardImageService.claim_next()
            if image is None:
                break
            label = image.card.title if image.card else str(image.version_group)
            self.stdout.write(f'Generating for "{label}" using {image.model} ...')
            image = CardImageService.run(image, client=client)
            if image.status == CardImage.SUCCEEDED:
                succeeded += 1
                self.stdout.write(self.style.SUCCESS(f'  ok: {image.image.name}'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(
                    f'  {image.status} after attempt {image.attempts}: {image.error[:160]}'
                ))

        remaining = CardImage.objects.filter(status=CardImage.QUEUED).count()
        self.stdout.write(self.style.SUCCESS(
            f'Done. {succeeded} generated, {failed} failed, {remaining} still queued.'
        ))

    def _dry_run(self, options, limit):
        if options['card_id']:
            cards = [self._get_card(options['card_id'])]
        else:
            cards = list(
                Flashcard.objects.filter(is_active=True, is_live=True)
                .exclude(version_group__in=CardImage.objects.values('version_group'))
                .prefetch_related('tags')
                .order_by('created_at')[:limit]
            )

        if not cards:
            self.stdout.write('Nothing to queue: every card already has at least one image.')
            return

        for card in cards:
            preview = CardImageService.preview_prompt(card)
            self.stdout.write(self.style.SUCCESS(f'\n{card.title}  [{preview["model"]}]'))
            self.stdout.write(preview['prompt'])
        self.stdout.write(self.style.WARNING(
            f'\nDry run: {len(cards)} card(s) would be queued. Nothing was changed.'
        ))

    @staticmethod
    def _get_card(card_id):
        try:
            return Flashcard.objects.prefetch_related('tags').get(pk=card_id)
        except Flashcard.DoesNotExist:
            raise CommandError(f'No card with id {card_id}.')
