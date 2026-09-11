# Yoga Flashcards - Database Schema

This document provides the complete database schema specification for regenerating the Django models.

---

## Entity Relationship Diagram

```
┌─────────────────────┐
│       User          │
├─────────────────────┤
│ id (PK)             │
│ email (unique)      │
│ username (unique)   │
│ password            │
│ first_name          │
│ last_name           │
│ role                │──────────────────────────────────────┐
│ is_active           │                                      │
│ is_staff            │     ┌─────────────────────┐          │
│ is_superuser        │     │    UserProfile      │          │
│ daily_email_enabled │     ├─────────────────────┤          │
│ email_verified      │     │ id (PK)             │          │
│ email_verif_token   │──1:1│ user_id (FK,unique) │          │
│ date_joined         │     │ bio                 │          │
│ last_login          │     │ avatar              │          │
│ created_at          │     │ favorite_cards (M2M)│──────────┼──┐
│ updated_at          │     └─────────────────────┘          │  │
└─────────────────────┘                                      │  │
          │                                                  │  │
          │ 1:M (created_by)                                 │  │
          ▼                                                  │  │
┌─────────────────────┐     ┌─────────────────────┐          │  │
│     Flashcard       │     │        Tag          │          │  │
├─────────────────────┤     ├─────────────────────┤          │  │
│ id (PK)             │◄────│ id (PK)             │          │  │
│ title               │ M:M │ name (unique)       │          │  │
│ phrase              │     │ description         │          │  │
│ definition          │     └─────────────────────┘          │  │
│ short_answer        │                                      │  │
│ front_image         │◄─────────────────────────────────────┘  │
│ back_image          │◄────────────────────────────────────────┘
│ tags (M2M)          │
│ version_group (UUID)│
│ version_number      │
│ is_live             │
│ is_active           │
│ created_by (FK)     │
│ created_at          │
│ updated_at          │
└─────────────────────┘
          │
          │ 1:M
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│     DailyCard       │     │   CardUsageLog      │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │     │ id (PK)             │
│ card_id (FK)        │     │ card_id (FK)        │
│ date (unique)       │     │ used_date           │
└─────────────────────┘     │ cycle_number        │
                            └─────────────────────┘
```

---

## Model Specifications

### User Model

**Table:** `users_user`

**Extends:** `django.contrib.auth.models.AbstractUser`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| email | EmailField | unique | required | Login identifier |
| username | CharField(150) | unique | auto-gen | Auto-generated from email |
| password | CharField(128) | | required | Hashed password |
| first_name | CharField(150) | | '' | First name |
| last_name | CharField(150) | | '' | Last name |
| role | CharField(20) | choices | 'user' | user/curator/admin |
| is_active | BooleanField | | True | Account active status |
| is_staff | BooleanField | | False | Django admin access |
| is_superuser | BooleanField | | False | Superuser status |
| daily_email_enabled | BooleanField | | False | Daily email preference |
| email_verified | BooleanField | | False | Email verification status |
| email_verification_token | CharField(100) | null, blank | None | Verification token |
| date_joined | DateTimeField | | auto | Account creation time |
| last_login | DateTimeField | null | None | Last login time |
| created_at | DateTimeField | auto_now_add | auto | Record creation time |
| updated_at | DateTimeField | auto_now | auto | Record update time |

**Role Choices:**
```python
ROLE_CHOICES = [
    ('user', 'User'),
    ('curator', 'Curator'),
    ('admin', 'Admin'),
]
```

**Methods:**
```python
def is_admin(self) -> bool:
    return self.role == 'admin' or self.is_superuser

def is_curator(self) -> bool:
    return self.role in ('curator', 'admin') or self.is_superuser

def can_edit_cards(self) -> bool:
    return self.is_curator()

def can_edit_users(self) -> bool:
    return self.is_admin()
```

---

### UserProfile Model

