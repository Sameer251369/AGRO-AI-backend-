import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_server.settings')
django.setup()

from api.models import Disease, Symptom, Prescription, SymptomTemplate, PrescriptionTemplate

def run_fix():
    print("🚀 Starting hard reset of disease data...")

    Symptom.objects.all().delete()
    Prescription.objects.all().delete()

    sym_pool = list(SymptomTemplate.objects.all())
    pre_pool = list(PrescriptionTemplate.objects.all())
    diseases = Disease.objects.all()

    if not sym_pool or not pre_pool:
        print("❌ Template pools empty. Run population script first.")
        return

    plants = ['Tomato', 'Potato', 'Wheat', 'Rice', 'Corn', 'Apple', 'Citrus', 'Grape']
    pathogens = ['Fungus', 'Virus', 'Bacterium', 'Mite', 'Oomycete']

    symptom_objs = []
    prescription_objs = []

    for i, disease in enumerate(diseases):
        disease.name = f"{random.choice(plants)} {random.choice(pathogens)} Case-{i+1000}"
        disease.save()

        for idx, temp in enumerate(random.sample(sym_pool, 5)):
            symptom_objs.append(Symptom(disease=disease, text=temp.text, order=idx))

        for idx, temp in enumerate(random.sample(pre_pool, 5)):
            prescription_objs.append(Prescription(disease=disease, text=temp.text, order=idx))

    Symptom.objects.bulk_create(symptom_objs, batch_size=5000)
    Prescription.objects.bulk_create(prescription_objs, batch_size=5000)

    print(f"✅ Fixed {len(diseases)} diseases successfully.")

if __name__ == "__main__":
    run_fix()
