import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_server.settings')
django.setup()

from api.models import Disease, Symptom, Prescription, SymptomTemplate, PrescriptionTemplate

def hard_reset_and_link():
    print("Starting Hard Reset...")
    
    # 1. Clear existing specific symptoms/prescriptions
    Symptom.objects.all().delete()
    Prescription.objects.all().delete()
    
    # 2. Fetch the pools
    sym_pool = list(SymptomTemplate.objects.all())
    pre_pool = list(PrescriptionTemplate.objects.all())
    diseases = Disease.objects.all()

    if not sym_pool or not pre_pool:
        print("Error: Your Template Pools are empty. Run your template population script first!")
        return

    plants = ['Tomato', 'Potato', 'Wheat', 'Rice', 'Corn', 'Apple', 'Citrus', 'Grape']
    pathogens = ['Fungus', 'Virus', 'Bacterium', 'Mite', 'Oomycete']

    symptom_links = []
    prescription_links = []

    for i, disease in enumerate(diseases):
        # 3. FIX THE NAME: Change it from 'Early Blight' to something unique
        disease.name = f"{random.choice(plants)} {random.choice(pathogens)} Case-{random.randint(1000, 9999)}-{i}"
        disease.save()

        # 4. Pick unique symptoms and treatments
        selected_syms = random.sample(sym_pool, 5)
        selected_pres = random.sample(pre_pool, 5)

        for idx, template in enumerate(selected_syms):
            symptom_links.append(Symptom(disease=disease, text=template.text, order=idx))
        
        for idx, template in enumerate(selected_pres):
            prescription_links.append(Prescription(disease=disease, text=template.text, order=idx))

    # 5. Bulk Save for speed
    Symptom.objects.bulk_create(symptom_links, batch_size=5000)
    Prescription.objects.bulk_create(prescription_links, batch_size=5000)
    
    print(f"Success! {len(diseases)} diseases renamed and linked to unique data.")

if __name__ == "__main__":
    hard_reset_and_link()