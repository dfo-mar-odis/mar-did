import datetime

import factory
from django.contrib.auth.models import User
from django.test import TestCase
from faker import Faker

from core import models

fake = Faker()

class MardidTestCase(TestCase):
    fixtures = [ 'init_group_fixtures', 'init_dataset_status', 'init_countries',
                 'init_organizations', 'init_platforms', 'init_regions', 'init_programs',
                 'init_positions', 'init_datatypes', 'init_file_types']


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
        lambda
            o: f"{Faker().random_element(['CAR', 'DY', 'JC'])}{Faker().random_int(min=2000, max=2030):04}{Faker().random_int(min=1, max=999):03}"
    )


class MissionWithLegsFactory(MissionFactory):
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

    @factory.post_generation
    def mission_legs(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # If a specific number of legs is provided, create that many
            for _ in range(extracted):
                MissionLegFactory(mission=self)
        else:
            # Default to creating one mission leg
            MissionLegFactory(mission=self)

class MissionLegFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Legs

    mission = factory.SubFactory(MissionFactory)
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

class MissionDatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Datasets

    mission = factory.SubFactory(MissionWithLegsFactory)
    datatype = factory.LazyFunction(
        lambda: models.DataTypes.objects.order_by('?').first()
    )
    status = factory.LazyFunction(
        lambda: models.DatasetStatus.objects.get(name__iexact="EXPECTED")
    )


class MissionDataFilesFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.DataFiles

    dataset = factory.SubFactory(MissionDatasetFactory)
    file_name = factory.LazyAttribute(lambda o: f"{fake.file_name(extension='txt')}")
    file_type = factory.LazyFunction(
        lambda: models.FileTypes.objects.order_by('?').first()
    )
    submitted_by = factory.LazyFunction(
        lambda: User.objects.order_by('?').first()
    )


class MissionCommentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.MissionComments

    mission = factory.SubFactory(MissionFactory)
    author = factory.SelfAttribute('author')
    comment = factory.Faker('paragraph')


class DatasetLocationsFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.DatasetLocations

    datatype = factory.LazyFunction(
        lambda: models.DataTypes.objects.order_by('?').first()
    )
    output_dir = 'test_output'