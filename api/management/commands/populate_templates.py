from django.core.management.base import BaseCommand
from api.models import SymptomTemplate, PrescriptionTemplate
import random


ADJECTIVES = [
    'dark', 'light', 'severe', 'mild', 'patchy', 'systemic', 'localized', 'circular', 'elongated', 'irregular'
]

LOCATIONS = [
    'leaf edges', 'leaf tips', 'lower leaves', 'upper leaves', 'stem', 'petiole', 'veins', 'entire leaf', 'fruit surface'
]

VERBS = [
    'spots', 'lesions', 'necrosis', 'discoloration', 'chlorosis', 'wilting', 'blight', 'mottling', 'cankers'
]

TREAT_ACTIONS = [
    'remove infected tissue', 'apply copper-based fungicide', 'apply systemic insecticide', 'increase airflow',
    'reduce overhead watering', 'improve drainage', 'apply neem oil', 'rotate crops', 'use resistant varieties', 'mulch around base'
]


def gen_symptom(i):
    # Generate a varied symptom string
    a = random.choice(ADJECTIVES)
    v = random.choice(VERBS)
    loc = random.choice(LOCATIONS)
    return f"{a.capitalize()} {v} observed on {loc} ({i:04d})"


def gen_prescription(i):
    # Generate a varied prescription string
    action = random.choice(TREAT_ACTIONS)
    extra = random.choice(['monitor regularly', 'consult local extension', 'adjust fertilization', 'avoid overhead irrigation'])
    return f"{action.capitalize()}; {extra} ({i:04d})"


class Command(BaseCommand):
    help = 'Populate SymptomTemplate and PrescriptionTemplate pools with unique entries'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=2000, help='Number of templates to create for each pool')

    def handle(self, *args, **options):
        count = options['count']
        created_sym = 0
        created_pres = 0

        # Create symptom templates
        for i in range(1, count + 1):
            text = gen_symptom(i)
            obj, created = SymptomTemplate.objects.get_or_create(text=text)
            if created:
                created_sym += 1

        # Create prescription templates
        for i in range(1, count + 1):
            text = gen_prescription(i)
            obj, created = PrescriptionTemplate.objects.get_or_create(text=text)
            if created:
                created_pres += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_sym} symptom templates and {created_pres} prescription templates'))
