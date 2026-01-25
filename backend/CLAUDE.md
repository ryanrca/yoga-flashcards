# Claude Code Instructions - Backend (Django)

## Quick Reference

```
Framework:  Django 4.2.7 + DRF 3.14.0
Database:   MySQL 8.0
Port:       8000
Run tests:  python -m pytest
```

## Project Structure

```
backend/
├── yoga_flashcards/           # Django project
│   ├── settings.py           # Configuration
│   ├── urls.py               # Root URL routing
│   └── wsgi.py
├── flashcards/                # Flashcard app
│   ├── models.py             # Flashcard, Tag, DailyCard, CardUsageLog
│   ├── views.py              # FlashcardViewSet, TagViewSet
│   ├── serializers.py        # DRF serializers
│   ├── services.py           # DailyCardService
│   ├── permissions.py        # IsCuratorOrAdmin, IsAdminOnly
│   ├── pagination.py         # CardPagination (20 per page)
│   └── management/commands/  # seed_initial_data, import_cards
├── users/                     # User app
│   ├── models.py             # User, UserProfile
│   ├── views.py              # Auth endpoints
│   ├── serializers.py        # User serializers
│   └── services.py           # Email verification
├── core/                      # Core utilities
│   ├── views.py              # health_check, daily_card
│   └── urls.py
├── requirements.txt
├── Dockerfile
└── start.sh                   # Container startup
```

## Architecture Principles

1. **Thin views, fat models** - Business logic in `services.py`
2. **DRF ModelViewSets** for REST endpoints
3. **Serializers** for all validation (never raw request.data)
4. **Apps by domain**: flashcards, users, core
5. **Session-based auth** (not JWT)

---

## Data Models

### User (users/models.py)

```python
class User(AbstractUser):
    ROLE_CHOICES = [('user', 'User'), ('curator', 'Curator'), ('admin', 'Admin')]

    role = CharField(max_length=20, default='user')
    daily_email_enabled = BooleanField(default=False)
    email_verified = BooleanField(default=False)
    email_verification_token = CharField(max_length=100, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def is_admin(self): return self.role == 'admin' or self.is_superuser
    def is_curator(self): return self.role in ('curator', 'admin') or self.is_superuser
    def can_edit_cards(self): return self.is_curator()
    def can_edit_users(self): return self.is_admin()
```

### UserProfile (users/models.py)

```python
class UserProfile(Model):
    user = OneToOneField(User, on_delete=CASCADE, related_name='profile')
    bio = TextField(blank=True)
    avatar = ImageField(upload_to='avatars/', blank=True, null=True)
    favorite_cards = ManyToManyField('flashcards.Flashcard', blank=True)
```

### Flashcard (flashcards/models.py)

```python
class Flashcard(Model):
    # Content
    title = CharField(max_length=200)
    phrase = CharField(max_length=500)  # Sanskrit
    definition = TextField()
    short_answer = TextField(blank=True)
    front_image = ImageField(upload_to='flashcard_images/', blank=True, null=True)
    back_image = ImageField(upload_to='flashcard_images/', blank=True, null=True)
    tags = ManyToManyField('Tag', blank=True)

    # Versioning
    version_group = UUIDField(default=uuid.uuid4)
    version_number = PositiveIntegerField(default=1)
    is_live = BooleanField(default=True)
    is_active = BooleanField(default=True)  # Soft delete

    # Audit
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def get_version_history(self):
        return Flashcard.objects.filter(
            version_group=self.version_group
        ).order_by('-version_number')

    def create_new_version(self, **kwargs):
        # Sets old is_live=False, creates new with version_number+1
        ...

    def revert_to_this_version(self, reverted_by):
        # Creates NEW version copying this version's content
        ...
```

### Tag (flashcards/models.py)

```python
class Tag(Model):
    name = CharField(max_length=50, unique=True)
    description = TextField(blank=True)

    class Meta:
        ordering = ['name']
```

### DailyCard (flashcards/models.py)

```python
class DailyCard(Model):
    card = ForeignKey(Flashcard, on_delete=CASCADE)
    date = DateField(unique=True)  # One card per day
```

### CardUsageLog (flashcards/models.py)

```python
class CardUsageLog(Model):
    card = ForeignKey(Flashcard, on_delete=CASCADE)
    used_date = DateField()
    cycle_number = PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['card', 'used_date', 'cycle_number']
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | /api/users/register/ | AllowAny | Create account |
| POST | /api/users/login/ | AllowAny | Login (email + password) |
| POST | /api/users/logout/ | IsAuthenticated | Logout |
| GET | /api/users/auth-status/ | AllowAny | Check auth status |
| GET/PUT | /api/users/profile/ | IsAuthenticated | User profile |

### Flashcards

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | /api/cards/ | IsAuthenticated | List cards (?search=&tags=&page=) |
| POST | /api/cards/ | IsCuratorOrAdmin | Create card |
| GET | /api/cards/{id}/ | IsAuthenticated | Card detail |
| PUT | /api/cards/{id}/ | IsCuratorOrAdmin | Update (new version) |
| DELETE | /api/cards/{id}/ | IsCuratorOrAdmin | Soft delete |
| GET | /api/cards/{id}/versions/ | IsCuratorOrAdmin | Version history |
| POST | /api/cards/{id}/revert_version/ | IsCuratorOrAdmin | Revert to version |

### Tags

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | /api/tags/ | AllowAny | List tags |
| POST | /api/tags/ | IsCuratorOrAdmin | Create tag |
| PUT | /api/tags/{id}/ | IsCuratorOrAdmin | Update tag |
| DELETE | /api/tags/{id}/ | IsCuratorOrAdmin | Delete tag |

### Utility

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | /api/dailycard/ | AllowAny | Today's daily card |
| GET | /api/health/ | AllowAny | Health check |

### Admin (User Management)

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | /api/users/manage/ | IsAdminOnly | List users |
| POST | /api/users/manage/ | IsAdminOnly | Create user |
| PATCH | /api/users/manage/{id}/ | IsAdminOnly | Update user |
| DELETE | /api/users/manage/{id}/ | IsAdminOnly | Delete user |
| POST | /api/users/manage/{id}/toggle_active/ | IsAdminOnly | Toggle active |
| GET | /api/users/manage/stats/ | IsAdminOnly | User stats |

---

## Versioning Logic

### Creating a Card

```python
# In FlashcardSerializer.create()
flashcard = Flashcard.objects.create(
    **validated_data,
    version_group=uuid.uuid4(),
    version_number=1,
    is_live=True,
    created_by=self.context['request'].user
)
```

### Updating a Card (New Version)

```python
# In FlashcardSerializer.update()
def update(self, instance, validated_data):
    # Don't update in place - create new version
    new_version = instance.create_new_version(
        **validated_data,
        created_by=self.context['request'].user
    )
    return new_version
