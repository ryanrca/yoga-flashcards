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
│ role                │
│ is_active           │     ┌─────────────────────┐
│ is_staff            │     │    UserProfile      │
│ is_superuser        │     ├─────────────────────┤
│ daily_email_enabled │     │ id (PK)             │
│ email_verified      │──1:1│ user_id (FK,unique) │
│ email_verif_token   │     │ bio                 │
│ date_joined         │     │ avatar              │
│ last_login          │     └─────────────────────┘
│ created_at          │
│ updated_at          │     ┌─────────────────────┐
└─────────────────────┘     │      Favorite       │
          │           ──1:M─├─────────────────────┤
          │                 │ id (PK)             │
          │                 │ user_id (FK)        │
          │                 │ version_group (UUID)│
          │ 1:M             │ created_at          │
          │ (created_by)    └─────────────────────┘
          ▼
┌─────────────────────┐     ┌─────────────────────┐
│     Flashcard       │     │        Tag          │
├─────────────────────┤     ├─────────────────────┤
│ id (PK)             │◄────│ id (PK)             │
│ title               │ M:M │ name (unique)       │
│ phrase              │     │ description         │
│ definition          │     └─────────────────────┘
│ short_answer        │
│ favorite_count      │
│ front_image (FK)    │──┐
│ back_image (FK)     │──┤
│ tags (M2M)          │  │
│ version_group (UUID)│  │
│ version_number      │  │   ┌─────────────────────┐
│ is_live             │  │   │      CardImage      │
│ is_active           │  └──►├─────────────────────┤
│ created_by (FK)     │◄─────│ id (PK)             │
│ created_at          │ 1:M  │ version_group (UUID)│
│ updated_at          │ card │ card_id (FK, prov.) │
└─────────────────────┘      │ status              │
          │                  │ image               │
          │                  │ prompt / model      │
          │                  └─────────────────────┘
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
| is_active | BooleanField | | True | Account active status. Cleared by a soft delete; also toggled independently by admins. |
| is_deleted | BooleanField | index | False | Soft delete flag. The row is always kept. |
| deleted_at | DateTimeField | | NULL | When the account was soft deleted. |
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

**Relationships:**
- `user`: OneToOne to User (CASCADE on delete)

Favourites are **not** stored here. They live in `flashcards_favorite`, keyed on a
card's `version_group` rather than a row id, so that editing a card cannot orphan
them. See the Favorite table below.

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
| front_image | ForeignKey(CardImage) | SET_NULL, null | NULL | The media shown on this version's front. A pointer, not a file. SET_NULL so removing an image never removes the card. |
| back_image | ForeignKey(CardImage) | SET_NULL, null | NULL | The media shown on this version's back |
| tags | ManyToManyField | blank | [] | Associated tags |
| version_group | UUIDField | | uuid4() | Groups all versions |
| version_number | PositiveIntegerField | | 1 | Version sequence |
| is_live | BooleanField | | True | Current active version |
| is_active | BooleanField | | True | Intended as a soft delete flag, but `DELETE /api/cards/{id}/` currently hard-deletes the row. Only the seeder and queries read it. Unrelated to `User.is_deleted`, which *is* honoured. |
| created_by | ForeignKey | PROTECT, required | | Creating user. PROTECT so deleting a user can never cascade into their card library -- accounts are soft deleted instead. |
| created_at | DateTimeField | auto_now_add | auto | Creation time |
| updated_at | DateTimeField | auto_now | auto | Update time |

**Image Upload Path:** none. The card stores no files -- `front_image` and `back_image` are
foreign keys into `CardImage`, whose own `upload_to` is `card_images/generated/`. An upload
creates a row there like any generation.

`flashcard_images/` is legacy: nothing writes to it now, and it stays in the scorched-earth
sweep only so files left by the old schema can still be cleared.

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

**Note:** these image lines are unchanged from when `front_image` was an `ImageField`, and
still correct. The value passed is now a `CardImage` instance rather than a path, but it is
copied the same way -- which is what makes each version record the image it was showing at
the time, with no special handling.

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

