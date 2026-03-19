import csv

from core.models import Organizations, Countries


def load_organizations_from_csv(file_path):
    Organizations.objects.all().delete()

    bulk_create_list = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=',')
        print(reader.fieldnames)
        for row, data in enumerate(reader):
            print(data)
            # Assuming the CSV has columns 'name' and 'code'
            element = Organizations(
                id=row+1,
                name=data['name']
            )
            element.acronym = data['acronym'] if 'acronym' in data and data['acronym'] else None
            element.code = data['code'] if 'code' in data and data['code'] else None
            element.description = data['description'] if 'description' in data and data['description'] else None
            element.country = Countries.objects.get(name__iexact=data['country_code']) if 'country_code' in data and data['country_code'] else Countries.objects.get(name__iexact='unknown')

            bulk_create_list.append(element)

            if len(bulk_create_list) > 1000:
                Organizations.objects.bulk_create(bulk_create_list)
                bulk_create_list = []

    Organizations.objects.bulk_create(bulk_create_list)


# Call the function with the path to the CSV file
load_organizations_from_csv('scripts/data/import_for_LU_ORGANIZATION.csv')