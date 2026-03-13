from django.test import tag, TestCase, RequestFactory
from core.views import view_missions

class TestCruiseView(TestCase):

    def setUp(self):
        factory = RequestFactory()

    def test_init(self):
        view = view_cruises.MissionListView.as_view()

        self.assertIsNotNone(view)

    def test_list(self):
        view_cruises.list_cruises()