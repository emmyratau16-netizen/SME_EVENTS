from django import forms
from .models import (
    SMEEventScorecard, EventBudget, ParticipationLog,
    SMEStakeholderTarget, InternalShowcase
)


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.update({'class': 'form-select form-select-sm'})
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({'class': 'form-control form-control-sm', 'rows': 2})
            else:
                widget.attrs.update({'class': 'form-control form-control-sm'})


class InternalShowcaseForm(BootstrapFormMixin, forms.ModelForm):
    STATUS_CHOICES = [
        ('Proposed', 'Proposed'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES)

    class Meta:
        model = InternalShowcase
        fields = [
            'proposed_date', 'title', 'event_format', 'sme_focus',
            'purpose', 'invitees', 'lead_owner', 'location', 'status'
        ]
        widgets = {
            'proposed_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SMEEventScorecardForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SMEEventScorecard
        fields = [
            'sme', 'event', 'sector_fit', 'commercial_readiness',
            'compliance', 'delivery_capacity', 'pitch_demo',
            'strategic_alignment', 'selection_decision', 'notes_gaps'
        ]


class EventBudgetForm(BootstrapFormMixin, forms.ModelForm):
    APPROVAL_CHOICES = [
        ('Not approved', 'Not approved'),
        ('Pending Review', 'Pending Review'),
        ('Approved', 'Approved'),
    ]
    approval_status = forms.ChoiceField(choices=APPROVAL_CHOICES)

    class Meta:
        model = EventBudget
        fields = [
            'event', 'sme', 'participation_type', 'registration_stand_fee',
            'transport', 'accommodation', 'freight_samples', 'display_av',
            'marketing_printing', 'other_cost', 'contingency_pct',
            'funding_source', 'approval_status', 'actual_spend', 'notes'
        ]


class ParticipationLogForm(BootstrapFormMixin, forms.ModelForm):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    follow_up_status = forms.ChoiceField(choices=STATUS_CHOICES)

    class Meta:
        model = ParticipationLog
        fields = [
            'event_name', 'event_date', 'sme', 'participation_type',
            'leads_captured', 'qualified_buyer_leads', 'buyer_meetings',
            'investor_meetings', 'partnership_leads', 'partnerships_confirmed',
            'potential_sales_zar', 'confirmed_sales_zar',
            'follow_up_status', 'outcome_next_action'
        ]
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SMEStakeholderTargetForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SMEStakeholderTarget
        fields = [
            'organisation_name', 'organisation_category', 'proposed_representative',
            'email', 'phone', 'reason_for_invitation'
        ]