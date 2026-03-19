import datetime

import factory
from django.test import TestCase
from faker import Faker

from django.contrib.auth import models as auth

from core import models

fake = Faker()

class MardidTestCase(TestCase):
    fixtures = ['test_countries', 'test_platforms', 'test_programs', 'test_regions']

class MissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Missions

    platform = factory.LazyFunction(
        lambda: models.Platforms.objects.order_by('?').first()
    )

    program = factory.LazyFunction(
        lambda: models.Programs.objects.order_by('?').first()
    )

    name = factory.LazyAttribute(
        lambda o: f"{Faker().random_element(['CAR', 'DY', 'JC'])}{Faker().random_int(min=2000, max=2030):04}{Faker().random_int(min=1, max=999):03}"
    )

class MissionLegFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Legs

    mission = factory.SubFactory(MissionFactory)
    number = factory.Sequence(lambda n: n + 1)
    start_date = factory.LazyFunction(
        lambda: datetime.date(
            year=fake.random_int(min=2000, max=2030),
            month=fake.random_int(min=1, max=12),
            day=fake.random_int(min=1, max=28)
        )
    )
    end_date = factory.LazyAttribute(
        lambda obj: obj.start_date + datetime.timedelta(days=fake.random_int(min=1, max=30))
    )
