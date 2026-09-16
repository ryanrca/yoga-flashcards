"""
Tests for the site-wide appearance settings.

The theme is read by everyone and written only by admins, and that asymmetry is
the entire point of the endpoint, so it is what these exercise hardest.

The curator boundary gets the most attention deliberately: curators DO have
access to the image settings sitting immediately next door, and `is_curator()`
returns true for admins as well, so "curator cannot change the theme" is the
easiest thing here to get quietly wrong.
"""
import os

import pytest
from rest_framework import status

from flashcards.models import SiteSettings
from users.tests.factories import UserFactory

URL = '/api/site-settings/'


@pytest.mark.django_db
class TestSiteSettingsRead:
    """GET is AllowAny: signed-out visitors need the theme to paint the page."""

    def test_anonymous_can_read_the_theme(self, api_client):
        response = api_client.get(URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['theme'] == SiteSettings.DEFAULT_THEME

    def test_anonymous_sees_the_theme_and_nothing_else(self, api_client):
        admin = UserFactory(role='admin', username='secret-admin')
        config = SiteSettings.load()
        config.theme = SiteSettings.Theme.DUSK
        config.updated_by = admin
        config.save()

        response = api_client.get(URL)

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {'theme'}
        assert response.data['theme'] == 'dusk'
        # The audit fields name an admin; an anonymous caller must not learn it.
        assert 'secret-admin' not in str(response.data)

    def test_plain_user_also_sees_only_the_theme(self, api_client):
        admin = UserFactory(role='admin', username='another-admin')
        config = SiteSettings.load()
        config.updated_by = admin
        config.save()

        api_client.force_authenticate(user=UserFactory(role='user'))
        response = api_client.get(URL)

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {'theme'}

    def test_curator_also_sees_only_the_theme(self, api_client):
        api_client.force_authenticate(user=UserFactory(role='curator'))
        response = api_client.get(URL)

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {'theme'}

    def test_admin_sees_the_audit_fields(self, api_client):
        admin = UserFactory(role='admin', username='the-admin')
        config = SiteSettings.load()
        config.updated_by = admin
        config.save()

        api_client.force_authenticate(user=admin)
        response = api_client.get(URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['updated_by_username'] == 'the-admin'
        assert response.data['updated_at'] is not None


@pytest.mark.django_db
class TestSiteSettingsWrite:
    """PUT is IsAdminOnly. Appearance is a whole-site decision."""

    def test_admin_can_change_the_theme(self, api_client):
        api_client.force_authenticate(user=UserFactory(role='admin'))

        response = api_client.put(URL, {'theme': 'clay'}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['theme'] == 'clay'
        assert SiteSettings.load().theme == 'clay'

    def test_the_change_is_attributed_to_the_admin(self, api_client):
        admin = UserFactory(role='admin', username='deciding-admin')
        api_client.force_authenticate(user=admin)

        api_client.put(URL, {'theme': 'neon'}, format='json')

        config = SiteSettings.load()
        assert config.updated_by == admin
        assert config.updated_at is not None

    def test_curator_cannot_change_the_theme(self, api_client):
        # The load-bearing case: curators can edit the image settings next
        # door, and is_curator() is true for admins, so this boundary is the
        # easy one to get wrong.
        api_client.force_authenticate(user=UserFactory(role='curator'))

        response = api_client.put(URL, {'theme': 'neon'}, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert SiteSettings.load().theme == SiteSettings.DEFAULT_THEME

    def test_plain_user_cannot_change_the_theme(self, api_client):
        api_client.force_authenticate(user=UserFactory(role='user'))

        response = api_client.put(URL, {'theme': 'neon'}, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert SiteSettings.load().theme == SiteSettings.DEFAULT_THEME

    def test_anonymous_cannot_change_the_theme(self, api_client):
        response = api_client.put(URL, {'theme': 'neon'}, format='json')

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN
        )
        assert SiteSettings.load().theme == SiteSettings.DEFAULT_THEME

    def test_unknown_theme_is_rejected(self, api_client):
        # A bad value here would leave every visitor on a data-theme the
        # stylesheet has no block for, so it must not reach the database.
        api_client.force_authenticate(user=UserFactory(role='admin'))

        response = api_client.put(URL, {'theme': 'dark'}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert SiteSettings.load().theme == SiteSettings.DEFAULT_THEME

    def test_every_advertised_theme_is_accepted(self, api_client):
        api_client.force_authenticate(user=UserFactory(role='admin'))

        for choice in SiteSettings.Theme.values:
            response = api_client.put(URL, {'theme': choice}, format='json')
            assert response.status_code == status.HTTP_200_OK, choice
            assert SiteSettings.load().theme == choice


@pytest.mark.django_db
class TestSiteSettingsSingleton:
    """One row, always pk=1, never deletable."""

    def test_load_creates_exactly_one_row(self):
        assert SiteSettings.objects.count() == 0
        first = SiteSettings.load()
        second = SiteSettings.load()
        assert first.pk == second.pk == 1
        assert SiteSettings.objects.count() == 1

    def test_save_always_pins_pk_to_one(self):
        SiteSettings.load()
        stray = SiteSettings(theme=SiteSettings.Theme.CLAY)
        stray.save()

        assert stray.pk == 1
        assert SiteSettings.objects.count() == 1
        assert SiteSettings.load().theme == 'clay'

    def test_delete_is_refused(self):
        config = SiteSettings.load()
        with pytest.raises(NotImplementedError):
            config.delete()
        assert SiteSettings.objects.count() == 1


@pytest.mark.django_db
class TestThemeIdsMatchTheFrontend:
    """
    The model's Theme ids and the frontend's THEMES list are one contract split
    across two languages: the id goes into data-theme, and app.scss only has a
    block for the four it knows. If they drift, visitors get an unstyled page.

    Skipped when only the backend tree is present, which is the case inside the
    backend image.
    """

    def test_ids_match_use_theme_js(self):
        path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..',
            'frontend', 'src', 'composables', 'useTheme.js',
        )
        if not os.path.exists(path):
            pytest.skip('frontend tree not present (backend-only checkout)')

        with open(path) as handle:
            source = handle.read()

        import re
        frontend_ids = re.findall(r"id: '([a-z]+)'", source)
        assert frontend_ids, 'could not parse THEMES out of useTheme.js'
        assert frontend_ids == list(SiteSettings.Theme.values)
