"""
Factory Boy factories for the flashcards app.
"""
import uuid
import factory
from factory.django import DjangoModelFactory
from flashcards.models import Flashcard, Tag, DailyCard, CardUsageLog, CardImage
from users.tests.factories import UserFactory


class TagFactory(DjangoModelFactory):
    """Factory for creating Tag instances."""

    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f'Tag {n}')
    description = factory.Faker('sentence')


class FlashcardFactory(DjangoModelFactory):
    """Factory for creating Flashcard instances."""

    class Meta:
        model = Flashcard

    title = factory.Faker('sentence', nb_words=3)
    phrase = factory.Faker('word')
    definition = factory.Faker('paragraph')
    short_answer = factory.Faker('sentence')
    created_by = factory.SubFactory(UserFactory)
    version_group = factory.LazyFunction(uuid.uuid4)
    version_number = 1
    is_live = True
    is_active = True

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class DailyCardFactory(DjangoModelFactory):
    """Factory for creating DailyCard instances."""

    class Meta:
        model = DailyCard

    card = factory.SubFactory(FlashcardFactory)
    date = factory.Faker('date_object')


class CardUsageLogFactory(DjangoModelFactory):
    """Factory for creating CardUsageLog instances."""

    class Meta:
        model = CardUsageLog

    card = factory.SubFactory(FlashcardFactory)
    used_date = factory.Faker('date_object')
    cycle_number = 1


class CardImageFactory(DjangoModelFactory):
    """Factory for creating CardImage instances."""

    class Meta:
        model = CardImage

    card = factory.SubFactory(FlashcardFactory)
    version_group = factory.LazyAttribute(lambda o: o.card.version_group)
    status = CardImage.QUEUED
    prompt = factory.Faker('sentence')
    prompt_seed = factory.Faker('sentence')
    look_and_feel = 'Soft watercolour, warm earth tones.'
    look_and_feel_override = ''
    model = 'black-forest-labs/flux.2-pro'
