import datetime

import factory
from faker import Faker

from django.contrib.auth import models as auth

from core import models

fake = Faker()
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth.User

    first_name = factory.LazyFunction(lambda: fake.name())
    last_name = factory.LazyFunction(lambda: fake.name())
    user_name = factory.LazyFunction(lambda o: f"{o.last_name.lower()}{o.first_name.lower()[1]}")


class LocationsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GeographicRegions

    name = factory.LazyFunction(lambda: fake.name())


class PlatformFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Platforms

    name = factory.LazyFunction(lambda: fake.name())
    ship_code = factory.LazyFunction(lambda: ''.join(fake.random_choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4)))


class CruiseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Cruises

    name = factory.LazyFunction(
        lambda: f"{Faker().random_element(['CAR', 'DY', 'JC'])}{datetime.date.today().year}{Faker().random_int(min=1, max=999):03}"
    )
    start_date = factory.LazyFunction(lambda: Faker().date_object())
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + datetime.timedelta(days=21))
    platform = factory.LazyFunction(
        lambda: models.Platforms.objects.order_by('?').first() or PlatformFactory()
    )

    @factory.post_generation
    def chief_scientists(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.chief_scientists.set(extracted)
        else:
            group = auth.Group.objects.filter(name='Chief Scientists').first()
            if group and group.user_set.exists():
                self.chief_scientists.set(group.user_set.order_by('?')[:Faker().random_int(min=1, max=2)])
            else:
                self.chief_scientists.set(UserFactory.create_batch(size=Faker().random_int(min=1, max=2)))

    @factory.post_generation
    def data_managers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.data_managers.set(extracted)
        else:
            group = auth.Group.objects.filter(name='Data Managers').first()
            if group and group.user_set.exists():
                self.data_managers.set(group.user_set.order_by('?')[:Faker().random_int(min=1, max=2)])
            else:
                self.data_managers.set(UserFactory.create_batch(size=Faker().random_int(min=1, max=2)))

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.locations.set(extracted)
        else:
            locations = models.GeographicRegions.objects.all().order_by('?')
            if locations and locations.exists():
                self.locations.set(locations[:Faker().random_int(min=1, max=2)])
            else:
                self.locations.set(LocationsFactory.create_batch(size=Faker().random_int(min=1, max=2)))

    @factory.post_generation
    def datasets(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.datasets.set(extracted)
        else:
            self.data.set(DatasetFactory.create_batch(size=Faker().random_int(min=5, max=10), cruise=self))


class DatasetFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = models.Dataset

    cruise = factory.SubFactory(CruiseFactory)
    data_type = factory.LazyFunction(
        lambda: models.DataTypes.objects.all().order_by('?').first()
    )
    status = factory.LazyFunction(
        lambda: models.DataStatus.objects.filter(name__in=["Expected", "Received"]).order_by('?').first()
    )