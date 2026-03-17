from bs4 import BeautifulSoup
from crispy_forms.utils import render_crispy_form

from core.tests.core_factory_floor import MardidTestCase, MissionFactory, MissionLegFactory
from core.views.forms import form_mission


class TestFormMission(MardidTestCase):

    def setUp(self):
        pass

    def test_mission_form(self):
        self.assertTrue(True)


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

    def test_mission_legs_form_with_existing_legs(self):
        # provided a mission that has existing legs, we should get a mission form with the leg's initial value
        # set to the number of existing legs + 1
        batch = 3
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
