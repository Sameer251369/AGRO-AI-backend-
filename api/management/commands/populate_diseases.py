import random
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Disease, Symptom, Prescription

class Command(BaseCommand):
    help = 'Populate the database with unique plant diseases'

    def add_arguments(self, parser):
        # Using optional argument syntax with '--'
        parser.add_argument('--count', type=int, default=2000, help='Number of diseases to create')
        parser.add_argument('--symptoms', type=int, default=10, help='Symptoms per disease')
        parser.add_argument('--prescriptions', type=int, default=10, help='Treatments per disease')

    def handle(self, *args, **options):
        # Accessing the arguments from the options dictionary
        count = options['count']
        symptoms_per = options['symptoms']
        prescriptions_per = options['prescriptions']

        self.stdout.write(self.style.NOTICE(f'Starting population of {count} diseases...'))

        PLANTS = ['Tomato', 'Potato', 'Wheat', 'Corn', 'Rice', 'Soybean', 'Banana', 'Apple', 'Grape', 'Citrus']
        PATHOGENS = ['fungus', 'bacterium', 'virus', 'nematode', 'oomycete', 'mite']
        
        # ... (Your template lists here) ...

        with transaction.atomic():
            # 1. Clear existing data
            Prescription.objects.all().delete()
            Symptom.objects.all().delete()
            Disease.objects.all().delete()

            # 2. Bulk Create Diseases
            disease_list = []
            for i in range(1, count + 1):
                plant = random.choice(PLANTS)
                pathogen = random.choice(PATHOGENS)
                name = f"{plant} {pathogen.capitalize()} Disease {i:05d}"
                disease_list.append(Disease(
                    name=name,
                    description=f"Unique {pathogen} infection targeting {plant} variety #{i}.",
                    category=pathogen
                ))
            
            Disease.objects.bulk_create(disease_list)
            all_diseases = list(Disease.objects.all())

            # 3. Create Related Data
            symptom_objs = []
            prescription_objs = []

            for disease in all_diseases:
                for s_idx in range(symptoms_per):
                    text = f"Visible {disease.category} spot detected on {disease.name} sample {s_idx}"
                    symptom_objs.append(Symptom(disease=disease, text=text, order=s_idx))
                
                for p_idx in range(prescriptions_per):
                    text = f"Treatment protocol {p_idx} for {disease.name}"
                    prescription_objs.append(Prescription(disease=disease, text=text, order=p_idx))

            # Batch create for performance
            Symptom.objects.bulk_create(symptom_objs, batch_size=5000)
            Prescription.objects.bulk_create(prescription_objs, batch_size=5000)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} unique diseases!'))