**Table:** `users_userprofile`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| user_id | OneToOneField | FK(User), unique | required | Reference to User |
| bio | TextField | blank | '' | User biography |
| avatar | ImageField | blank, null | None | Profile picture |
| favorite_cards | ManyToManyField | blank | [] | Favorited flashcards |

**Relationships:**
- `user`: OneToOne to User (CASCADE on delete)
- `favorite_cards`: ManyToMany to Flashcard

**Signal:** Create UserProfile automatically when User is created:
```python
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
```

---

### Flashcard Model

**Table:** `flashcards_flashcard`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| title | CharField(200) | | required | Card title |
| phrase | CharField(500) | | required | Sanskrit phrase |
| definition | TextField | | required | Full definition |
| short_answer | TextField | blank | '' | Brief summary |
| front_image | ImageField | blank, null | None | Front image |
| back_image | ImageField | blank, null | None | Back image |
| tags | ManyToManyField | blank | [] | Associated tags |
| version_group | UUIDField | | uuid4() | Groups all versions |
| version_number | PositiveIntegerField | | 1 | Version sequence |
| is_live | BooleanField | | True | Current active version |
| is_active | BooleanField | | True | Intended as a soft delete flag, but `DELETE /api/cards/{id}/` currently hard-deletes the row. Only the seeder and queries read it. |
| created_by | ForeignKey | null, SET_NULL | None | Creating user |
| created_at | DateTimeField | auto_now_add | auto | Creation time |
| updated_at | DateTimeField | auto_now | auto | Update time |

**Image Upload Path:** `flashcard_images/`

**Indexes:**
```python
class Meta:
    indexes = [
        models.Index(fields=['title']),
        models.Index(fields=['is_active']),
        models.Index(fields=['created_at']),
        models.Index(fields=['version_group', 'is_live']),
        models.Index(fields=['version_group', '-version_number']),
    ]
    ordering = ['-created_at']
```

**Methods:**
```python
def get_version_history(self) -> QuerySet:
    """Get all versions of this card ordered by version_number desc."""
    return Flashcard.objects.filter(
        version_group=self.version_group
    ).order_by('-version_number')

def create_new_version(self, **kwargs) -> 'Flashcard':
    """Create a new version of this card."""
    # 1. Set current live version to not live
    Flashcard.objects.filter(
        version_group=self.version_group,
        is_live=True
    ).update(is_live=False)

    # 2. Get next version number
    max_version = Flashcard.objects.filter(
        version_group=self.version_group
    ).aggregate(Max('version_number'))['version_number__max'] or 0

    # 3. Create new version
    new_card = Flashcard.objects.create(
        title=kwargs.get('title', self.title),
        phrase=kwargs.get('phrase', self.phrase),
        definition=kwargs.get('definition', self.definition),
        short_answer=kwargs.get('short_answer', self.short_answer),
        front_image=kwargs.get('front_image', self.front_image),
        back_image=kwargs.get('back_image', self.back_image),
        version_group=self.version_group,
        version_number=max_version + 1,
        is_live=True,
        is_active=True,
        created_by=kwargs.get('created_by', self.created_by),
    )

    # 4. Copy tags
    tags = kwargs.get('tags', self.tags.all())
    new_card.tags.set(tags)

    return new_card

def revert_to_this_version(self, reverted_by: User) -> 'Flashcard':
    """Create a new version copying this version's content."""
    return self.create_new_version(
        title=self.title,
        phrase=self.phrase,
        definition=self.definition,
        short_answer=self.short_answer,
        front_image=self.front_image,
        back_image=self.back_image,
        tags=self.tags.all(),
        created_by=reverted_by,
    )
```

---

### Tag Model

**Table:** `flashcards_tag`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| name | CharField(50) | unique | required | Tag name |
| description | TextField | blank | '' | Tag description |

**Meta:**
```python
class Meta:
    ordering = ['name']
```

---

### DailyCard Model

