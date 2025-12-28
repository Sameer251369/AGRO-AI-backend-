from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Disease, Symptom, Prescription
import random


PLANTS = [
    'Tomato', 'Potato', 'Wheat', 'Corn', 'Rice', 'Soybean', 'Banana', 'Apple',
    'Grape', 'Citrus', 'Lettuce', 'Cucumber', 'Pepper', 'Onion', 'Carrot'
]

PATHOGENS = [
    'fungus', 'bacterium', 'virus', 'nematode', 'oomycete', 'mite'
]

SYMPTOM_TEMPLATES = [
    'Yellowing of leaves in the upper canopy',
    'Brown spots with concentric rings',
    'Wilting during the hottest part of the day',
    'Stunted growth and small new leaves',
    'Powdery white coating on leaf surfaces',
    'Lesions on stems near soil line',
    'Leaf curling and deformation',
    'Dark streaks on fruit skin',
    'Root rot and soft roots',
    'General chlorosis and poor vigor',
]

TREATMENT_TEMPLATES = [
    'Remove and destroy affected plant parts',
    'Apply an appropriate registered fungicide following label rates',
    'Rotate to non-host crops for one season',
    'Use certified disease-free transplants',
    'Improve drainage and avoid overwatering',
    'Practise good sanitation and tool hygiene',
    'Apply an appropriate bactericide where labelled',
    'Incorporate organic matter to improve soil structure',
    'Use resistant varieties when available',
    'Maintain recommended fertilization to reduce stress',
]


class Command(BaseCommand):
    help = 'Populate the database with synthetic, realistic-looking plant diseases (optionally large)'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=2000, help='Number of diseases to create')
        parser.add_argument('--symptoms', type=int, default=10, help='Symptoms per disease')
        parser.add_argument('--prescriptions', type=int, default=10, help='Prescriptions/treatments per disease')

    def handle(self, *args, **options):
        count = options['count']
        symptoms_per = options['symptoms']
        prescriptions_per = options['prescriptions']

        self.stdout.write(f'Populating {count} diseases with {symptoms_per} symptoms and {prescriptions_per} prescriptions each')

        with transaction.atomic():
            # Delete existing
            Prescription.objects.all().delete()
            Symptom.objects.all().delete()
            Disease.objects.all().delete()

            diseases = []
            for i in range(1, count + 1):
                plant = random.choice(PLANTS)
                pathogen = random.choice(PATHOGENS)
                name = f'{plant} {pathogen.capitalize()} Disease {i:05d}'
                description = f'A {pathogen}-related disease affecting {plant} with characteristic symptoms of {pathogen} infection.'
                category = pathogen
                diseases.append(Disease(name=name, description=description, category=category))

            Disease.objects.bulk_create(diseases)

            # Create related symptoms and prescriptions in bulk
            all_diseases = list(Disease.objects.all())
            symptom_objs = []
            prescription_objs = []

            for idx, disease in enumerate(all_diseases, start=1):
                # deterministic-ish selection of templates
                for s_idx in range(symptoms_per):
                    template = SYMPTOM_TEMPLATES[(s_idx) % len(SYMPTOM_TEMPLATES)]
                    text = f"{template} (example {s_idx+1})"
                    symptom_objs.append(Symptom(disease=disease, text=text, order=s_idx))

                for p_idx in range(prescriptions_per):
                    template = TREATMENT_TEMPLATES[(p_idx) % len(TREATMENT_TEMPLATES)]
                    text = f"{template} (recommendation {p_idx+1})"
                    prescription_objs.append(Prescription(disease=disease, text=text, order=p_idx))

            # bulk create in reasonable sized chunks to avoid memory spikes
            BATCH = 10000
            for i in range(0, len(symptom_objs), BATCH):
                Symptom.objects.bulk_create(symptom_objs[i:i+BATCH])
            for i in range(0, len(prescription_objs), BATCH):
                Prescription.objects.bulk_create(prescription_objs[i:i+BATCH])

        self.stdout.write(self.style.SUCCESS(f'Created {count} diseases with related symptoms and prescriptions'))
