"""
Factory Boy factories for the users app.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = 'user'
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def save_instance(obj, create, extracted, **kwargs):
        if create:
            obj.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""

    role = 'admin'
    is_staff = True
    is_superuser = True


class CuratorUserFactory(UserFactory):
    """Factory for creating curator users."""

    role = 'curator'
