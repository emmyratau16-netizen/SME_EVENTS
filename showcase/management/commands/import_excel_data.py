import pandas as pd
from django.core.management.base import BaseCommand
from showcase.models import (
    SME, ExternalEvent, InternalShowcase, Stakeholder, SMEStakeholderTarget,
    MonthlyPlan, ProgrammeMilestone, ProgrammeRisk
)


def clean_str(val):
    return "" if pd.isna(val) else str(val).strip()


def clean_date(val):
    if pd.isna(val):
        return None
    ts = pd.to_datetime(val, errors='coerce')
    return None if pd.isna(ts) else ts.date()


class Command(BaseCommand):
    help = "Imports SME_EVENT.xlsx and Gauteng_SME_Events_Showcase_Master_Programme_2027.xlsx into Django"

    def handle(self, *args, **options):
        master_file = 'Gauteng_SME_Events_Showcase_Master_Programme_2027.xlsx'
        sme_file = 'SME_EVENT.xlsx'

        df_smes = pd.read_excel(sme_file, sheet_name='Matching SMEs to events', header=2).dropna(subset=['SME'])
        sme_map = {}
        for _, row in df_smes.iterrows():
            name = clean_str(row['SME'])
            sme_obj, _ = SME.objects.update_or_create(
                trading_name=name,
                defaults={
                    'priority_events_notes': clean_str(row.get('Priority events')),
                    'additional_opportunities': clean_str(row.get('Additional opportunities')),
                    'potential_customers': clean_str(row.get('Potential customers to approach')),
                }
            )
            sme_map[name.lower()] = sme_obj

        df_targets = pd.read_excel(sme_file, sheet_name='Investors for each SME')
        current_sme = None
        for _, row in df_targets.iterrows():
            first_col = clean_str(row.iloc[0])
            if not first_col or first_col == 'Organisation to invite':
                continue
            matched = False
            for key, obj in sme_map.items():
                if key in first_col.lower() and ('–' in first_col or '-' in first_col):
                    current_sme = obj
                    if '–' in first_col:
                        current_sme.sector = first_col.split('–', 1)[1].strip()
                        current_sme.save()
                    matched = True
                    break
            if not matched and current_sme:
                SMEStakeholderTarget.objects.get_or_create(
                    sme=current_sme,
                    organisation_name=first_col,
                    defaults={
                        'proposed_representative': clean_str(row.iloc[1]),
                        'reason_for_invitation': clean_str(row.iloc[2]),
                        'organisation_category': clean_str(row.iloc[3]),
                        'email': clean_str(row.iloc[4]),
                        'phone': clean_str(row.iloc[5]),
                        'address': clean_str(row.iloc[6]),
                    }
                )

        df_events = pd.read_excel(master_file, sheet_name='2027 Event Database', header=3).dropna(subset=['Event'])
        for _, row in df_events.iterrows():
            ExternalEvent.objects.update_or_create(
                name=clean_str(row['Event']),
                defaults={
                    'start_date': clean_date(row.get('Start Date')),
                    'end_date': clean_date(row.get('End Date')),
                    'city_area': clean_str(row.get('City / Area')),
                    'venue': clean_str(row.get('Venue')),
                    'full_address': clean_str(row.get('Full Physical Venue Address')),
                    'event_type': clean_str(row.get('Event Type')),
                    'relevant_sectors': clean_str(row.get('Relevant SME Sectors')),
                    'recommended_stage': clean_str(row.get('Recommended SME Stage / Readiness')),
                    'recommended_participation': clean_str(row.get('Recommended Participation')),
                    'organiser': clean_str(row.get('Organiser')),
                    'contact_person': clean_str(row.get('Who to Contact')),
                    'contact_email': clean_str(row.get('Email / Contact Route')),
                    'phone': clean_str(row.get('Phone')),
                    'registration_deadline': clean_str(row.get('Registration / Deadline')),
                    'date_venue_status': clean_str(row.get('Date / Venue Status')),
                    'priority': clean_str(row.get('Priority')),
                    'selection_notes': clean_str(row.get('Selection Notes / Cautions')),
                    'official_url': clean_str(row.get('Official Event Source URL')),
                }
            )

        df_internal = pd.read_excel(master_file, sheet_name='Internal Showcases', header=3).dropna(subset=['Internal Event / Activity'])
        for _, row in df_internal.iterrows():
            InternalShowcase.objects.update_or_create(
                title=clean_str(row['Internal Event / Activity']),
                defaults={
                    'proposed_date': clean_date(row.get('Proposed Date')),
                    'event_format': clean_str(row.get('Format')),
                    'purpose': clean_str(row.get('Purpose / Expected Value')),
                    'sme_focus': clean_str(row.get('SME Profile / Sector Focus')),
                    'invitees': clean_str(row.get('Invitees / Stakeholders')),
                    'expected_outputs': clean_str(row.get('Expected Outputs')),
                    'lead_owner': clean_str(row.get('Lead Owner')),
                    'success_measure': clean_str(row.get('Success Measure')),
                    'status': clean_str(row.get('Status')) or 'Proposed',
                    'location': clean_str(row.get('Location / Venue')),
                }
            )

        df_stakeholders = pd.read_excel(master_file, sheet_name='Stakeholder Pipeline', header=3).dropna(subset=['Organisation'])
        for _, row in df_stakeholders.iterrows():
            Stakeholder.objects.update_or_create(
                organisation=clean_str(row['Organisation']),
                defaults={
                    'category': clean_str(row.get('Category')),
                    'physical_address': clean_str(row.get('Physical Address')),
                    'contact_person': clean_str(row.get('Who to Contact / Role')),
                    'email_route': clean_str(row.get('Public Email / Contact Route')),
                    'phone': clean_str(row.get('Phone')),
                    'suggested_ask': clean_str(row.get('Suggested First Engagement / Ask')),
                    'priority': clean_str(row.get('Priority')),
                    'relationship_status': clean_str(row.get('Relationship Status')) or 'Not approached',
                    'internal_owner': clean_str(row.get('Internal Owner')),
                    'source_url': clean_str(row.get('Source URL')),
                }
            )

        df_plan = pd.read_excel(master_file, sheet_name='12-Month SME Plan', header=3).dropna(subset=['Month'])
        for _, row in df_plan.iterrows():
            MonthlyPlan.objects.update_or_create(
                month=clean_str(row['Month']),
                defaults={
                    'programme_window': clean_date(row.get('Programme Date / Window')),
                    'primary_objective': clean_str(row.get('Primary Objective')),
                    'external_event_anchors': clean_str(row.get('External Event Anchors')),
                    'proposed_internal_activity': clean_str(row.get('Proposed Internal Activity')),
                    'sme_focus': clean_str(row.get('SME Focus / Selection')),
                    'key_milestones': clean_str(row.get('Key Milestones')),
                    'lead_owner': clean_str(row.get('Lead Owner')),
                    'planning_kpi': clean_str(row.get('Planning KPI / Target')),
                    'resourcing_budget': clean_str(row.get('Resourcing / Budget Items')),
                }
            )

        df_milestones = pd.read_excel(master_file, sheet_name='Events Calendar & Milestones', header=3).dropna(subset=['Activity / Event'])
        for _, row in df_milestones.iterrows():
            ProgrammeMilestone.objects.get_or_create(
                activity=clean_str(row['Activity / Event']),
                start_date=clean_date(row.get('Start Date')),
                defaults={
                    'end_date': clean_date(row.get('End Date')),
                    'milestone_type': clean_str(row.get('Type')),
                    'location': clean_str(row.get('Location / Venue')),
                    'owner': clean_str(row.get('Owner')),
                    'deadline_note': clean_str(row.get('Registration / Deadline')),
                    'status': clean_str(row.get('Status')) or 'Planned',
                    'action_required': clean_str(row.get('Milestone / Action Required')),
                }
            )

        df_risks = pd.read_excel(master_file, sheet_name='Risks & Assumptions', header=3).dropna(subset=['Risk / Assumption'])
        for _, row in df_risks.iterrows():
            ProgrammeRisk.objects.get_or_create(
                risk_description=clean_str(row['Risk / Assumption']),
                defaults={
                    'impact': clean_str(row.get('Impact')),
                    'likelihood': clean_str(row.get('Likelihood')),
                    'priority': clean_str(row.get('Priority')),
                    'mitigation': clean_str(row.get('Mitigation / Control')),
                    'owner': clean_str(row.get('Owner')),
                    'trigger_due_date': clean_str(row.get('Trigger / Due Date')),
                    'status': clean_str(row.get('Status')) or 'Open',
                }
            )

        self.stdout.write(self.style.SUCCESS(
            f"Import complete: {SME.objects.count()} SMEs, {ExternalEvent.objects.count()} External Events, "
            f"{InternalShowcase.objects.count()} Internal Showcases, {Stakeholder.objects.count()} Stakeholders."
        ))