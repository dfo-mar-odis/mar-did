from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


# MEDS uses a list of country codes that I think are from ICES
# https://www.ncbi.nlm.nih.gov/books/NBK7249/table/appd.T1/ dumped to mardid/fixtures/countries.json
class Country(models.Model):
    id = models.AutoField(primary_key=True, db_column='COUNTRY_SEQ')
    name = models.CharField(max_length=35, db_column='COUNTRY_NAME')
    code = models.CharField(max_length=2, db_column='COUNTRY_CODE', blank=True, null=True, help_text=_("2-character Country code"))

    class Meta:
        db_table = 'LU_COUNTRY'
        ordering = ['name']

    def __str__(self):
        return self.name


class Platforms(models.Model):
    id = models.AutoField(primary_key=True, db_column='PLATFORM_SEQ')

    # The description of the platform, for example the name of the vessel, or another
    # meaningful collection method (ie glider) of the data.
    platform = models.CharField(max_length=100, db_column='PLATFORM', help_text=_("Platform name or description"))
    country = models.ForeignKey(Country, related_name="platforms", on_delete=models.CASCADE, blank=True, null=True, db_column='COUNTRY_SEQ')
    call_sign = models.CharField(max_length=10, db_column='CALL_SIGN', blank=True, null=True, help_text=_("Platform call sign, if applicable"))
    max_speed = models.IntegerField(db_column='MAXIMUM_SPEED', blank=True, null=True, help_text=_("Maximum speed of the platform in knots"))
    ices_code = models.CharField(db_column='ICES_CODE', max_length=4, blank=True, null=True, help_text=_("ICES code"))
    ship_code = models.CharField(db_column='SHIP_CODE', max_length=6, blank=True, null=True, help_text=_("OSCruise code"))

    class Meta:
        db_table = 'LU_PLATFORM'
        ordering = ['platform']

    def __str__(self):
        return self.platform


class DataTypes(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255)

    def __str__(self):
        return f'{self.name} - {self.description}'

    class Meta:
        ordering = ['name']


class DataStatus(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255)

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

class GroupProfiles(models.Model):
    group = models.OneToOneField('auth.Group', on_delete=models.CASCADE, related_name='profile')
    description = models.TextField(_("Description"), blank=True, null=True)

    def __str__(self):
        return f"{self.group.name} - {self.description or _('No description')}"


class GeographicRegions(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    description = models.CharField(_('Description'), blank=True, null=True, max_length=255)

    def __str__(self):
        return f'{self.name}'

    def delete(self, *args, **kwargs):
        if self.locations.exists():  # Check if related Cruises exist
            raise ValidationError(_("This region is in use and cannot be deleted."))
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['name']


class Cruises(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, help_text=_("The name of the cruise e.g 'CAR2025002'"))
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    descriptor = models.CharField(verbose_name=_("Descriptor"), max_length=20, blank=True, null=True, help_text=_("MEDS assigned description of the cruise e.g '18QL25002'"))
    chief_scientists = models.ManyToManyField('auth.User', verbose_name=_("Chief Scientists"), related_name='chief_scientists')
    data_managers = models.ManyToManyField('auth.User', verbose_name=_("Data Managers"), related_name='data_managers')
    locations = models.ManyToManyField(GeographicRegions, verbose_name=_("Locations"), blank=True, related_name='locations')
    platform = models.ForeignKey(Platforms, verbose_name=_("Ship/Platform"), on_delete=models.PROTECT, related_name='cruises')

    def __str__(self):
        return f'{self.name} - {self.descriptor}'


class Dataset(models.Model):
    cruise = models.ForeignKey(Cruises, on_delete=models.CASCADE, related_name="datasets")
    data_type = models.ForeignKey(DataTypes, on_delete=models.PROTECT, related_name="datasets")
    legacy_file_location = models.CharField(verbose_name=_("File location"), max_length=255, blank=True, null=True)
    status = models.ForeignKey(DataStatus, verbose_name=_("Process Status"), on_delete=models.PROTECT, related_name="datasets")

    @property
    def current_files(self):
        return self.files.filter(is_archived=False)

    @property
    def archived_files(self):
        return self.files.filter(is_archived=True)

    def __str__(self):
        return f'{self.data_type} : {self.status}'


class DataFiles(models.Model):
    data = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(verbose_name=_("File Name"), max_length=200)
    file = models.FileField(verbose_name=_("File"), max_length=255)
    submitted_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    submitted_date = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(verbose_name=_("Is archived"), default=False)

    def __str__(self):
        return self.file.name

    class Meta:
        ordering = ['file_name']


class DataFileIssues(models.Model):
    datafile = models.ForeignKey(DataFiles, verbose_name=_("Data File"), on_delete=models.CASCADE, related_name='issues')
    issue = models.TextField(verbose_name=_("Issue Description"))
    submitted_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    submitted_date = models.DateTimeField(auto_now_add=True)


class Processing(models.Model):
    dataset = models.ForeignKey(Dataset, verbose_name=_("Dataset"), on_delete=models.CASCADE, related_name='processing')
    assigned_to = models.ForeignKey('auth.User', verbose_name=_("Assigned"), on_delete=models.PROTECT, related_name='processing')
    assigned_date = models.DateTimeField(auto_now=True)
