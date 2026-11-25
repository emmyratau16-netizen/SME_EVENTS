from django.contrib import admin
from .models import (
    SME, ExternalEvent, InternalShowcase, Stakeholder, SMEStakeholderTarget,
    SMEEventScorecard, EventBudget, ParticipationLog, MonthlyPlan,
    ProgrammeMilestone, ProgrammeRisk
)


class SMEStakeholderTargetInline(admin.TabularInline):
    model = SMEStakeholderTarget
    extra = 1


@admin.register(SME)
class SMEAdmin(admin.ModelAdmin):
    list_display = ('trading_name', 'sector', 'suburb_township', 'business_stage', 'showcase_readiness', 'data_sharing_consent')
    search_fields = ('trading_name', 'sector', 'product_service')
    inlines = [SMEStakeholderTargetInline]


@admin.register(ExternalEvent)
class ExternalEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'city_area', 'venue', 'priority')
    list_filter = ('priority', 'city_area')
    search_fields = ('name', 'relevant_sectors', 'organiser')


@admin.register(InternalShowcase)
class InternalShowcaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'proposed_date', 'event_format', 'lead_owner', 'status')
    list_filter = ('status',)


@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ('organisation', 'category', 'priority', 'relationship_status', 'internal_owner', 'next_followup')
    list_filter = ('category', 'priority', 'relationship_status')
    search_fields = ('organisation', 'contact_person', 'suggested_ask')


@admin.register(SMEEventScorecard)
class SMEEventScorecardAdmin(admin.ModelAdmin):
    list_display = ('sme', 'event', 'total_score', 'recommendation', 'selection_decision')
    list_filter = ('selection_decision', 'event')


@admin.register(EventBudget)
class EventBudgetAdmin(admin.ModelAdmin):
    list_display = ('event', 'sme', 'estimated_total', 'actual_spend', 'variance', 'approval_status')
    list_filter = ('approval_status', 'event')


@admin.register(ParticipationLog)
class ParticipationLogAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'sme', 'event_date', 'qualified_buyer_leads', 'potential_sales_zar', 'confirmed_sales_zar')


admin.site.register(MonthlyPlan)
admin.site.register(ProgrammeMilestone)
admin.site.register(ProgrammeRisk)