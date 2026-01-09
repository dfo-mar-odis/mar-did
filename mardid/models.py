from django.db import models
from django.utils.translation import gettext_lazy as _

############################################################################################
## Lookup Tables
############################################################################################

# MEDS uses a list of country codes that I think are from ICES
# https://www.ncbi.nlm.nih.gov/books/NBK7249/table/appd.T1/ dumped to mardid/fixtures/meds_country_codes.json
class Country(models.Model):
    id = models.AutoField(primary_key=True, db_column='COUNTRY_SEQ')
    name = models.CharField(max_length=35, db_column='COUNTRY_NAME')

    class Meta:
        db_table = 'LU_COUNTRY'
        ordering = ['name']

    def __str__(self):
        return self.name


class Platform(models.Model):
    id = models.AutoField(primary_key=True, db_column='PLATFORM_SEQ')

    # The description of the platform, for example the name of the vessel, or another
    # meaningful collection method (ie glider) of the data.
    platform = models.CharField(max_length=100, db_column='PLATFORM', help_text=_("Platform name or description"))
    country = models.ForeignKey(Country, related_name="platforms", on_delete=models.CASCADE, blank=True, null=True, db_column='COUNTRY_SEQ')
    call_sign = models.CharField(max_length=10, db_column='CALL_SIGN', blank=True, null=True, help_text=_("Platform call sign, if applicable"))
    max_speed = models.IntegerField(max_length=3, db_column='MAXIMUM_SPEED', blank=True, null=True, help_text=_("Maximum speed of the platform in knots"))

    class Meta:
        db_table = 'LU_PLATFORM'
        ordering = ['platform']

    def __str__(self):
        return self.platform


class GeographicRegion(models.Model):
    id = models.AutoField(primary_key=True, db_column='GEOGRAPHIC_SEQ')
    name = models.CharField(max_length=40, db_column='GEOGRAPHIC_NAME')

    class Meta:
        db_table = 'LU_GEOGRAPHIC_REGION'
        ordering = ['name']

    def __str__(self):
        return self.name


class Institute(models.Model):
    id = models.AutoField(primary_key=True, db_column='INSTITUTE_SEQ')
    name = models.CharField(max_length=50, db_column='INSTITUTE_NAME')

    class Meta:
        db_table = 'LU_INSTITUTE'
        ordering = ['name']

    def __str__(self):
        return self.name


class Program(models.Model):
    id = models.AutoField(primary_key=True, db_column='PROGRAM_SEQ')
    name = models.CharField(max_length=50, db_column='PROGRAM_NAME')
    description = models.CharField(max_length=250, db_column='PROGRAM_DESCRIPTION')

    class Meta:
        db_table = 'LU_PROGRAM'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class Project(models.Model):
    id = models.AutoField(primary_key=True, db_column='PROJECT_SEQ')
    name = models.CharField(max_length=100, db_column='PROJECT_NAME')
    description = models.CharField(max_length=250, db_column='PROJECT_DESCRIPTION')

    class Meta:
        db_table = 'LU_PROJECT'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class EquipmentType(models.Model):
    id = models.AutoField(primary_key=True, db_column='EQUIPMENT_TYPE_SEQ')
    type = models.CharField(max_length=35, db_column='EQUIPMENT_TYPE')

    class Meta:
        db_table = 'LU_EQUIPMENT_TYPE'
        ordering = ['type']

    def __str__(self):
        return f"{self.type}"


class ParameterType(models.Model):
    id = models.AutoField(primary_key=True, db_column='PARAMETER_TYPE_SEQ')
    type = models.CharField(max_length=25, db_column='PARAMETER_TYPE')
    units = models.CharField(max_length=50, db_column='PARAMETER_UNITS')

    class Meta:
        db_table = 'LU_PARAMETER_TYPE'
        ordering = ['type']

    def __str__(self):
        return f"{self.type} - {self.units}"


class InstrumentType(models.Model):
    id = models.AutoField(primary_key=True, db_column='INSTRUMENT_TYPE_SEQ')
    type = models.CharField(max_length=35, db_column='INSTRUMENT_TYPE')

    class Meta:
        db_table = 'LU_INSTRUMENT_TYPE'
        ordering = ['type']

    def __str__(self):
        return f"{self.type}"


class ProcessingState(models.Model):
    id = models.AutoField(primary_key=True, db_column='PROCESSING_STATE_SEQ')
    name = models.CharField(max_length=25, db_column='PROCESSING_STATE_NAME')
    description = models.CharField(max_length=100, db_column='PROCESSING_STATE_DESCRIPTION')

    class Meta:
        db_table = 'LU_PROCESSING_STATE'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class Organization(models.Model):
    id = models.AutoField(primary_key=True, db_column='ORGANIZATION_SEQ')
    name = models.CharField(max_length=100, db_column='ORGANIZATION_NAME')
    description = models.CharField(max_length=250, db_column='ORGANIZATION_DESCRIPTION')

    class Meta:
        db_table = 'LU_ORGANIZATION'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class Division(models.Model):
    id = models.AutoField(primary_key=True, db_column='DIVISION_SEQ')
    name = models.CharField(max_length=100, db_column='DIVISION_NAME')

    class Meta:
        db_table = 'LU_DIVISION'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


## Todo: This model needs a better description of what it's supposed to do
class FolderPath(models.Model):
    id = models.AutoField(primary_key=True, db_column='FOLDER_PATH_SEQ')
    path = models.CharField(max_length=10, db_column='FOLDER_PATH_STRING')

    class Meta:
        db_table = 'LU_FOLDER_PATH'
        ordering = ['path']

    def __str__(self):
        return f"{self.path}"


class FileType(models.Model):
    id = models.AutoField(primary_key=True, db_column='FILE_TYPE_SEQ')
    type = models.CharField(max_length=25, db_column='FILE_TYPE_NAME')
    description = models.CharField(max_length=100, db_column='FILE_TYPE_DESCRIPTION')

    class Meta:
        db_table = 'LU_FILE_TYPE'
        ordering = ['type']

    def __str__(self):
        return f"{self.type} - {self.description}"


class GroupRole(models.Model):
    id = models.AutoField(primary_key=True, db_column='ROLE_SEQ')
    name = models.CharField(max_length=25, db_column='ROLE_NAME')
    description = models.CharField(max_length=50, db_column='ROLE_DESCRIPTION')

    class Meta:
        db_table = 'LU_ROLE'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.description}"


class Contact(models.Model):
    id = models.AutoField(primary_key=True, db_column='CONTACT_SEQ')
    last_name = models.CharField(max_length=50, db_column='LAST_NAME')
    first_name = models.CharField(max_length=50, db_column='FIRST_NAME')

    class Meta:
        db_table = 'LU_CONTACT'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


############################################################################################
## Data Tables
############################################################################################

class MissionMetadata(models.Model):
    id = models.AutoField(primary_key=True, db_column='MISSION_METADATA_SEQ')

    start_date = models.DateField(db_column='START_DATE')
    end_date = models.DateField(db_column='END_DATE')

    class Meta:
        db_table = 'MISSION_METADATA'


############################################################################################
## Many-to-many Tables
############################################################################################

class MissionRegion(models.Model):
    mission = models.ForeignKey(MissionMetadata, related_name="mission_regions", on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    geographic_region = models.ForeignKey(GeographicRegion, related_name="mission_regions", on_delete=models.CASCADE, db_column='GEOGRAPHIC_SEQ')

    class Meta:
        db_table = 'LU_MISSION_REGION'
        ordering = ['mission__start_date']

    def __str__(self):
        return f"{self.mission} - {self.geographic_region}"
