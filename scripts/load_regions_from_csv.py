import csv

from core.models import GeographicRegions


def load_regions_from_csv(file_path):
    GeographicRegions.objects.all().delete()

    bulk_create_list = []
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=',')
        print(reader.fieldnames)
        for row, data in enumerate(reader):
            print(data)
            # Assuming the CSV has columns 'name' and 'code'
            element = GeographicRegions(
                id=row+1,
                name=data['name']
            )
            element.description = data['description'] if 'description' in data and data['description'] else None

            bulk_create_list.append(element)

            if len(bulk_create_list) > 1000:
                GeographicRegions.objects.bulk_create(bulk_create_list)
                bulk_create_list = []

    GeographicRegions.objects.bulk_create(bulk_create_list)


# Call the function with the path to the CSV file
load_regions_from_csv('scripts/data/import_for_LU_GEOGRAPHIC_REGION.csv')