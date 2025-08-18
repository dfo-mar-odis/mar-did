from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class Programs(models.Model):
    name = models.CharField(_("Program name"), max_length=100, unique=True)
    description = models.TextField(_("Program description"))


class GeographicRegions(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    description = models.CharField(_('Description'), blank=True, null=True, max_length=255)

    def __str__(self):
        return f'{self.name}'

    def delete(self, *args, **kwargs):
        if self.locations.exists():  # Check if related Cruises exist
            raise ValidationError(_("This region is in use and cannot be deleted."))
        super().delete(*args, **kwargs)


class Cruises(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, help_text=_("The name of the cruise e.g 'CAR2025002'"))
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    descriptor = models.CharField(verbose_name=_("Descriptor"), max_length=20, blank=True, null=True, help_text=_("MEDS assigned description of the cruise e.g '18QL25002'"))
    chief_scientists = models.ManyToManyField('auth.User', verbose_name=_("Chief Scientists"), related_name='chief_scientists')
    locations = models.ManyToManyField(GeographicRegions, verbose_name=_("Locations"), blank=True, related_name='locations')

    def __str__(self):
        return f'{self.name} - {self.descriptor}'


class Missions(models.Model):
    program = models.ForeignKey(Programs, on_delete=models.CASCADE, related_name='missions')
    cruise = models.ForeignKey(Cruises, on_delete=models.CASCADE, related_name='missions')


class DataTypes(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255)

    def __str__(self):
        return f'{self.name} - {self.description}'


class DataStatus(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True)
    description = models.CharField(verbose_name=_("Description"), max_length=255)

    def __str__(self):
        return f'{self.name} - {self.description}'


class Instruments(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=20, unique=True)
    serial_number = models.CharField(verbose_name=_("Serial Number"), max_length=255, blank=True, null=True,
                                     help_text=_("Serial number of an instrument if it exists"))
    description = models.CharField(verbose_name=_("Description"), max_length=255)

    def __str__(self):
        return self.name + (f" - {self.description}" if self.description else "" ) + (f" - {self.serial_number}" if self.serial_number else "" )

class MooredInstruments(models.Model):
    descriptor = models.CharField(verbose_name=_("Name"), max_length=20, unique=True,
                                  help_text=_("Serial Number or name given to the moored instrument"))
    instruments = models.ManyToManyField(Instruments, verbose_name=_("Instruments"), blank=True, related_name='moored_instruments')


class Data(models.Model):
    cruise = models.ForeignKey(Cruises, on_delete=models.CASCADE, related_name="mission_data")
    data_type = models.ForeignKey(DataTypes, on_delete=models.PROTECT, related_name="mission_data")
    legacy_file_location = models.CharField(verbose_name=_("File location"), max_length=255)
    file = models.FileField(verbose_name=_("File"))
    instruments = models.ManyToManyField(Instruments, verbose_name=_("Instruments"), blank=True, related_name='mission_data')
    status = models.ForeignKey(DataStatus, verbose_name=_("Process Status"), on_delete=models.PROTECT, related_name="mission_data")