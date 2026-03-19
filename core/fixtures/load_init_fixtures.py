from django.core.management import call_command


fixture_list = [ 'init_group_fixtures', 'init_dataset_status', 'init_countries',
                  'init_organizations', 'init_platforms', 'init_regions', 'init_programs' ]


call_command("loaddata", *fixture_list)
