import random
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Disease, Symptom, Prescription

# Data Pools for Uniqueness
PLANTS = ['Tomato', 'Potato', 'Wheat', 'Corn', 'Rice', 'Soybean', 'Banana', 'Apple', 'Grape', 'Citrus', 'Lettuce', 'Cucumber', 'Pepper', 'Onion', 'Carrot']
PATHOGENS = ['fungus', 'bacterium', 'virus', 'nematode', 'oomycete', 'mite']
ADJECTIVES = ['severe', 'mild', 'rapid', 'chronic', 'acute', 'progressive', 'localized', 'systemic', 'sporadic', 'persistent']
LOCATIONS = ['leaf edges', 'lower leaves', 'upper leaves', 'stem', 'petiole', 'veins', 'fruit surface', 'root zone']
SYMPTOM_TEMPLATES = ['Yellowing of leaves', 'Brown spots', 'Wilting', 'Stunted growth', 'Powdery coating', 'Lesions', 'Leaf curling', 'Dark streaks', 'Root rot', 'General chlorosis']
TREAT_ACTIONS = ['Remove infected tissue', 'Apply copper-based fungicide', 'Increase airflow', 'Reduce overhead watering', 'Improve drainage', 'Apply neem oil', 'Rotate crops', 'Sterilize tools']
ADVICE = ['monitor regularly', 'consult local extension', 'adjust fertilization', 'avoid overhead irrigation', 'ensure proper spacing']

class Command(BaseCommand):
    help = 'Populate the database with 2000 unique plant diseases'

    def add_arguments(self, parser):
        # This tells Django to look for these flags in the terminal
        parser.add_argument('--count', type=int, default=2000, help='Number of diseases to create')
        parser.add_argument('--symptoms', type=int, default=5, help='Symptoms per disease')
        parser.add_argument('--prescriptions', type=int, default=5, help='Prescriptions per disease')

    def handle(self, *args, **options):
        count = options['count']
        symptoms_per = options['symptoms']
        prescriptions_per = options['prescriptions']

        self.stdout.write(self.style.NOTICE(f'Generating {count} unique diseases...'))

        with transaction.atomic():
            # 1. Clean old data
            Prescription.objects.all().delete()
            Symptom.objects.all().delete()
            Disease.objects.all().delete()

            # 2. Build Diseases
            diseases = []
            for i in range(1, count + 1):
                plant = random.choice(PLANTS)
                pathogen = random.choice(PATHOGENS)
                name = f"{plant} {pathogen.capitalize()} Strain-{random.randint(100, 999)}-{i:04d}"
                description = f"A unique variant of {pathogen} affecting {plant} crops, identified as case #{i}."
                diseases.append(Disease(name=name, description=description, category=pathogen))

            Disease.objects.bulk_create(diseases)
            all_diseases = list(Disease.objects.all())

            # 3. Build Symptoms and Prescriptions
            symptom_objs = []
            prescription_objs = []

            for disease in all_diseases:
                # Get random selection from templates to avoid "everyone gets the same 10"
                current_symptoms = random.sample(SYMPTOM_TEMPLATES, min(len(SYMPTOM_TEMPLATES), symptoms_per))
                for s_idx, template in enumerate(current_symptoms):
                    text = f"{random.choice(ADJECTIVES).capitalize()} {template.lower()} on the {random.choice(LOCATIONS)}."
                    symptom_objs.append(Symptom(disease=disease, text=text, order=s_idx))

                current_treats = random.sample(TREAT_ACTIONS, min(len(TREAT_ACTIONS), prescriptions_per))
                for p_idx, action in enumerate(current_treats):
                    text = f"{action}; {random.choice(ADVICE)}."
                    prescription_objs.append(Prescription(disease=disease, text=text, order=p_idx))

            # 4. Bulk Save
            BATCH = 5000
            for i in range(0, len(symptom_objs), BATCH):
                Symptom.objects.bulk_create(symptom_objs[i:i+BATCH])
            for i in range(0, len(prescription_objs), BATCH):
                Prescription.objects.bulk_create(prescription_objs[i:i+BATCH])

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} unique records!'))