from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Disease, Symptom, Prescription
import random  # Ensure random is imported to avoid UnboundLocalError


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



            ADJECTIVES = [
                'severe', 'mild', 'rapid', 'chronic', 'acute', 'progressive', 'localized', 'systemic',
                'sporadic', 'persistent', 'unusual', 'classic', 'notable', 'distinct', 'widespread', 'patchy',
                'irregular', 'circular', 'elongated', 'diffuse', 'confluent', 'scattered', 'clustered', 'isolated'
            ]
            LOCATIONS = [
                'leaf edges', 'leaf tips', 'lower leaves', 'upper leaves', 'stem', 'petiole', 'veins', 'entire leaf',
                'fruit surface', 'root zone', 'shoot apex', 'flower buds', 'seedlings', 'nodes', 'internodes', 'canopy'
            ]
            ACTIONS = [
                'spots', 'lesions', 'necrosis', 'discoloration', 'chlorosis', 'wilting', 'blight', 'mottling', 'cankers',
                'curling', 'deformation', 'streaks', 'rot', 'softening', 'shriveling', 'abscission', 'browning'
            ]
            TREAT_ACTIONS = [
                'remove infected tissue', 'apply copper-based fungicide', 'apply systemic insecticide', 'increase airflow',
                'reduce overhead watering', 'improve drainage', 'apply neem oil', 'rotate crops', 'use resistant varieties', 'mulch around base',
                'sterilize tools', 'monitor regularly', 'consult local extension', 'adjust fertilization', 'avoid overhead irrigation',
                'apply bactericide', 'use organic amendments', 'solarize soil', 'prune affected branches', 'isolate infected plants'
            ]
            ADVICE = [
                'monitor regularly', 'consult local extension', 'adjust fertilization', 'avoid overhead irrigation',
                'ensure proper spacing', 'sanitize equipment', 'remove debris', 'apply at dawn', 'repeat after rain', 'combine with biological control'
            ]

            for idx, disease in enumerate(all_diseases, start=1):
                plant = disease.name.split()[0]
                pathogen = disease.category

                for s_idx in range(symptoms_per):
                    adjective = random.choice(ADJECTIVES)
                    action = random.choice(ACTIONS)
                    location = random.choice(LOCATIONS)
                    # Compose a maximally unique symptom
                    text = f"{adjective.capitalize()} {action} observed on {location} of {plant} due to {pathogen} ({idx}-{s_idx+1})"
                    symptom_objs.append(Symptom(disease=disease, text=text, order=s_idx))

                for p_idx in range(prescriptions_per):
                    treat_action = random.choice(TREAT_ACTIONS)
                    advice = random.choice(ADVICE)
                    text = f"{treat_action.capitalize()}; {advice} ({idx}-{p_idx+1})"
                    prescription_objs.append(Prescription(disease=disease, text=text, order=p_idx))

            # bulk create in reasonable sized chunks to avoid memory spikes
            BATCH = 10000
            for i in range(0, len(symptom_objs), BATCH):
                Symptom.objects.bulk_create(symptom_objs[i:i+BATCH])
            for i in range(0, len(prescription_objs), BATCH):
                Prescription.objects.bulk_create(prescription_objs[i:i+BATCH])

        self.stdout.write(self.style.SUCCESS(f'Created {count} diseases with related symptoms and prescriptions'))
