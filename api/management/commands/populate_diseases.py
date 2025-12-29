"""
Management command to populate database with diverse plant diseases.
Usage: python manage.py populate_diseases --count 2000
"""
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Disease, Symptom, Prescription

# Comprehensive data pools for variety
PLANTS = [
    'Tomato', 'Potato', 'Wheat', 'Corn', 'Rice', 'Soybean', 'Banana', 
    'Apple', 'Grape', 'Citrus', 'Lettuce', 'Cucumber', 'Pepper', 
    'Onion', 'Carrot', 'Cotton', 'Coffee', 'Tea', 'Mango', 'Strawberry',
    'Blueberry', 'Peach', 'Cherry', 'Pear', 'Plum', 'Watermelon',
    'Cantaloupe', 'Spinach', 'Cabbage', 'Broccoli', 'Cauliflower'
]

PATHOGENS = [
    'fungus', 'bacteria', 'virus', 'nematode', 'oomycete', 
    'phytoplasma', 'mite', 'aphid'
]

DISEASE_TYPES = [
    'Blight', 'Rot', 'Wilt', 'Spot', 'Rust', 'Mildew', 'Scab', 
    'Canker', 'Mosaic', 'Curl', 'Mottle', 'Streak', 'Smut', 
    'Mold', 'Gall', 'Chlorosis'
]

LOCATIONS = [
    'leaf edges', 'lower leaves', 'upper leaves', 'stem base', 
    'petioles', 'leaf veins', 'fruit surface', 'root system',
    'flower buds', 'young shoots', 'leaf tips', 'branch tips'
]

SYMPTOM_DESCRIPTORS = [
    'Yellowing', 'Browning', 'Wilting', 'Curling', 'Spotting',
    'Lesions', 'Necrosis', 'Chlorosis', 'Stunting', 'Distortion',
    'Streaking', 'Mottling', 'Powdery coating', 'Dark patches',
    'Water-soaked areas', 'Concentric rings', 'Irregular margins'
]

TREATMENT_ACTIONS = [
    'Remove and destroy infected plant material',
    'Apply copper-based fungicide',
    'Apply systemic fungicide',
    'Improve air circulation around plants',
    'Reduce overhead watering',
    'Water at soil level only',
    'Improve soil drainage',
    'Apply neem oil spray',
    'Use biological control agents',
    'Implement crop rotation',
    'Sterilize all garden tools',
    'Apply horticultural oil',
    'Remove weeds that harbor pests',
    'Apply sulfur-based treatment',
    'Prune affected branches',
    'Adjust fertilization schedule',
    'Mulch to prevent soil splash'
]

PREVENTION_TIPS = [
    'Plant resistant varieties when available',
    'Maintain proper plant spacing for air flow',
    'Avoid working with plants when wet',
    'Monitor plants regularly for early signs',
    'Use drip irrigation instead of overhead',
    'Remove plant debris promptly',
    'Practice crop rotation annually',
    'Disinfect tools between uses',
    'Avoid excess nitrogen fertilization',
    'Ensure adequate sunlight exposure',
    'Test and maintain proper soil pH'
]


