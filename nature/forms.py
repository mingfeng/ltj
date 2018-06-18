from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from nature.models import FeatureClass, Criterion, ConservationProgramme, Protection, ProtectionCriterion, \
    ProtectionConservationProgramme


class FeatureForm(forms.ModelForm):
    feature_class = forms.ModelChoiceField(
        queryset=FeatureClass.objects.order_by('name'),
        label=FeatureClass._meta.verbose_name.capitalize(),
    )

    class Meta:
        widgets = {
            'text': CKEditorWidget,
            'text_www': CKEditorWidget,
            'description': forms.Textarea,
            'notes': forms.Textarea,
            'name': forms.TextInput(attrs={'size': '80'})
        }


class HabitatTypeObservationInlineForm(forms.ModelForm):

    class Meta:
        widgets = {
            'additional_info': forms.Textarea(attrs={'rows': '5'}),
        }


class ProtectionInlineForm(forms.ModelForm):
    criteria = forms.ModelMultipleChoiceField(
        queryset=Criterion.objects.all(),
        widget=FilteredSelectMultiple(verbose_name=_('Criteria'), is_stacked=False),
    )
    conservation_programmes = forms.ModelMultipleChoiceField(
        queryset=ConservationProgramme.objects.all(),
        widget=FilteredSelectMultiple(verbose_name=_('Conservation programmes'), is_stacked=False),

    )

    class Meta:
        model = Protection
        fields = '__all__'

    @transaction.atomic
    def save(self, commit=True):
        protection = super().save(commit=False)
        if commit:
            protection.save()

        if protection.pk:
            # django does not allow saving m2m with manually specified m2m intermediate
            # tables, so use intermediate model manager instead.
            ProtectionCriterion.objects.filter(protection=protection).delete()
            protection_criteria = [
                ProtectionCriterion(
                    protection=protection,
                    criterion=criterion,
                ) for criterion in self.cleaned_data['criteria']
            ]
            ProtectionCriterion.objects.bulk_create(protection_criteria)

            ProtectionConservationProgramme.objects.filter(protection=protection).delete()
            protection_conservation_programmes = [
                ProtectionConservationProgramme(
                    protection=protection,
                    conservation_programme=conservation_programme,
                ) for conservation_programme in self.cleaned_data['conservation_programmes']
            ]
            ProtectionConservationProgramme.objects.bulk_create(protection_conservation_programmes)

        return protection
