from django.db import models
from django.db.models.fields import TextField
from django.utils.translation import gettext_lazy as _

############################################################################################
## Lookup Tables
############################################################################################

# MEDS uses a list of country codes that I think are from ICES
# https://www.ncbi.nlm.nih.gov/books/NBK7249/table/appd.T1/ dumped to mardid/fixtures/meds_country_codes.json
class Country(models.Model):
    id = models.AutoField(primary_key=True, db_column='COUNTRY_SEQ')
    name = models.CharField(max_length=35, db_column='COUNTRY_NAME')
    code = models.CharField(max_length=2, db_column='COUNTRY_CODE', blank=True, null=True, help_text=_("2-character Country code"))

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
    max_speed = models.IntegerField(db_column='MAXIMUM_SPEED', blank=True, null=True, help_text=_("Maximum speed of the platform in knots"))
    ices_code = models.CharField(db_column='ICES_CODE', max_length=4, blank=True, null=True, help_text=_("ICES code"))
    ship_code = models.CharField(db_column='SHIP_CODE', max_length=6, blank=True, null=True, help_text=_("OSCruise code"))

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
    mission_name = models.CharField(max_length=25, db_column='MISSION_NAME')
    platform = models.ForeignKey(Platform, related_name='mission_metadata', on_delete=models.CASCADE, db_column='PLATFORM_SEQ')
    nodc_descriptor = models.CharField(max_length=15, db_column='NODC_DESCRIPTOR', blank=True, null=True)
    start_date = models.DateField(db_column='START_DATE', blank=True, null=True)
    end_date = models.DateField(db_column='END_DATE', blank=True, null=True)
    program = models.ForeignKey(Program, related_name='mission_metadata', on_delete=models.CASCADE, db_column='PROGRAM_SEQ')
    institute = models.ForeignKey(Institute, related_name='mission_metadata', on_delete=models.CASCADE, db_column='INSTITUTE_SEQ')
    project_planning_tool_id = models.IntegerField(db_column='PPT_ID', blank=True, null=True)
    participant = models.ForeignKey("MissionParticipant", related_name='mission_metadata', on_delete=models.CASCADE, db_column='PARTICIPANT_SEQ')

    class Meta:
        db_table = 'MISSION_METADATA'


