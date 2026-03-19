from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


# MEDS uses a list of country codes that I think are from ICES
# https://www.ncbi.nlm.nih.gov/books/NBK7249/table/appd.T1/ dumped to mardid/fixtures/test_countries.json
class Countries(models.Model):
    id = models.AutoField(primary_key=True, db_column='country_seq')
    name = models.CharField(verbose_name=_("Name"), max_length=45, db_column='name')
    short_name = models.CharField(verbose_name=_("Short Name"), max_length=2, help_text=_("2-character country code"),
                                  db_column='short_name')
    code = models.IntegerField(verbose_name=_("Code"), blank=True, null=True, help_text=_("2-digit country code"),
                               db_column='code')

    class Meta:
        db_table = 'lu_countries'
        ordering = ['name']

    def __str__(self):
        return self.name


class DatasetStatus(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True, db_column='name')
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True, null=True,
                                   db_column='description')

    class Meta:
        db_table = 'lu_dataset_status'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.description}'

    @property
    def get_button_colour(self):
        name = self.name.upper()
        if name == 'EXPECTED':
            return 'btn-warning'
        elif name == 'LAB':
            return 'btn-outline-danger'
        elif name == 'SUBMITTED':
            return 'btn-success'
        elif name == 'RECEIVED':
            return 'btn-outline-success'

        return 'btn-outline-dark'


class DataTypes(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=25, unique=True, db_column='name')
    description = models.CharField(verbose_name=_("Description"), blank=True, null=True, max_length=255,
                                   db_column='description')

    def __str__(self):
        return f'{self.name} - {self.description}'

    class Meta:
        db_table = 'lu_dataset_types'
        ordering = ['name']


class FileTypes(models.Model):
    extension = models.CharField(verbose_name=_("Extension"), max_length=25, db_column='extension')
    description = models.CharField(verbose_name=_("Description"), max_length=255, db_column='description')

    def __str__(self):
        return f'{self.extension} - {self.description}'

    class Meta:
        db_table = 'lu_file_types'
        ordering = ['extension']


class Organizations(models.Model):
    name = models.CharField(verbose_name=_("Name"), db_column='name', max_length=50, unique=True)
    acronym = models.CharField(verbose_name=_("Acronym"), db_column='acronym', blank=True, null=True, max_length=25)
    code = models.IntegerField(verbose_name=_("Code"), db_column='code', blank=True, null=True)
    description = models.CharField(verbose_name=_("Description"), db_column='description', blank=True, null=True,
                                   max_length=255)
    country = models.ForeignKey(Countries, verbose_name=_("Country"), db_column='country_seq',
                                related_name="organizations", on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.name} - {self.description}'

    class Meta:
        db_table = 'lu_organizations'
        ordering = ['name']


class Participants(models.Model):
    id = models.AutoField(primary_key=True, db_column='participant_seq')

    last_name = models.CharField(verbose_name=_("Last Name"), max_length=50, db_column='last_name')
    first_name = models.CharField(verbose_name=_("First Name"), max_length=50, db_column='first_name')

    class Meta:
        db_table = 'lu_participants'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


def get_default_platform_country():
    country, created = Countries.objects.get_or_create(name='UNKNOWN', short_name='00')
    return country.pk


class Platforms(models.Model):
    id = models.AutoField(primary_key=True, db_column='platform_seq')

    # The description of the platform, for example the name of the vessel, or another
    # meaningful collection method (ie glider) of the data.
    name = models.CharField(verbose_name=_("Name"), max_length=100, db_column='name',
                            help_text=_("Platform name or description"), default='Unknown')
    country = models.ForeignKey(Countries, verbose_name=_("Country"), db_column='country_seq',
                                default=get_default_platform_country, related_name="platforms",
                                on_delete=models.PROTECT)
    call_sign = models.CharField(verbose_name=_("Call Sign"), max_length=10, db_column='call_sign',
                                 help_text=_("Platform call sign, if applicable"), default="------")
    max_speed = models.FloatField(verbose_name=_("Max Speed"), db_column='maximum_speed',
                                  help_text=_("Maximum speed of the platform in knots"), default=-999)
    ices_code = models.CharField(verbose_name=_("ICES Code"), db_column='ices_code', max_length=4, blank=True,
                                 null=True, help_text=_("ICES code"))
    ship_code = models.CharField(verbose_name=_("Ship Code"), db_column='ship_code', max_length=6, blank=True,
                                 null=True, help_text=_("OSCruise code"))

    class Meta:
        db_table = 'lu_platforms'
        ordering = ['name']

    def __str__(self):
        return self.name


class Positions(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=30, db_column='name')
    description = models.CharField(verbose_name=_("Description"), max_length=255, db_column='description')

    class Meta:
        db_table = 'lu_positions'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class Programs(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=45, unique=True, db_column='name')
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True, null=True,
                                   db_column='description')

    class Meta:
        db_table = 'lu_programs'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.description}'


