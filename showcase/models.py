from decimal import Decimal
from django.db import models


def parse_pipe_urls(raw_text):
    if not raw_text:
        return []
    urls = [u.strip() for u in raw_text.split('|') if u.strip().startswith('http')]
    labeled = []
    for idx, url in enumerate(urls):
        lower = url.lower()
        if idx == 0:
            label = "Visit Website"
        elif 'contact' in lower:
            label = "Contact Page"
        elif 'exhibit' in lower:
            label = "Exhibitors"
        elif 'faq' in lower:
            label = "FAQ"
        elif 'office' in lower:
            label = "Offices"
        else:
            label = f"Link {idx + 1}"
        labeled.append({'url': url, 'label': label})
    return labeled


class SME(models.Model):
    trading_name = models.CharField(max_length=200, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    sector = models.CharField(max_length=200, blank=True)
    sub_sector = models.CharField(max_length=200, blank=True)
    product_service = models.TextField(blank=True)
    physical_address = models.TextField(blank=True)
    suburb_township = models.CharField(max_length=150, blank=True)
    municipality = models.CharField(max_length=150, blank=True)
    primary_contact = models.CharField(max_length=150, blank=True)
    contact_role = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    website_social = models.CharField(max_length=255, blank=True)
    business_stage = models.CharField(max_length=100, blank=True)
    showcase_readiness = models.PositiveSmallIntegerField(default=3, help_text="Scale 1 to 5")
    priority_events_notes = models.TextField(blank=True)
    additional_opportunities = models.TextField(blank=True)
    potential_customers = models.TextField(blank=True)
    data_sharing_consent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Incubated SME"
        verbose_name_plural = "Incubated SMEs"
        ordering = ['trading_name']

    def __str__(self):
        return self.trading_name


class ExternalEvent(models.Model):
    name = models.CharField(max_length=255, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    city_area = models.CharField(max_length=150, blank=True)
    venue = models.CharField(max_length=255, blank=True)
    full_address = models.TextField(blank=True)
    event_type = models.CharField(max_length=255, blank=True)
    relevant_sectors = models.TextField(blank=True)
    recommended_stage = models.TextField(blank=True)
    recommended_participation = models.TextField(blank=True)
    organiser = models.CharField(max_length=255, blank=True)
    contact_person = models.TextField(blank=True)
    contact_email = models.TextField(blank=True)
    phone = models.CharField(max_length=255, blank=True)
    registration_deadline = models.TextField(blank=True)
    date_venue_status = models.TextField(blank=True)
    priority = models.CharField(max_length=100, blank=True)
    selection_notes = models.TextField(blank=True)
    official_url = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date', 'name']

    @property
    def website_links(self):
        return parse_pipe_urls(self.official_url)

    @property
    def primary_url(self):
        links = self.website_links
        return links[0]['url'] if links else ''

    def __str__(self):
        return f"{self.name} ({self.start_date or 'TBC'})"


class InternalShowcase(models.Model):
    proposed_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=255)
    event_format = models.CharField(max_length=150, blank=True)
    purpose = models.TextField(blank=True)
    sme_focus = models.TextField(blank=True)
    invitees = models.TextField(blank=True)
    expected_outputs = models.TextField(blank=True)
    lead_owner = models.CharField(max_length=150, blank=True)
    success_measure = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="Proposed")
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['proposed_date']

    def __str__(self):
        return f"{self.title} ({self.proposed_date or 'TBC'})"


class Stakeholder(models.Model):
    category = models.CharField(max_length=150, blank=True)
    organisation = models.CharField(max_length=255)
    physical_address = models.TextField(blank=True)
    contact_person = models.TextField(blank=True)
    email_route = models.TextField(blank=True)
    phone = models.CharField(max_length=255, blank=True)
    suggested_ask = models.TextField(blank=True)
    priority = models.CharField(max_length=50, blank=True)
    relationship_status = models.CharField(max_length=100, default="Not approached")
    internal_owner = models.CharField(max_length=150, blank=True)
    last_contacted = models.DateField(null=True, blank=True)
    next_followup = models.DateField(null=True, blank=True)
    source_url = models.TextField(blank=True)

    class Meta:
        ordering = ['organisation']

    @property
    def website_links(self):
        return parse_pipe_urls(self.source_url)

    @property
    def primary_url(self):
        links = self.website_links
        return links[0]['url'] if links else ''

    def __str__(self):
        return f"{self.organisation} [{self.category}]"


class SMEStakeholderTarget(models.Model):
    sme = models.ForeignKey(SME, on_delete=models.CASCADE, related_name='targeted_stakeholders')
    organisation_name = models.CharField(max_length=255)
    proposed_representative = models.CharField(max_length=255, blank=True)
    reason_for_invitation = models.TextField(blank=True)
    organisation_category = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sme.trading_name} -> {self.organisation_name}"