### CardImage Model

`flashcards_cardimage` -- the media table. One row per image, however it came to exist.

A row is either something the bot generated, carrying the prompt, model and cost that
produced it, or something a person uploaded, where those are blank and the status is
`uploaded`. Nothing else separates them, and nothing downstream should care: a card points
at a row, and that is the whole relationship.

Append-only: regenerating inserts a new row and never edits or deletes an old one, so every
prompt and image ever tried stays inspectable.

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | BigAutoField | PK | auto | |
| version_group | UUIDField | index | | The card family. Keyed here rather than on a Flashcard id because editing a card creates a new row, which would orphan an id-keyed image. |
| card | ForeignKey(Flashcard) | SET_NULL, null | NULL | The card version whose text seeded the prompt. Provenance only. |
| status | CharField(12) | index | queued | queued, generating, succeeded, failed, uploaded |
| image | ImageField | null | NULL | `card_images/generated/`. Null for queued and failed rows, which have no file |
| prompt | TextField | blank | '' | Full prompt sent, look and feel included. Blank for uploads |
| prompt_seed | TextField | blank | '' | Card-derived portion, before style guidance |
| look_and_feel | TextField | blank | '' | Style actually used, snapshotted at generation time |
| look_and_feel_override | TextField | blank | '' | Per-image style. When set, replaces the global one. |
| model | CharField(200) | blank | '' | OpenRouter model slug. Blank for uploads |
| attempts | PositiveSmallIntegerField | | 0 | Incremented at claim time; capped by `max_attempts` |
| error | TextField | blank | '' | Last provider error |
| cost_usd | DecimalField(8,4) | null | NULL | Cost reported by OpenRouter |
| provider_response_id | CharField(200) | blank | '' | |
| requested_by | ForeignKey(User) | SET_NULL, null | NULL | Null when the bot queued it |
| is_auto | BooleanField | | False | True when queued by the bot |
| created_at / updated_at | DateTimeField | auto | auto | |
| started_at / finished_at | DateTimeField | null | NULL | Generation window |

**Indexes:** `(version_group, -created_at)`, `(status, created_at)`

**Note on single-accepted:** there is no `is_accepted` column. Acceptance is not a property
of an image, it is which image a card points at -- so it lives on `Flashcard.front_image`
and cannot disagree with itself.

This also removed a workaround. The rule "one accepted image per card family" could not be a
database constraint, because MySQL has no partial indexes and Django would have skipped a
conditional `UniqueConstraint` silently, leaving the guarantee true in SQLite tests and false
in production. It was enforced by hand in a transaction instead. A row holds one foreign key,
so the invariant is now structural and that machinery is gone.

---

### CardImagePreference Model

`flashcards_cardimagepreference` -- per-card image settings, currently just the model.

Keyed on `version_group` for the same reason `CardImage` is: editing a card creates a new
Flashcard row, so an id-keyed preference would be lost on any typo fix.

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | BigAutoField | PK | auto | |
| version_group | UUIDField | unique, index | | The card family |
| model | CharField(200) | blank | '' | Model slug for this card. Blank falls back to the global default. |
| updated_at | DateTimeField | auto | auto | |
| updated_by | ForeignKey(User) | SET_NULL, null | NULL | |

Resolve the effective model with `CardImageService.effective_model(card)` rather than reading
`ImageGenerationSettings.model`, or per-card choices are silently ignored.

---

### ImageGenerationSettings Model

`flashcards_imagegenerationsettings` -- singleton (pk is forced to 1) holding global
image-generation configuration.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| look_and_feel | TextField | (a minimalist style) | Appended to every prompt; overridable per image |
| model | CharField(200) | black-forest-labs/flux.2-pro | Default OpenRouter model |
| enabled | BooleanField | True | Master switch; when off nothing generates |
| auto_generate_new_cards | BooleanField | True | Queue an image the first time a card is seen |
| max_attempts | PositiveSmallIntegerField | 3 | Hard cap on provider calls per image row |
| updated_at | DateTimeField | auto | |
| updated_by | ForeignKey(User) | NULL | |

