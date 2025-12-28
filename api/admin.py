from django.contrib import admin
from .models import Disease, Symptom, Prescription
from .models import SymptomTemplate, PrescriptionTemplate


class SymptomInline(admin.TabularInline):
    model = Symptom
    extra = 0
    fields = ('text', 'order')


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    fields = ('text', 'order')


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    search_fields = ('name', 'category')
    inlines = [SymptomInline, PrescriptionInline]


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('id', 'disease', 'text')
    search_fields = ('text',)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'disease', 'text')
    search_fields = ('text',)


@admin.register(SymptomTemplate)
class SymptomTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'text')
    search_fields = ('text',)


@admin.register(PrescriptionTemplate)
class PrescriptionTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'text')
    search_fields = ('text',)