class SMEEventScorecard(models.Model):
    DECISION_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Deferred', 'Deferred'),
        ('Declined', 'Declined'),
    ]
    sme = models.ForeignKey(SME, on_delete=models.CASCADE, related_name='scorecards')
    event = models.ForeignKey(ExternalEvent, on_delete=models.CASCADE, related_name='scorecards')
    sector_fit = models.PositiveSmallIntegerField(default=0, help_text="Max 30")
    commercial_readiness = models.PositiveSmallIntegerField(default=0, help_text="Max 20")
    compliance = models.PositiveSmallIntegerField(default=0, help_text="Max 15")
    delivery_capacity = models.PositiveSmallIntegerField(default=0, help_text="Max 15")
    pitch_demo = models.PositiveSmallIntegerField(default=0, help_text="Max 10")
    strategic_alignment = models.PositiveSmallIntegerField(default=0, help_text="Max 10")
    selection_decision = models.CharField(max_length=50, choices=DECISION_CHOICES, default='Pending')
    notes_gaps = models.TextField(blank=True)

    class Meta:
        unique_together = ('sme', 'event')

    @property
    def total_score(self):
        return (
            self.sector_fit + self.commercial_readiness + self.compliance +
            self.delivery_capacity + self.pitch_demo + self.strategic_alignment
        )

    @property
    def recommendation(self):
        score = self.total_score
        if score >= 75:
            return "Exhibit / Pitch"
        elif score >= 60:
            return "Attend / Network"
        return "Hold / Build Readiness"

    def __str__(self):
        return f"{self.sme} @ {self.event.name} ({self.total_score}/100)"


class EventBudget(models.Model):
    event = models.ForeignKey(ExternalEvent, on_delete=models.CASCADE, related_name='budgets')
    sme = models.ForeignKey(SME, on_delete=models.SET_NULL, null=True, blank=True)
    participation_type = models.CharField(max_length=150, blank=True)
    registration_stand_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transport = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accommodation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    freight_samples = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    display_av = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    marketing_printing = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contingency_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    funding_source = models.CharField(max_length=150, blank=True)
    approval_status = models.CharField(max_length=50, default="Not approved")
    actual_spend = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    @property
    def subtotal(self):
        return (
            self.registration_stand_fee + self.transport + self.accommodation +
            self.freight_samples + self.display_av + self.marketing_printing + self.other_cost
        )

    @property
    def contingency_value(self):
        return (self.subtotal * (self.contingency_pct / Decimal('100'))).quantize(Decimal('0.01'))

    @property
    def estimated_total(self):
        return self.subtotal + self.contingency_value

    @property
    def variance(self):
        if self.actual_spend is None:
            return None
        return self.estimated_total - self.actual_spend

    def __str__(self):
        return f"Budget: {self.event.name} - {self.sme or 'Cohort'}"


class ParticipationLog(models.Model):
    event_name = models.CharField(max_length=255)
    event_date = models.DateField(null=True, blank=True)
    sme = models.ForeignKey(SME, on_delete=models.CASCADE, related_name='participations')
    participation_type = models.CharField(max_length=100, blank=True)
    leads_captured = models.PositiveIntegerField(default=0)
    qualified_buyer_leads = models.PositiveIntegerField(default=0)
    buyer_meetings = models.PositiveIntegerField(default=0)
    investor_meetings = models.PositiveIntegerField(default=0)
    partnership_leads = models.PositiveIntegerField(default=0)
    partnerships_confirmed = models.PositiveIntegerField(default=0)
    potential_sales_zar = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    confirmed_sales_zar = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    follow_up_status = models.CharField(max_length=100, default="Pending")
    outcome_next_action = models.TextField(blank=True)

    def __str__(self):
        return f"{self.sme} - {self.event_name}"


class MonthlyPlan(models.Model):
    month = models.CharField(max_length=50)
    programme_window = models.DateField(null=True, blank=True)
    primary_objective = models.TextField(blank=True)
    external_event_anchors = models.TextField(blank=True)
    proposed_internal_activity = models.TextField(blank=True)
    sme_focus = models.TextField(blank=True)
    key_milestones = models.TextField(blank=True)
    lead_owner = models.CharField(max_length=150, blank=True)
    planning_kpi = models.TextField(blank=True)
    resourcing_budget = models.TextField(blank=True)

    def __str__(self):
        return f"{self.month} 2027"


class ProgrammeMilestone(models.Model):
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    activity = models.CharField(max_length=255)
    milestone_type = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    owner = models.CharField(max_length=150, blank=True)
    deadline_note = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="Planned")
    action_required = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.start_date}: {self.activity}"


class ProgrammeRisk(models.Model):
    risk_description = models.TextField()
    impact = models.CharField(max_length=50, blank=True)
    likelihood = models.CharField(max_length=50, blank=True)
    priority = models.CharField(max_length=50, blank=True)
    mitigation = models.TextField(blank=True)
    owner = models.CharField(max_length=150, blank=True)
    trigger_due_date = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=50, default="Open")

    def __str__(self):
        return f"[{self.priority}] {self.risk_description[:60]}"