**Table:** `flashcards_dailycard`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| card_id | ForeignKey | FK(Flashcard) | required | Selected card |
| date | DateField | unique | required | Selection date |

**Purpose:** Tracks which card was selected for each day.

---

### CardUsageLog Model

**Table:** `flashcards_cardusagelog`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | AutoField | PK | auto | Primary key |
| card_id | ForeignKey | FK(Flashcard) | required | Used card |
| used_date | DateField | | required | Date used |
| cycle_number | PositiveIntegerField | | 1 | Cycle iteration |

**Constraints:**
```python
class Meta:
    unique_together = ['card', 'used_date', 'cycle_number']
```

**Purpose:** Tracks card usage for daily card rotation. When all cards have been used in a cycle, the cycle_number increments.

---

## Junction Tables (Auto-generated)

### flashcards_flashcard_tags

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| flashcard_id | ForeignKey | Reference to Flashcard |
| tag_id | ForeignKey | Reference to Tag |

### users_userprofile_favorite_cards

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| userprofile_id | ForeignKey | Reference to UserProfile |
| flashcard_id | ForeignKey | Reference to Flashcard |

---

## Database Configuration

**Engine:** MySQL 8.0

**Character Set:** UTF8MB4 (for Sanskrit character support)

**Connection String:**
```
mysql://django_user:django_password@db:3306/yoga_flashcards
```

**Django Settings:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yoga_flashcards',
        'USER': 'django_user',
        'PASSWORD': 'django_password',
        'HOST': 'db',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

---

## Migration Notes

### Initial Migration Order

1. `users` app first (custom User model)
2. `flashcards` app second (depends on User)
3. `core` app (if any models)

### Key Migrations

1. `users/0001_initial.py` - User and UserProfile models
2. `flashcards/0001_initial.py` - Flashcard, Tag models
3. `flashcards/0002_*` - DailyCard, CardUsageLog models
4. `flashcards/0003_*` - Version fields (version_group, version_number, is_live)
5. `flashcards/0004_*` - Populate version_group UUIDs for existing cards
6. `flashcards/0005_*` - short_answer field

### Custom User Model Setting

```python
# settings.py
AUTH_USER_MODEL = 'users.User'
```

This MUST be set before running any migrations.

---

## Seed Data

### Initial Tags

| Name | Description |
|------|-------------|
| 8 Limbs | The eight limbs of yoga according to Patanjali |
| Yamas | Ethical restraints - how we relate to others |
| Niyamas | Personal observances - how we relate to ourselves |

### Initial Users

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | admin (superuser) |
| admin1@example.com | admin1 | admin |
| curator1@example.com | curator1 | curator |
| user1@example.com | user1 | user |

### Initial Flashcards

See `backend/flashcards/management/commands/data/flashcards.json` for the complete seed data.
19 cards in total:
- 8 Limbs of Yoga
- 5 Yamas
- 5 Niyamas
- 1 "Yoga" overview card

---

## Querying Patterns

### Get Live Cards Only

```python
Flashcard.objects.filter(is_active=True, is_live=True)
```

### Get All Versions of a Card

```python
Flashcard.objects.filter(
    version_group=card.version_group
).order_by('-version_number')
```

### Get Current Live Version

```python
Flashcard.objects.get(
    version_group=version_group_uuid,
    is_live=True
)
```

### Search Cards

```python
from django.db.models import Q

Flashcard.objects.filter(
    Q(title__icontains=search) |
    Q(phrase__icontains=search) |
    Q(definition__icontains=search) |
    Q(tags__name__icontains=search),
    is_active=True,
    is_live=True
).distinct()
```

### Filter by Tags

```python
# By tag IDs
Flashcard.objects.filter(
    tags__id__in=[1, 2, 3],
    is_active=True,
    is_live=True
).distinct()

# By tag names
Flashcard.objects.filter(
    tags__name__in=['Yamas', 'Sanskrit'],
    is_active=True,
    is_live=True
).distinct()
```
