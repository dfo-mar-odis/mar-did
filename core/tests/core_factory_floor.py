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


class CruiseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Cruises
        exclude = ('leg', 'year',)

    start_date = factory.LazyFunction(lambda: Faker().date_object())
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + datetime.timedelta(days=21))
    platform = factory.LazyFunction(
        lambda: models.Platforms.objects.order_by('?').first() or PlatformFactory()
    )
    leg = factory.LazyFunction(lambda: f"{Faker().random_int(min=1, max=999):03}")
    year = factory.LazyAttribute(lambda o: datetime.datetime.strftime(o.start_date, '%Y'))
    name = factory.LazyAttribute(
        lambda o: f"{Faker().random_element(['CAR', 'DY', 'JC'])}{o.year}{o.leg}"
    )
    descriptor = factory.LazyAttribute(
        lambda o: f"{o.platform.ship_code}{o.year}{o.leg}"
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


    @factory.post_generation
    def programs(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.programs.set(extracted)
        else:
            programs = models.Programs.objects.all().order_by('?')
            if programs and programs.exists():
                self.programs.set(programs[:Faker().random_int(min=1, max=2)])

    @factory.post_generation
    def datasets(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.datasets.set(extracted)
        else:
            datasets = models.Dataset.objects.all().order_by('?')
            if datasets and datasets.exists():
                self.datasets.set(datasets[:Faker().random_int(min=5, max=10)])
