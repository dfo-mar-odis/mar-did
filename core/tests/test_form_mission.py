from bs4 import BeautifulSoup
from crispy_forms.utils import render_crispy_form
from django.contrib.auth.models import User, Group
from django.test import tag, RequestFactory, Client
from django.urls import reverse_lazy

from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionLegFactory, MissionDatasetFactory, MissionCommentFactory
from core.views.forms import form_mission


@tag('test_form_mission')
class TestFormMission(MardidTestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.superuser = User.objects.create_superuser(username='admin', password='password')
        self.group = Group.objects.get_or_create(name='MarDID Maintainers')[0]
        self.user.groups.add(self.group)

    def test_mission_form_anonymous_user(self):
        # and anonymous user should not be able to access the new mission form
        # and should be redirected to the login page
        response = self.client.get(reverse_lazy('core:new_mission_view'))
        self.assertEqual(response.status_code, 302)

    def test_mission_form_anonymous_user_mission_form(self):
        mission = MissionFactory(name='JC28302')
        response = self.client.get(reverse_lazy('core:update_mission_view', args=[mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        # an anonymous user should not be able to see the mission form for editing a mission
        mission_form = soup.find(id="form_id_mission")
        self.assertIsNone(mission_form)

        # an anonymous user should not be able to see the legs form for editing mission legs
        legs_form = soup.find(id="form_id_mission_legs")
        self.assertIsNone(legs_form)

        # an anonymous user should not be able to see the datasets form for editing mission legs
        datasets_from = soup.find(id="form_id_mission_datasets")
        self.assertIsNone(datasets_from)

    def test_mission_form_anonymous_user_form_details(self):
        # an anonymous user should be able to see the mission details card
        mission = MissionFactory(name='JC28302')
        MissionLegFactory(mission=mission)
        MissionDatasetFactory(mission=mission)

        response = self.client.get(reverse_lazy('core:update_mission_view', args=[mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        details = soup.find(id="div_id_mission_details")
        self.assertIsNotNone(details)

        # An anonymous user should be able to see the mission legs table
        legs_table = soup.find(id="table_id_mission_leg_list")
        self.assertIsNotNone(legs_table)

        # An anonymous user should not see a delete button for each leg
        button = legs_table.find("button", attrs={"class": "btn-danger"})
        self.assertIsNone(button)

        # An anonymous user should be able to see the mission legs table
        datasets_table = soup.find(id="table_id_mission_dataset_list")
        self.assertIsNotNone(datasets_table)

        # An anonymous user should not see a delete button for each dataset
        button = datasets_table.find("button", attrs={"class": "btn-danger"})
        self.assertIsNone(button)

    def test_mission_form_authenticated_user_new_mission(self):
        # if a user is logged in then the form element should be visible
        self.client.login(username='testuser', password='password')

        response = self.client.get(reverse_lazy('core:new_mission_view'))
        soup = BeautifulSoup(response.content, 'html.parser')
        form = soup.find(id="form_id_mission")
        self.assertIsNotNone(form)

    def test_mission_form_authenticated_user_update_mission(self):

        self.client.login(username='admin', password='password')

        mission = MissionFactory(name='JC28302')
        MissionLegFactory.create(mission=mission)
        MissionDatasetFactory(mission=mission)

        response = self.client.get(reverse_lazy('core:update_mission_view', args=[mission.pk]))
        soup = BeautifulSoup(response.content, 'html.parser')

        form = soup.find(id="form_id_mission")
        self.assertIsNotNone(form)

        # if a user is logged in then form for editing mission legs should be visible
        form_legs = soup.find(id="form_id_mission_legs")
        self.assertIsNotNone(form_legs)

        # if a user is logged in then form for editing mission legs should be visible
        table_legs = soup.find(id="table_id_mission_leg_list")
        self.assertIsNotNone(table_legs)

        # if a user is logged in then they should see a delete button for each dataset
        button = table_legs.find("button", attrs={"class": "btn-danger"})
        self.assertIsNotNone(button)

        icon = button.find("span", attrs={"class": "bi bi-x-square"})
        self.assertIsNotNone(icon)

        # if a user is logged in then form for editing mission datasets should be visible
        details = soup.find(id="form_id_mission_datasets")
        self.assertIsNotNone(details)

        # if a user is logged in then they should see a list of missions
        table_dataset = soup.find(id="table_id_mission_dataset_list")
        self.assertIsNotNone(table_dataset)

        # if a user is logged in then they should see a delete button for each dataset
        button = table_dataset.find("button", attrs={"class": "btn-danger"})
        self.assertIsNotNone(button)

        icon = button.find("span", attrs={"class": "bi bi-x-square"})
        self.assertIsNotNone(icon)


class TestFormMissionLegs(MardidTestCase):

    def setUp(self):
        self.mission = MissionFactory.create()

    def get_mission_leg_soup(self, form):
        crispy = render_crispy_form(form)
        soup = BeautifulSoup(crispy, 'html.parser')
        return soup


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