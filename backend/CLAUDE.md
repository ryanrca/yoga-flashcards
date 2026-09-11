# Backend - Claude Code Instructions

## Quick Reference

```
Framework:  Django 4.2.7 + DRF 3.14.0
Database:   MySQL 8.0
Port:       8000
Tests:      python -m pytest
Settings:   yoga_flashcards/settings.py
```

## Architecture

- **Thin views, fat models** -- business logic in `services.py`, not views
- **DRF ModelViewSets** for REST endpoints
- **Serializers** for all validation (never use raw `request.data`)
- **Self-service endpoints get their own narrow serializer** -- `ProfileUpdateSerializer`
  whitelists editable fields so a user cannot write `role` or `is_active` on themselves
- **Session-based auth** (not JWT)
- **Apps by domain**: `flashcards`, `users`, `core`
- **Custom user model**: `AUTH_USER_MODEL = 'users.User'`

## Versioning (Critical Pattern)

Card edits never modify in place. The serializer's `update()` calls `instance.create_new_version()`:
- Old version gets `is_live=False`
- New version gets `version_number+1`, `is_live=True`, same `version_group` UUID
- Revert also creates a NEW version (copies content from target, highest version_number)
- Queries for "current" cards filter on `is_live=True, is_active=True`

## Role Hierarchy

- `User.is_admin()` -- role='admin' or is_superuser
- `User.is_curator()` -- role in ('curator', 'admin') or is_superuser
- Permission classes: `IsCuratorOrAdmin`, `IsAdminOnly` in `flashcards/permissions.py`
- Use `IsAdminOnly`, never DRF's `IsAdminUser` -- the latter checks `is_staff`, which is
  unrelated to the `role` field and locks out a role='admin' user who is not staff

## Key Files

| File | Purpose |
|------|---------|
| `flashcards/models.py` | Flashcard (versioned), Tag, DailyCard, CardUsageLog |
| `flashcards/serializers.py` | Validation + version creation in `update()` |
| `flashcards/services.py` | DailyCardService (card rotation with cycle tracking) |
| `flashcards/permissions.py` | IsCuratorOrAdmin, IsAdminOnly |
| `flashcards/views.py` | FlashcardViewSet, TagViewSet |
| `users/models.py` | User (AbstractUser + role), UserProfile |
| `users/views.py` | login, logout, register, auth_status, profile, change_password, user management |
| `yoga_flashcards/settings.py` | CORS, REST_FRAMEWORK, middleware config |

## Testing

```bash
python -m pytest                              # All tests
python -m pytest flashcards/                  # Single app
python -m pytest -v --cov=flashcards --cov=users  # With coverage
```

Test structure: `{app}/tests/test_models.py`, `test_views.py`, `test_services.py`, `factories.py`
Uses pytest with `@pytest.mark.django_db` and Factory Boy.

## Management Commands

- `seed_initial_data` -- imports/exports flashcard JSON (`--pull` to export)
- `import_cards` -- imports from CSV (`--dry-run` supported)

## Style

- 4 spaces, `snake_case` for functions/variables, `CamelCase` for classes
- No emojis in code or comments