class Status(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=45, unique=True, db_column='name')
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True, null=True,
                                   db_column='description')

    class Meta:
        db_table = 'lu_status'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} - {self.description}'


class Missions(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20,
                            help_text=_("The name of the cruise e.g 'CAR2025002'"), db_column='name')
    descriptor = models.CharField(verbose_name=_("Descriptor"), max_length=20, blank=True, null=True,
                                  help_text=_("MEDS assigned description of the cruise e.g '18QL25002'"),
                                  db_column='meds_descriptor')
    platform = models.ForeignKey(Platforms, verbose_name=_("Ship/Platform"), on_delete=models.PROTECT,
                                 related_name='cruises', db_column='platform_seq')
    program = models.ForeignKey(Programs, verbose_name=_("Program"), on_delete=models.PROTECT, related_name='missions',
                                db_column='program_seq')
    ppt_id = models.IntegerField(verbose_name=_("PPT id"), blank=True, null=True,
                                 help_text=_("Project Planning Tool ID to link to project details"), db_column='ppt_id')

    organizations = models.ManyToManyField(Organizations, verbose_name=_("Organizations"),
                                           through='MissionOrganizations')

    class Meta:
        db_table = 'missions'
        ordering = ['name']

    @property
    def start_date(self):
        first_leg = self.legs.order_by('start_date').first()
        return first_leg.start_date if first_leg else None

    @property
    def end_date(self):
        last_leg = self.legs.order_by('-end_date').first()
        return last_leg.end_date if last_leg else None

    @property
    def cheif_scientist(self):
        chief = self.legs.filter(participants__position__name__iexact='chief scientist')
        return ', '.join([chief]) if chief else None

    def __str__(self):
        return f'{self.name} - {self.descriptor}'


class MissionOrganizations(models.Model):
    id = models.AutoField(primary_key=True, db_column='mission_organization_seq')

    mission = models.ForeignKey(Missions, verbose_name=_("Mission"), on_delete=models.CASCADE,
                                related_name='mission_organizations', db_column='mission_seq')
    organization = models.ForeignKey(Organizations, verbose_name=_("Organization"), on_delete=models.PROTECT,
                                     related_name='organization_missions', db_column='organization_seq')

    class Meta:
        db_table = 'mission_organizations'
        ordering = ['mission', 'organization']


class Legs(models.Model):
    id = models.AutoField(primary_key=True, db_column='leg_seq')

    mission = models.ForeignKey(Missions, verbose_name=_("Mission"), on_delete=models.CASCADE, related_name='legs',
                                db_column='mission_seq')
    number = models.IntegerField(verbose_name=_("Leg Number"), db_column='number')
    start_date = models.DateField(verbose_name=_("Start Date"), db_column='start_date')
    end_date = models.DateField(verbose_name=_("End Date"), db_column='end_date')
    description = models.CharField(verbose_name=_("Description"), max_length=255, blank=True, null=True,
                                   db_column='description')

    regions = models.ManyToManyField('GeographicRegions', verbose_name=_("Geographic Regions"),
                                     through='MissionRegions')

    class Meta:
        db_table = 'legs'
        ordering = ['number']
        unique_together = ('mission', 'number')

    @property
    def chief_scientist(self):
        chief = self.leg_participants.filter(position__name__iexact='chief scientist').first()
        return f'{chief.participant}' if chief else None

    def __str__(self):
        return f'{self.mission.name} - Leg {self.number} ({self.start_date} to {self.end_date})'


class MissionParticipants(models.Model):
    id = models.AutoField(primary_key=True, db_column='mission_participant_seq')

    leg = models.ForeignKey(Legs, verbose_name=_("Leg"), on_delete=models.CASCADE,
                            related_name='leg_participants', db_column='leg_seq')
    participant = models.ForeignKey(Participants, verbose_name=_("Participant"), on_delete=models.PROTECT,
                                    related_name='participant_legs', db_column='participant_seq')
    position = models.ForeignKey(Positions, verbose_name=_("Position"), on_delete=models.PROTECT,
                                 related_name='position_legs', db_column='position_seq')

    class Meta:
        db_table = 'mission_participants'
        ordering = ['leg', 'position']

    def __str__(self):
        return f'{self.participant} - {self.position} on {self.leg}'


class GeographicRegions(models.Model):
    name = models.CharField(verbose_name=_('Name'), max_length=50, unique=True, db_column='name')
    description = models.CharField(verbose_name=_('Description'), max_length=255, blank=True, null=True,
                                   db_column='description')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'lu_geographic_regions'
        ordering = ['name']


