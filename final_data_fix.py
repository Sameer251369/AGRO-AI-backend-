import os
import django
import random

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_server.settings')
django.setup()

from api.models import Disease, Symptom, Prescription, SymptomTemplate, PrescriptionTemplate

def run_fix():
    print("🚀 Starting hard reset of disease data...")

    # 1. Clear existing specific data (The "Early Blight" links)
    Symptom.objects.all().delete()
    Prescription.objects.all().delete()
    
    # 2. Get the templates you already created
    sym_pool = list(SymptomTemplate.objects.all())
    pre_pool = list(PrescriptionTemplate.objects.all())
    diseases = Disease.objects.all()

    if not sym_pool or not pre_pool:
        print("❌ Error: Your Template pools are empty! Run your population script first.")
        return

    plants = ['Tomato', 'Potato', 'Wheat', 'Rice', 'Corn', 'Apple', 'Citrus', 'Grape']
    pathogens = ['Fungus', 'Virus', 'Bacterium', 'Mite', 'Oomycete']

    symptom_objs = []
    prescription_objs = []

    for i, disease in enumerate(diseases):
        # 3. Rename the disease so it isn't "Early Blight"
        # We use i to ensure every name is technically unique
        new_name = f"{random.choice(plants)} {random.choice(pathogens)} Case-{i+1000}"
        disease.name = new_name
        disease.save()

        # 4. Pick 5 UNIQUE items from your pools for this specific disease
        selected_syms = random.sample(sym_pool, 5)
        selected_pres = random.sample(pre_pool, 5)

        for idx, temp in enumerate(selected_syms):
            symptom_objs.append(Symptom(disease=disease, text=temp.text, order=idx))
        
        for idx, temp in enumerate(selected_pres):
            prescription_objs.append(Prescription(disease=disease, text=temp.text, order=idx))

    # 5. Bulk create for speed
    Symptom.objects.bulk_create(symptom_objs, batch_size=5000)
    Prescription.objects.bulk_create(prescription_objs, batch_size=5000)
    
    print(f"✅ Success! {len(diseases)} diseases renamed and linked uniquely.")

if __name__ == "__main__":
    run_fix()