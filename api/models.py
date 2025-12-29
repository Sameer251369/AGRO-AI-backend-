from django.db import models


class Disease(models.Model):
    """Plant disease information."""
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    prevention_tips = models.TextField(
        blank=True, 
        help_text='Line-separated prevention tips'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Diseases'

    def __str__(self):
        return self.name


class Symptom(models.Model):
    """Symptoms associated with a disease."""
    disease = models.ForeignKey(
        Disease, 
        on_delete=models.CASCADE, 
        related_name='symptom_set'
    )
    text = models.CharField(max_length=512)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['disease', 'order']),
        ]

    def __str__(self):
        return f"{self.disease.name}: {self.text[:50]}"


class Prescription(models.Model):
    """Treatment prescriptions for a disease."""
    disease = models.ForeignKey(
        Disease, 
        on_delete=models.CASCADE, 
        related_name='prescription_set'
    )
    text = models.CharField(max_length=1024)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['disease', 'order']),
        ]

    def __str__(self):
        return f"{self.disease.name}: {self.text[:50]}"


class ContactMessage(models.Model):
    """Contact form submissions."""
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Contact from {self.name} <{self.email}> - {self.subject}"


class SymptomTemplate(models.Model):
    """Reusable symptom templates for data generation."""
    text = models.CharField(max_length=512, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['text']

    def __str__(self):
        return self.text[:80]


class PrescriptionTemplate(models.Model):
    """Reusable prescription templates for data generation."""
    text = models.CharField(max_length=1024, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['text']

    def __str__(self):
        return self.text[:80]