class MissionRegions(models.Model):
    id = models.AutoField(primary_key=True, db_column='mission_region_seq')

    leg = models.ForeignKey(Legs, verbose_name=_("Leg"), on_delete=models.CASCADE, db_column='leg_seq'
                            , related_name='leg_regions')
    region = models.ForeignKey(GeographicRegions, verbose_name=_("Region"), on_delete=models.PROTECT,
                               related_name='region_legs', db_column='geographic_region_seq')

    class Meta:
        db_table = 'mission_regions'
        ordering = ['leg', 'region']


class Dataset(models.Model):
    id = models.AutoField(primary_key=True, db_column='dataset_seq')

    mission = models.ForeignKey(Missions, on_delete=models.CASCADE, related_name="datasets", db_column='mission_seq')
    data_type = models.ForeignKey(DataTypes, on_delete=models.PROTECT, related_name="datasets",
                                  db_column='data_type_seq')
    legacy_file_location = models.CharField(verbose_name=_("File location"), max_length=255, blank=True, null=True,
                                            db_column='legacy_file_location')
    status = models.ForeignKey(DatasetStatus, verbose_name=_("Dataset Status"), on_delete=models.PROTECT,
                               related_name="datasets", db_column='dataset_status_seq')

    @property
    def current_files(self):
        return self.files.filter(is_archived=False)

    @property
    def archived_files(self):
        return self.files.filter(is_archived=True)

    def __str__(self):
        return f'{self.data_type} : {self.status}'

    class Meta:
        db_table = 'datasets'
        ordering = ['mission', 'data_type']


class DataFiles(models.Model):
    id = models.AutoField(primary_key=True, db_column='file_seq')

    data = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='files', db_column='dataset_seq')
    file_name = models.CharField(verbose_name=_("File Name"), max_length=50, db_column='file_name')
    file_type = models.ForeignKey(FileTypes, on_delete=models.PROTECT, related_name='files', db_column='file_type_seq')
    submitted_by = models.ForeignKey('auth.User', on_delete=models.PROTECT, db_column='submitted_by')
    submitted_date = models.DateTimeField(auto_now_add=True, db_column='submitted_date')
    is_archived = models.BooleanField(verbose_name=_("Is archived"), default=False, db_column='is_archived')

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = 'files'
        ordering = ['file_name']


class DataFileComments(models.Model):
    id = models.AutoField(primary_key=True, db_column='file_comment_seq')

    datafile = models.ForeignKey(DataFiles, verbose_name=_("Data File"), on_delete=models.CASCADE,
                                 related_name='comments', db_column='file_seq')
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT, db_column='author_seq')
    comment = models.CharField(max_length=255, verbose_name=_("Comments"), db_column='comment')
    comment_date = models.DateTimeField(auto_now_add=True, db_column='comment_date')

    class Meta:
        db_table = 'file_comments'
        ordering = ['comment_date']


class DatasetComments(models.Model):
    id = models.AutoField(primary_key=True, db_column='dataset_comment_seq')

    dataset = models.ForeignKey(Dataset, verbose_name=_("Dataset"), on_delete=models.CASCADE, related_name='comments',
                                db_column='dataset_seq')
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT, db_column='author_seq')
    comment = models.CharField(max_length=255, verbose_name=_("Comments"), db_column='comment')
    comment_date = models.DateTimeField(auto_now_add=True, db_column='comment_date')

    class Meta:
        db_table = 'dataset_comments'
        ordering = ['comment_date']


class MissionComments(models.Model):
    id = models.AutoField(primary_key=True, db_column='mission_comment_seq')

    mission = models.ForeignKey(Missions, verbose_name=_("Mission"), on_delete=models.CASCADE, related_name='comments',
                                db_column='mission_seq')
    author = models.ForeignKey('auth.User', on_delete=models.PROTECT, db_column='author_seq')
    comment = models.CharField(max_length=255, verbose_name=_("Comments"), db_column='comment')
    comment_date = models.DateTimeField(auto_now_add=True, db_column='comment_date')

    class Meta:
        db_table = 'mission_comments'
        ordering = ['comment_date']


class ProcessingStatus(models.Model):
    id = models.AutoField(primary_key=True, db_column='processing_seq')

    dataset = models.ForeignKey(Dataset, verbose_name=_("Dataset"), on_delete=models.CASCADE, related_name='processing',
                                db_column='dataset_seq')
    assigned_to = models.ForeignKey('auth.User', verbose_name=_("Assigned"), on_delete=models.PROTECT,
                                    related_name='processing', db_column='assigned_to')
    assigned_date = models.DateTimeField(auto_now=True, db_column='assigned_date')
    status = models.ForeignKey(Status, verbose_name=_("Status"), on_delete=models.PROTECT, related_name='processing',
                               db_column='status_seq')


class GroupProfiles(models.Model):
    group = models.OneToOneField('auth.Group', on_delete=models.CASCADE, related_name='profile')
    description = models.TextField(_("Description"), blank=True, null=True)

    def __str__(self):
        return f"{self.group.name} - {self.description or _('No description')}"