class Equipment(models.Model):
    id = models.AutoField(primary_key=True, db_column='EQUIPMENT_SEQ')
    equipment_type = models.ForeignKey(InstrumentType, related_name='equipment', on_delete=models.CASCADE, db_column='EQUIPMENT_TYPE')
    equipment_number = models.CharField(max_length=25, blank=True, null=True, db_column='EQUIPMENT_NUMBER')
    serial_number = models.CharField(max_length=50, blank=True, null=True, db_column='SERIAL_NUMBER')
    metadata = models.ForeignKey(MissionMetadata, related_name='equipment', on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    deployment_date = models.DateField(db_column='DEPLOYMENT_DATE')
    recovery_date = models.DateField(db_column='RECOVERY_DATE')
    start_lat = models.FloatField(db_column='START_LATITUDE', blank=True, null=True)
    start_lon = models.FloatField(db_column='START_LONGITUDE', blank=True, null=True)
    end_lat = models.FloatField(db_column='END_LATITUDE', blank=True, null=True)
    end_lon = models.FloatField(db_column='END_LONGITUDE', blank=True, null=True)
    date_entered = models.DateField(db_column='DATE_ENTERED')
    entered_by = models.ForeignKey(Contact, related_name='equipment', on_delete=models.CASCADE, db_column='ENTERED_BY')
    recovery_metadata = models.ForeignKey(MissionMetadata, related_name='equipment_recoveries', blank=True, null=True, on_delete=models.CASCADE, db_column='RECOVERY_MISSION_METADATA_SEQ')

    class Meta:
        db_table = 'EQUIPMENT'


class DataCollected(models.Model):
    id = models.AutoField(primary_key=True, db_column='DATA_COLLECTED_SEQ')
    equipment = models.ForeignKey(Equipment, related_name='data_collected', on_delete=models.CASCADE, db_column='EQUIPMENT_SEQ')
    instrument_type = models.ForeignKey(InstrumentType, related_name='data_collected', on_delete=models.CASCADE, db_column='INSTRUMENT_TYPE_SEQ')
    principal_investigator = models.ForeignKey(Contact, related_name='data_collected_pis', on_delete=models.CASCADE, db_column='PI_SEQ')
    parameter_type = models.ForeignKey(ParameterType, related_name='data_collected', on_delete=models.CASCADE, db_column='PARAMETER_TYPE_SEQ')
    serial_number = models.CharField(max_length=35, db_column='SERIAL_NUMBER', blank=True, null=True)
    data_processor = models.ForeignKey(Contact, related_name='data_collected_processors', on_delete=models.CASCADE, db_column='DATA_PROCESSOR_SEQ')
    processing_state = models.ForeignKey(ProcessingState, related_name='data_collected', on_delete=models.CASCADE, db_column='PROCESSING_STATE_SEQ')
    date_entered = models.DateField(db_column='DATE_ENTERED')
    entered_by = models.ForeignKey(Contact, related_name='data_collected', on_delete=models.CASCADE, db_column='ENTERED_BY')
    date_received = models.DateField(db_column='DATE_RECEIVED')
    loaded_to_odf_archive = models.BooleanField(default=False, db_column='LOADED_TO_ODF_ARCHIVE')
    sent_to_meds = models.BooleanField(default=False, db_column='SENT_TO_MEDS')
    organization = models.ForeignKey(Organization, related_name='data_collected', on_delete=models.CASCADE, db_column='ORGANIZATION_SEQ')
    division = models.ForeignKey(Division, related_name='data_collected', on_delete=models.CASCADE, db_column='DIVISION_SEQ', blank=True, null=True)

    folder_path = models.ForeignKey(FolderPath, related_name="files", on_delete=models.CASCADE, db_column='FOLDER_PATH_SEQ')
    relative_path = models.CharField(max_length=200, db_column='RELATIVE_PATH')

    class Meta:
        db_table = 'DATA_COLLECTED'

class File(models.Model):
    id = models.AutoField(primary_key=True, db_column='FILE_SEQ')
    metadata = models.ForeignKey(MissionMetadata, related_name="files", on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    data_collected = models.ForeignKey(DataCollected, related_name="files", on_delete=models.CASCADE, db_column='DATA_COLLECTED_SEQ')
    file_type = models.ForeignKey(FileType, related_name="files", on_delete=models.CASCADE, db_column='FILE_TYPE_SEQ')
    file_name = models.CharField(max_length=200, db_column='FILE_NAME')
    date_submitted = models.DateField(db_column='DATE_SUBMITTED')
    submitted_by = models.ForeignKey(Contact, related_name="files", on_delete=models.CASCADE, db_column='SUBMITTED_BY_SEQ')

    class Meta:
        db_table = 'FILE'


############################################################################################
## Many-to-many Tables
############################################################################################

class MissionRegion(models.Model):
    mission = models.ForeignKey(MissionMetadata, related_name="mission_regions", on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    geographic_region = models.ForeignKey(GeographicRegion, related_name="mission_regions", on_delete=models.CASCADE, db_column='GEOGRAPHIC_SEQ')

    class Meta:
        db_table = 'MISSION_REGION'
        ordering = ['mission__start_date']

    def __str__(self):
        return f"{self.mission} - {self.geographic_region}"


class MissionParticipant(models.Model):
    id = models.AutoField(primary_key=True, db_column='PARTICIPANT_SEQ')
    role = models.ForeignKey(GroupRole, db_column='ROLE_SEQ', on_delete=models.CASCADE, related_name='mission_participants')
    contact = models.ForeignKey(Contact, db_column='CONTACT_SEQ', on_delete=models.CASCADE, related_name='mission_participant')

    class Meta:
        db_table = 'MISSION_PARTICIPANT'


class FileComment(models.Model):
    id = models.AutoField(primary_key=True, db_column='FILE_COMMENT_SEQ')
    author = models.ForeignKey(Contact, related_name="file_comments", on_delete=models.CASCADE, db_column='AUTHOR_SEQ')
    file = models.ForeignKey(File, related_name="file_comments", on_delete=models.CASCADE, db_column='FILE_SEQ')
    comment = TextField(db_column='COMMENT')
    date = models.DateField(db_column='FILE_COMMENT_DATE')

    class Meta:
        db_table = 'FILE_COMMENT'
        ordering = ['date']


class MissionComment(models.Model):
    id = models.AutoField(primary_key=True, db_column='MISSION_COMMENT_SEQ')
    mission_comment = models.TextField(db_column='MISSION_COMMENT')
    author = models.ForeignKey(Contact, related_name="mission_comments", on_delete=models.CASCADE, db_column='AUTHOR_SEQ')
    metadata = models.ForeignKey(MissionMetadata, related_name='mission_comments', on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    comment_date = models.DateField(db_column='MISSION_COMMENT_DATE')

    class Meta:
        db_table = 'MISSION_COMMENT'


class EquipmentProject(models.Model):
    id = models.AutoField(primary_key=True, db_column='EQUIPMENT_PROJECT_SEQ')
    equipment = models.ForeignKey(Equipment, related_name="equipment_projects", on_delete=models.CASCADE, db_column='EQUIPMENT_SEQ')
    metadata = models.ForeignKey(MissionMetadata, related_name="equipment_projects", on_delete=models.CASCADE, db_column='MISSION_METADATA_SEQ')
    project = models.ForeignKey(Project, related_name="equipment_projects", on_delete=models.CASCADE, db_column='PROJECT_SEQ')

    class Meta:
        db_table = 'EQUIPMENT_PROJECT'