The OpenRouter API key is **not** stored here; it is read from `OPENROUTER_API_KEY`.

---

### SiteSettings Model

`flashcards_sitesettings` -- singleton (pk is forced to 1) holding site-wide appearance.

Deliberately separate from `ImageGenerationSettings`: that row configures the image
bot, this one configures what every visitor sees. Folding appearance into a model
named "Image generation settings" would be a lie in the Django admin.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| theme | CharField(20) | studio | One of `studio`, `dusk`, `clay`, `neon`. Becomes the `data-theme` attribute on `<html>` |
| updated_at | DateTimeField | auto | |
| updated_by | ForeignKey(User) | NULL | The admin who last changed it; withheld from non-admin API responses |

Read by everyone -- `GET /api/site-settings/` is AllowAny, because anonymous visitors
resolve the theme on every page load -- and written only by admins.

The theme ids are one contract shared with `THEMES` in
`frontend/src/composables/useTheme.js` and the `[data-theme=...]` blocks in
`frontend/src/css/app.scss`. A test asserts the model and the composable agree, since
a drifted id would leave visitors on a theme the stylesheet has no block for.

---

## Junction Tables (Auto-generated)

### flashcards_flashcard_tags

| Field | Type | Description |
|-------|------|-------------|
| id | AutoField | Primary key |
| flashcard_id | ForeignKey | Reference to Flashcard |
| tag_id | ForeignKey | Reference to Tag |

### flashcards_favorite

One row per user per favourited card family. Replaced the
`users_userprofile_favorite_cards` join table, which was never read or written.

**Table:** `flashcards_favorite`

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| id | BigAutoField | PK | auto | Primary key |
| user_id | ForeignKey | FK(User), CASCADE | required | Who saved it |
| version_group | UUIDField | indexed | required | The card family saved |
| created_at | DateTimeField | auto_now_add | now | When it was saved |

**Constraints:**
- `unique_together: (user, version_group)` -- the row's existence *is* the
  favourite, so double-favouriting is impossible in the database rather than by
  convention.
- Index on `(user, -created_at)` for the favourites list.

**Why `version_group` and not `card_id`:** editing a card creates a new Flashcard
row and retires the old one, so an id-keyed favourite would silently vanish the
moment a curator fixed a typo. Keying on the family also means the favourites
list always resolves to whichever version is currently live.

**Related field:** `flashcards_flashcard.favorite_count` is a lifetime tally of
how many times a card has been favourited. It is incremented on favourite and
deliberately never decremented, so it is not a count of current holders; it is
carried forward when a new version is created.

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
2. `users/0002_user_deleted_at_user_is_deleted.py` - Soft-delete fields on User
3. `flashcards/0001_initial.py` - Flashcard, Tag models
4. `flashcards/0002_*` - DailyCard, CardUsageLog models
5. `flashcards/0003_*` - Version fields (version_group, version_number, is_live)
6. `flashcards/0004_populate_version_groups.py` - Populate version_group UUIDs for existing cards
7. `flashcards/0005_fix_version_groups.py` - Data repair for the same fields
8. `flashcards/0006_flashcard_short_answer.py` - short_answer field
9. `flashcards/0007_alter_flashcard_created_by.py` - created_by gains the `created_cards` reverse name
10. `flashcards/0008_imagegenerationsettings_cardimage.py` - ImageGenerationSettings and CardImage
11. `flashcards/0009_cardimagepreference.py` - Per-card model choice
12. `flashcards/0010_sitesettings.py` - SiteSettings (the site theme)

This list had drifted: it previously stopped at `0005` and described it as the
short_answer field, which is actually `0006` -- `0005` is a data repair for the version
groups. Current as of `0010`.

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
