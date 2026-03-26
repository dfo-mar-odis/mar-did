from django.test import TestCase, RequestFactory, tag
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden
from core.utils.authentication import authenticated, redirect_if_not_authenticated, redirect_if_not_superuser
from unittest.mock import patch


class TestUtilsAuthentication(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')
        self.group = Group.objects.create(name='MarDID Maintainers')
        self.user.groups.add(self.group)

    def test_authenticated_with_group(self):
        # Test if the user is authenticated when they belong to the specified group.
        # Input: User in 'MarDID Maintainers' group.
        # Expected Result: authenticated() returns True.
        request = self.factory.get('/')
        request.user = self.user
        self.assertTrue(authenticated(request, groups=['MarDID Maintainers']))

    def test_authenticated_without_group(self):
        # Test if the user is not authenticated when they do not belong to the specified group.
        # Input: User not in 'NonExistentGroup'.
        # Expected Result: authenticated() returns False.
        request = self.factory.get('/')
        request.user = self.user
        self.assertFalse(authenticated(request, groups=['NonExistentGroup']))

    def test_redirect_if_not_authenticated_redirects(self):
        # Test if the user is redirected to the login page when not authenticated.
        # Input: User not in 'MarDID Maintainers' group.
        # Expected Result: redirect_if_not_authenticated() returns HttpResponseRedirect to login page.
        request = self.factory.get('/')
        request.user = self.user
        request.user.groups.clear()  # Remove user from all groups
        response = redirect_if_not_authenticated(request, next_page='/next', groups=['MarDID Maintainers'])
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertIn('login', response.url)

    def test_redirect_if_not_authenticated_no_redirect(self):
        # Test if the user is not redirected when they are authenticated.
        # Input: User in 'MarDID Maintainers' group.
        # Expected Result: redirect_if_not_authenticated() returns None.
        request = self.factory.get('/')
        request.user = self.user
        response = redirect_if_not_authenticated(request, next_page='/next', groups=['MarDID Maintainers'])
        self.assertIsNone(response)

    def test_redirect_if_not_superuser_redirects(self):
        # Test if the user is forbidden access when they are not a superuser.
        # Input: Non-superuser user.
        # Expected Result: redirect_if_not_superuser() returns HttpResponseForbidden.
        request = self.factory.get('/')
        request.user = self.user
        response = redirect_if_not_superuser(request, next_page='/next', groups=['MarDID Maintainers'])
        self.assertIsInstance(response, HttpResponseForbidden)

    @tag('test_redirect_if_not_superuser_no_redirect')
    def test_redirect_if_not_superuser_no_redirect(self):
        # Test if the user is not redirected or forbidden when they are a superuser.
        # Input: Superuser.
        # Expected Result: redirect_if_not_superuser() returns None.
        request = self.factory.get('/')
        request.user = self.superuser
        with patch('core.utils.authentication.redirect_if_not_authenticated', return_value=None):
            response = redirect_if_not_superuser(request, next_page='/next', groups=['MarDID Maintainers'])
            self.assertIsNone(response)