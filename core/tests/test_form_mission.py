from bs4 import BeautifulSoup
from crispy_forms.utils import render_crispy_form
from django.contrib.auth.models import User, Group
from django.test import tag, RequestFactory, Client
from django.urls import reverse_lazy

from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionLegFactory, MissionDatasetFactory
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


    def test_mission_legs_form_no_existing_legs(self):
        # provided a mission that has no legs, we should get a mission form with the leg's initial value set to 1
        form = form_mission.MissionLegForm(self.mission)
        soup = self.get_mission_leg_soup(form)

        expected_leg = 1
        leg_elm = soup.find(id="id_number")
        self.assertTrue(leg_elm is not None)
        self.assertEqual(leg_elm.attrs['value'], str(expected_leg))

    @tag('test_mission_legs_form_with_existing_legs')
    def test_mission_legs_form_with_existing_legs(self):
        # provided a mission that has existing legs, we should get a mission form with the leg's initial value
        # set to the number of existing legs + 1
        batch = 3
        MissionLegFactory.reset_sequence(0)
        MissionLegFactory.create_batch(batch, mission=self.mission)

        form = form_mission.MissionLegForm(self.mission)
        soup = self.get_mission_leg_soup(form)

        leg_elm = soup.find(id="id_number")
        self.assertTrue(leg_elm is not None)
        self.assertEqual(leg_elm.attrs['value'], str(batch+1))

    def test_mission_legs_form_with_existing_leg(self):
        # if the MissionLegForm is provided a leg, the initial value should be set to that leg's number
        initial_leg = MissionLegFactory.create(mission=self.mission)
        leg = MissionLegFactory.create(mission=self.mission)

        form = form_mission.MissionLegForm(self.mission, instance=leg)
        soup = self.get_mission_leg_soup(form)

        leg_elm = soup.find(id="id_number")
        self.assertTrue(leg_elm is not None)
        self.assertEqual(leg_elm.attrs['value'], str(leg.number))

    def test_mission_legs_form_with_existing_leg(self):
        # if the MissionLegForm is provided a leg, there should be an additional field for adding Geographic Regions
        # to the provided leg
        initial_leg = MissionLegFactory.create(mission=self.mission)
        leg = MissionLegFactory.create(mission=self.mission)

        form = form_mission.MissionLegForm(self.mission, instance=leg)
        soup = self.get_mission_leg_soup(form)

        leg_elm = soup.find(id="id_number")
        self.assertTrue(leg_elm is not None)
        self.assertEqual(leg_elm.attrs['value'], str(leg.number))