class Command(BaseCommand):
    help = 'Populate database with diverse, realistic plant diseases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', 
            type=int, 
            default=2000, 
            help='Number of diseases to create'
        )
        parser.add_argument(
            '--symptoms', 
            type=int, 
            default=8, 
            help='Symptoms per disease (will vary slightly)'
        )
        parser.add_argument(
            '--treatments', 
            type=int, 
            default=7, 
            help='Treatments per disease (will vary slightly)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )

    def handle(self, *args, **options):
        count = options['count']
        avg_symptoms = options['symptoms']
        avg_treatments = options['treatments']
        clear_data = options['clear']

        self.stdout.write(
            self.style.NOTICE(f'Starting database population...')
        )

        with transaction.atomic():
            # Clear existing data if requested
            if clear_data:
                self.stdout.write('Clearing existing data...')
                Prescription.objects.all().delete()
                Symptom.objects.all().delete()
                Disease.objects.all().delete()

            # Generate diverse disease records
            diseases = []
            for i in range(1, count + 1):
                plant = random.choice(PLANTS)
                pathogen = random.choice(PATHOGENS)
                disease_type = random.choice(DISEASE_TYPES)
                
                # Create varied disease names
                if i % 3 == 0:
                    name = f"{plant} {disease_type}"
                elif i % 3 == 1:
                    name = f"{plant} {pathogen.capitalize()} {disease_type}"
                else:
                    name = f"{disease_type} of {plant}"
                
                # Add strain/variant identifier for uniqueness
                if i % 5 == 0:
                    name += f" Strain-{random.randint(100, 999)}"
                elif i % 7 == 0:
                    name += f" Type-{chr(65 + (i % 26))}"
                
                description = self._generate_description(
                    plant, pathogen, disease_type
                )
                
                diseases.append(Disease(
                    name=name,
                    description=description,
                    category=pathogen
                ))

            # Bulk create diseases
            self.stdout.write('Creating disease records...')
            Disease.objects.bulk_create(diseases, batch_size=1000)
            all_diseases = list(Disease.objects.all())
            
            self.stdout.write(
                self.style.SUCCESS(f'Created {len(all_diseases)} diseases')
            )

            # Generate symptoms and treatments
            self.stdout.write('Generating symptoms and treatments...')
            symptom_objs = []
            prescription_objs = []

            for disease in all_diseases:
                # Vary the number of symptoms/treatments per disease
                num_symptoms = avg_symptoms + random.randint(-2, 2)
                num_symptoms = max(3, min(12, num_symptoms))
                
                num_treatments = avg_treatments + random.randint(-2, 2)
                num_treatments = max(3, min(10, num_treatments))
                
                # Generate unique symptoms
                used_symptoms = set()
                for s_idx in range(num_symptoms):
                    symptom_text = self._generate_symptom()
                    
                    # Ensure uniqueness within this disease
                    attempts = 0
                    while symptom_text in used_symptoms and attempts < 10:
                        symptom_text = self._generate_symptom()
                        attempts += 1
                    
                    used_symptoms.add(symptom_text)
                    symptom_objs.append(Symptom(
                        disease=disease, 
                        text=symptom_text, 
                        order=s_idx
                    ))
                
                # Generate unique treatments
                used_treatments = set()
                available_actions = TREATMENT_ACTIONS.copy()
                random.shuffle(available_actions)
                
                for p_idx in range(num_treatments):
                    if available_actions:
                        action = available_actions.pop()
                    else:
                        action = random.choice(TREATMENT_ACTIONS)
                    
                    treatment_text = self._generate_treatment(action)
                    used_treatments.add(treatment_text)
                    
                    prescription_objs.append(Prescription(
                        disease=disease,
                        text=treatment_text,
                        order=p_idx
                    ))

            # Bulk create symptoms and prescriptions
            self.stdout.write('Saving symptoms...')
            Symptom.objects.bulk_create(symptom_objs, batch_size=5000)
            
            self.stdout.write('Saving treatments...')
            Prescription.objects.bulk_create(prescription_objs, batch_size=5000)

            # Update diseases with prevention tips
            self.stdout.write('Adding prevention tips...')
            for disease in all_diseases:
                tips = random.sample(PREVENTION_TIPS, k=random.randint(3, 6))
                disease.prevention_tips = '\n'.join(tips)
            
            Disease.objects.bulk_update(
                all_diseases, 
                ['prevention_tips'], 
                batch_size=1000
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully created {count} diseases with symptoms and treatments!'
            )
        )
        self.stdout.write(
            f'  - {len(symptom_objs)} symptoms'
        )
        self.stdout.write(
            f'  - {len(prescription_objs)} treatments'
        )

    def _generate_description(self, plant, pathogen, disease_type):
        """Generate a realistic disease description."""
        templates = [
            f"A common {pathogen}-based infection affecting {plant} plants, characterized by {disease_type.lower()}. "
            f"This condition typically spreads during periods of high humidity.",
            
            f"{disease_type} caused by {pathogen} in {plant} crops. "
            f"Can lead to significant yield loss if not managed properly.",
            
            f"This {pathogen} disease manifests as {disease_type.lower()} on {plant} plants. "
            f"Early detection and intervention are crucial for effective management.",
            
            f"A destructive {pathogen} pathogen targeting {plant}, resulting in {disease_type.lower()}. "
            f"Often associated with poor air circulation and excessive moisture."
        ]
        return random.choice(templates)

    def _generate_symptom(self):
        """Generate a realistic symptom description."""
        descriptor = random.choice(SYMPTOM_DESCRIPTORS)
        location = random.choice(LOCATIONS)
        
        templates = [
            f"{descriptor} observed on {location}",
            f"{descriptor} appearing primarily on {location}",
            f"Progressive {descriptor.lower()} starting from {location}",
            f"Visible {descriptor.lower()} concentrated on {location}",
            f"{descriptor} with irregular patterns on {location}"
        ]
        return random.choice(templates)

    def _generate_treatment(self, action):
        """Generate a treatment recommendation."""
        frequency = random.choice([
            'Apply weekly',
            'Repeat every 7-10 days',
            'Apply bi-weekly',
            'Continue until symptoms subside'
        ])
        
        advice = random.choice([
            'monitor plant response closely',
            'ensure thorough coverage',
            'avoid application during peak sun',
            'combine with cultural practices',
            'follow product label instructions'
        ])
        
        return f"{action}. {frequency}, and {advice}."