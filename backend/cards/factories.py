import pytest
from django.contrib.auth.models import User
from cards.models import Card, Tag, CardVersion
import factory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
    
    name = factory.Faker('word')


class CardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Card
    
    title = factory.Faker('sentence', nb_words=3)
    phrase = factory.Faker('sentence', nb_words=2)
    definition = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)
    enabled = True


class CardVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CardVersion
    
    card = factory.SubFactory(CardFactory)
    title = factory.Faker('sentence', nb_words=3)
    phrase = factory.Faker('sentence', nb_words=2)
    definition = factory.Faker('text')
    created_by = factory.SubFactory(UserFactory)
    version_number = 1
