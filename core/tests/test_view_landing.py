from django.template.loader import render_to_string
from django.test import tag, TestCase

from core.views import view_landing


@tag('landing', 'landing_navigation', 'landing_unauthenticated')
class TestLandingNavigationUnauthenticated(TestCase):

    def setUp(self):
        pass

    def test_views_menu_for_unauthenticated_user(self):
        # Render the navbar template with an unauthenticated user
        context = {'user': None}  # Simulate an unauthenticated user
        rendered_template = render_to_string('core/view_landing.html', context)

        # Check that 'Cruises' menu is visible
        self.assertIn('href="/en/cruise"', rendered_template)

        # Check that 'Add a Cruise' menu is hidden
        self.assertNotIn('href="/en/cruise/new"', rendered_template)

        # Check that 'Lookup Tables' navigation is hidden
        self.assertNotIn('id="lookupDropdown"', rendered_template)


@tag('landing', 'landing_navigation', 'landing_chief_scientist')
class TestLandingNavigationUnauthenticated(TestCase):

    def setUp(self):
        pass

    def test_views_menu_for_unauthenticated_user(self):
        # Render the navbar template with an unauthenticated user
        context = {'user': None}  # Simulate an unauthenticated user
        rendered_template = render_to_string('core/view_landing.html', context)

        # Check that 'Cruises' menu is visible
        self.assertIn('href="/en/cruise"', rendered_template)

        # Check that 'Add a Cruise' menu is hidden
        self.assertNotIn('href="/en/cruise/new"', rendered_template)

        # Check that 'Lookup Tables' navigation is hidden
        self.assertNotIn('id="lookupDropdown"', rendered_template)