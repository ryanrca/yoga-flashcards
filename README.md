# Yoga Flashcard Admin App

A web-based admin system for creating, editing, managing, and versioning flashcards for yoga teacher study decks.

**Admin only.** All front-end routes require login. User accounts are managed via Django Admin. No sign-up or self-registration.  

The public-facing user site will be built later, once this admin system is complete.

---

## Core Features

### Flashcard Model

Each flashcard has:

- `title`: Short title of the card
- `phrase`: The main phrase (e.g. Sanskrit term)
- `definition`: The description or explanation
- `created_at`, `updated_at`, `deleted_at`
- `created_by`: ForeignKey to User
- `views`: Integer counter
- `enabled`: Boolean
- `front_photo`, `back_photo`: Two images

Images should **not** be stored in the database. They should be saved on disk (or object storage) with path references in the DB for better performance and maintainability.

---

### Versioning

- Any edit to **text fields** creates a new **version** of the card.
- Admin can view full version history.
- Admin can revert to any previous version.

---

### Tagging

- Many-to-many relationship between Cards and Tags.
- Tags have their own table.
- Admin can add, edit, delete tags globally.
- Tags can be attached/detached from cards.

---

## Image Management

- Two images per card (front and back).
- Stored on disk (or S3-compatible storage) with DB paths.
- Uploading a new image for a card replaces the existing one.
- Admin UI should support image upload and preview.

---

## API

Built with Django + Django REST Framework.

- RESTful endpoints for managing cards, versions, tags, and images.
- Pagination, search, sort for card list endpoint.
- Search must work across all text fields.

---

## Admin Frontend (Vue 3 + Quasar)

- Login screen for all unauthenticated users.
- Quasar Table page:
  - Server-side pagination, search, and sorting.
  - Searchable on all text fields.
  - Sortable on all columns.
- Card Detail page:
  - Show card data and images.
  - Version history list with revert button.
  - Image upload/replace feature.
  - Edit button opens modal with all editable fields, including tags.
- Tag Management page:
  - Add, edit, delete tags.

---

## CLI CSV Import Tool

- Django management command.
- Reads CSV file with columns for:
  - title
  - phrase
  - definition
  - tags
- Creates new cards in bulk.
- Optional dry-run mode.
- Supports upd

