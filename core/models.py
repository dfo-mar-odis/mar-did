from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class Platforms(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=200, unique=True)
    ship_code = models.CharField(verbose_name=_("Ship Code"), max_length=4, null=True, help_text=_("ICES (https://vocab.ices.dk/) code consists of 2 character country code and a 2 character ship code for every unique vessel."))

    def __str__(self):
        return f'{self.name}'

    class Meta:
        ordering = ['name']


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


class Programs(models.Model):
    name = models.CharField(_("Program name"), max_length=100, unique=True)
    description = models.TextField(_("Program description"))

    def __str__(self):
        return f'{self.name} - {self.description}'

    class Meta:
        ordering = ['name']


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
    programs = models.ManyToManyField(Programs, verbose_name=_("programs"), related_name='programs')
    platform = models.ForeignKey(Platforms, verbose_name=_("Ship/Platform"), on_delete=models.PROTECT, related_name='cruises')

    def __str__(self):
        return f'{self.name} - {self.descriptor}'


class Instruments(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20)
    serial_number = models.CharField(verbose_name=_("Serial Number"), max_length=255, blank=True, null=True,
                                     help_text=_("Serial number of an instrument if it exists"), unique=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255)

    def __str__(self):
        return self.name + (f" - {self.description}" if self.description else "" ) + (f" - {self.serial_number}" if self.serial_number else "" )

    class Meta:
        ordering = ['name', 'serial_number']


class MooredInstruments(models.Model):
    descriptor = models.CharField(verbose_name=_("Name"), max_length=20, unique=True,
                                  help_text=_("Serial Number or name given to the moored instrument"))
    instruments = models.ManyToManyField(Instruments, verbose_name=_("Instruments"), blank=True, related_name='moored_instruments')


class Dataset(models.Model):
    cruise = models.ForeignKey(Cruises, on_delete=models.CASCADE, related_name="datasets")
    data_type = models.ForeignKey(DataTypes, on_delete=models.PROTECT, related_name="datasets")
    legacy_file_location = models.CharField(verbose_name=_("File location"), max_length=255, blank=True, null=True)
    instruments = models.ManyToManyField(Instruments, verbose_name=_("Instruments"), blank=True, related_name='instruments')
    status = models.ForeignKey(DataStatus, verbose_name=_("Process Status"), on_delete=models.PROTECT, related_name="datasets")

    def __str__(self):
        return f'{self.data_type} : {self.status}'


class DataFiles(models.Model):
    data = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='files')
    file_name = models.CharField(verbose_name=_("File Name"), max_length=100)
    file = models.FileField(verbose_name=_("File"))
    submitted_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    submitted_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name


class DataFileIssues(models.Model):
    datafile = models.ForeignKey(DataFiles, verbose_name=_("Data File"), on_delete=models.CASCADE, related_name='issues')
    issue = models.TextField(verbose_name=_("Issue Description"))
    submitted_by = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    submitted_date = models.DateTimeField(auto_now=True)


class Processing(models.Model):
    dataset = models.OneToOneField(Dataset, verbose_name=_("Dataset"), on_delete=models.CASCADE, related_name='processing')
    assigned_to = models.ForeignKey('auth.User', verbose_name=_("Assigned"), on_delete=models.PROTECT, related_name='processing')
    assigned_date = models.DateTimeField(auto_now=True)
