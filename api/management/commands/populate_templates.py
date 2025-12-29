import random
from django.core.management.base import BaseCommand
from api.models import SymptomTemplate, PrescriptionTemplate

# Keep your ADJECTIVES, LOCATIONS, VERBS, and TREAT_ACTIONS lists here...

def gen_symptom(i):
    return f"{random.choice(ADJECTIVES).capitalize()} {random.choice(VERBS)} observed on {random.choice(LOCATIONS)} (Ref: {i:04d})"

def gen_prescription(i):
    extra = random.choice(['monitor regularly', 'consult local extension', 'adjust fertilization', 'avoid overhead irrigation'])
    return f"{random.choice(TREAT_ACTIONS).capitalize()}; {extra} (Ref: {i:04d})"

class Command(BaseCommand):
    help = 'Populate SymptomTemplate and PrescriptionTemplate pools efficiently'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=2000, help='Number of templates to create')

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(f"Generating {count} templates for each pool...")

        # 1. Generate unique texts using Sets (prevents duplicates in memory)
        symptom_texts = {gen_symptom(i) for i in range(1, count + 1)}
        prescription_texts = {gen_prescription(i) for i in range(1, count + 1)}

        # 2. Prepare objects for bulk creation
        symptom_objs = [SymptomTemplate(text=t) for t in symptom_texts]
        prescription_objs = [PrescriptionTemplate(text=t) for t in prescription_texts]

        # 3. Bulk Create (This is 100x faster than a loop)
        try:
            SymptomTemplate.objects.bulk_create(symptom_objs, ignore_conflicts=True)
            PrescriptionTemplate.objects.bulk_create(prescription_objs, ignore_conflicts=True)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully populated {len(symptom_objs)} symptoms and {len(prescription_objs)} prescriptions!'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during population: {e}"))