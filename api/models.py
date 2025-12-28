from django.db import models


class Disease(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    symptoms = models.TextField(blank=True, help_text='Line-separated symptoms')
    treatment = models.TextField(blank=True, help_text='Line-separated treatment steps')
    prevention_tips = models.TextField(blank=True, help_text='Line-separated prevention tips')

    def __str__(self):
        return self.name


class Symptom(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='symptom_set')
    text = models.CharField(max_length=512)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.disease.name}: {self.text}"


class Prescription(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='prescription_set')
    text = models.CharField(max_length=1024)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.disease.name}: {self.text}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.name} <{self.email}> - {self.subject}"


class SymptomTemplate(models.Model):
    text = models.CharField(max_length=512, unique=True)

    def __str__(self):
        return self.text[:80]


class PrescriptionTemplate(models.Model):
    text = models.CharField(max_length=1024, unique=True)

    def __str__(self):
        return self.text[:80] 
