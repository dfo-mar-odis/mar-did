from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.test import tag
from django.urls import reverse_lazy

from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionCommentFactory


@tag('test_form_mission_comments')
class TestFormMissionComments(MardidTestCase):

    def setUp(self):
        self.mission = MissionFactory.create()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')

    # anonymous users
    def test_mission_comments_form_anonymous_user(self):
        response = self.client.get(reverse_lazy('core:update_mission_view', args=[self.mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # should not see the comment form
        comment_form = soup.find(id="form_id_mission_comments")
        self.assertIsNone(comment_form)

        # should see the comments section
        comments_section = soup.find(id="table_id_mission_comment_list")
        self.assertIsNotNone(comments_section)

        # should not see a delete button for comments
        button = comments_section.find("button", attrs={"class": "btn-danger"})
        self.assertIsNone(button)

        # should not see an edit button for comments
        button = comments_section.find("button", attrs={"class": "btn-secondary"})
        self.assertIsNone(button)

    # authenticated users
    def test_mission_comments_form_authenticated_user(self):
        self.client.login(username='testuser', password='password')

        MissionCommentFactory(mission=self.mission, author=self.user)
        MissionCommentFactory(mission=self.mission, author=self.superuser)

        response = self.client.get(reverse_lazy('core:update_mission_view', args=[self.mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # should see the comment form
        comment_form = soup.find(id="form_id_mission_comments")
        self.assertIsNotNone(comment_form)

        # should see the comments section
        comments_section = soup.find(id="table_id_mission_comment_list")
        self.assertIsNotNone(comments_section)

        # should not see a delete button for comments
        button = comments_section.find("button", attrs={"class": "btn-danger"})
        self.assertIsNotNone(button)

        # should see an edit button for comments that the user authored
        # Find the <div> element with text matching self.user.username
        div = comments_section.find('div', text=self.user.username)
        self.assertIsNotNone(div)

        # Get the parent <tr> element
        row = div.find_parent().find_parent("tr")
        self.assertIsNotNone(row)

        span_edit_button = row.find("span", attrs={"class": "bi bi-pencil-square"})
        self.assertIsNotNone(span_edit_button)

        # should not see an edit button for comments that another user authored
        # Find the <div> element with text matching self.superuser.username
        div = comments_section.find('div', text=self.superuser.username)
        self.assertIsNotNone(div)

        # Get the parent <tr> element
        row = div.find_parent().find_parent("tr")
        self.assertIsNotNone(row)

        span_edit_button = row.find("span", attrs={"class": "bi bi-pencil-square"})
        self.assertIsNone(span_edit_button)

    # superusers
    def test_mission_comments_form_superuser(self):
        self.client.login(username='admin', password='password')

        MissionCommentFactory(mission=self.mission, author=self.user)
        MissionCommentFactory(mission=self.mission, author=self.superuser)

        response = self.client.get(reverse_lazy('core:update_mission_view', args=[self.mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # should see the comment form
        comment_form = soup.find(id="form_id_mission_comments")
        self.assertIsNotNone(comment_form)

        # should see the comments section
        comments_section = soup.find(id="table_id_mission_comment_list")
        self.assertIsNotNone(comments_section)

        # should see a delete button for comments
        button = comments_section.find("button", attrs={"class": "btn-danger"})
        self.assertIsNotNone(button)

        # should see an edit button for comments that the user authored
        # Find the <div> element with text matching self.user.username
        div = comments_section.find('div', text=self.superuser.username)
        self.assertIsNotNone(div)

        # Get the parent <tr> element
        row = div.find_parent().find_parent("tr")
        self.assertIsNotNone(row)

        span_edit_button = row.find("span", attrs={"class": "bi bi-pencil-square"})
        self.assertIsNotNone(span_edit_button)

        # should not see an edit button for comments that another user authored
        # Find the <div> element with text matching self.superuser.username
        div = comments_section.find('div', text=self.user.username)
        self.assertIsNotNone(div)

        # Get the parent <tr> element
        row = div.find_parent().find_parent("tr")
        self.assertIsNotNone(row)

        span_edit_button = row.find("span", attrs={"class": "bi bi-pencil-square"})
        self.assertIsNone(span_edit_button)
