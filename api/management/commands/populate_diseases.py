from django.core.management.base import BaseCommand
from api.models import Disease


class Command(BaseCommand):
    help = 'Populate the database with 2000 placeholder diseases'

    def handle(self, *args, **options):
        Disease.objects.all().delete()
        objs = []
        for i in range(1, 2001):
            name = f'Disease {i:04d}'
            # Create small example content for symptoms, treatment and prevention
            symptoms = f"Symptom A for {name}\nSymptom B for {name}\nSymptom C for {name}"
            treatment = f"Remove infected parts\nApply appropriate fungicide\nImprove air circulation"
            prevention = f"Crop rotation\nUse resistant varieties\nAvoid overhead watering"
            objs.append(
                Disease(
                    name=name,
                    description=f'Placeholder description for {name}',
                    symptoms=symptoms,
                    treatment=treatment,
                    prevention_tips=prevention,
                )
            )
        Disease.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS('Created 2000 diseases'))