```

### Reverting to Previous Version

```python
# In FlashcardViewSet.revert_version()
@action(detail=True, methods=['post'])
def revert_version(self, request, pk=None):
    card = self.get_object()
    version_id = request.data.get('version_id')
    target_version = Flashcard.objects.get(
        id=version_id,
        version_group=card.version_group
    )
    new_version = target_version.revert_to_this_version(request.user)
    return Response(FlashcardSerializer(new_version).data)
```

---

## Daily Card Service

```python
# flashcards/services.py
class DailyCardService:
    @staticmethod
    def get_daily_card():
        today = timezone.now().date()

        # Check if already selected today
        daily_card = DailyCard.objects.filter(date=today).first()
        if daily_card:
            return daily_card.card

        # Select new card
        card = DailyCardService._select_next_card()
        DailyCard.objects.create(card=card, date=today)

        # Log usage
        current_cycle = CardUsageLog.objects.aggregate(
            max_cycle=Max('cycle_number')
        )['max_cycle'] or 1
        CardUsageLog.objects.create(
            card=card,
            used_date=today,
            cycle_number=current_cycle
        )

        return card

    @staticmethod
    def _select_next_card():
        current_cycle = CardUsageLog.objects.aggregate(
            max_cycle=Max('cycle_number')
        )['max_cycle'] or 1

        used_card_ids = CardUsageLog.objects.filter(
            cycle_number=current_cycle
        ).values_list('card_id', flat=True)

        available_cards = Flashcard.objects.filter(
            is_active=True,
            is_live=True
        ).exclude(id__in=used_card_ids)

        if not available_cards.exists():
            # Start new cycle
            current_cycle += 1
            available_cards = Flashcard.objects.filter(
                is_active=True,
                is_live=True
            )

        return random.choice(list(available_cards))
```

---

## Permission Classes

```python
# flashcards/permissions.py
from rest_framework.permissions import BasePermission

class IsCuratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (request.user.is_curator() or request.user.is_admin())
        )

class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_admin()
        )
```

---

## Settings Configuration

Key settings in `yoga_flashcards/settings.py`:

```python
# Custom user model
AUTH_USER_MODEL = 'users.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'flashcards.pagination.CardPagination',
    'PAGE_SIZE': 20,
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:9000",
    "http://127.0.0.1:9000",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF (disabled for API in dev)
MIDDLEWARE = [
    ...
    'yoga_flashcards.middleware.DisableCSRFMiddleware',
    ...
]
```

---

## Testing

### Run Tests

```bash
# All tests
python -m pytest

# Specific app
python -m pytest flashcards/

# With coverage
python -m pytest --cov=flashcards --cov=users

# Verbose
python -m pytest -v
```

### Test Structure

```
flashcards/tests/
├── test_models.py       # Model tests
├── test_views.py        # API tests
├── test_serializers.py  # Serializer tests
├── test_services.py     # Service tests
└── factories.py         # Factory Boy factories

users/tests/
├── test_models.py
├── test_views.py
└── factories.py
```

### Example Test

```python
# flashcards/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from .factories import FlashcardFactory, UserFactory

@pytest.mark.django_db
class TestFlashcardViewSet:
    def test_list_requires_auth(self):
        client = APIClient()
        response = client.get('/api/cards/')
        assert response.status_code == 403

    def test_curator_can_create(self):
        curator = UserFactory(role='curator')
        client = APIClient()
        client.force_authenticate(curator)

        response = client.post('/api/cards/', {
            'title': 'Test',
            'phrase': 'Test phrase',
            'definition': 'Test definition'
        })
        assert response.status_code == 201
```

---

## Management Commands

### seed_initial_data

```bash
# Import flashcards from JSON
python manage.py seed_initial_data

# Export flashcards to JSON
python manage.py seed_initial_data --pull

# Use custom file
python manage.py seed_initial_data -f /path/to/data.json
```

### import_cards

```bash
# Import from CSV
python manage.py import_cards /path/to/cards.csv

# Dry run
python manage.py import_cards /path/to/cards.csv --dry-run

# Specify user
python manage.py import_cards /path/to/cards.csv --user admin
```

CSV format:
```csv
title,phrase,definition,short_answer,tags
"Ahimsa","Non-violence","Full definition...","Non-violence","Yamas,Sanskrit"
```

---

## Style Guide

- 4 spaces indentation
- `snake_case` for variables, functions, files
- `CamelCase` for classes
- `UPPER_CASE` for constants
- No emojis in code or comments
- Docstrings for public methods
- Type hints encouraged
