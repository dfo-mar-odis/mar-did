import csv
from mardid.models import Country

def load_countries_from_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        print(reader.fieldnames)
        for row in reader:
            # Assuming the CSV has columns 'name' and 'code'
            country, created = Country.objects.get_or_create(
                name=row['Name'],
                defaults={'code': row['Code']}
            )
            if created:
                print(f"Added country: {country.name}")
            else:
                print(f"Country already exists: {country.name}")

# Call the function with the path to the CSV file
load_countries_from_csv('scripts/data/countries.csv')