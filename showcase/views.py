import io
import json
from collections import Counter
from datetime import date, timedelta
import pandas as pd
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    EventBudgetForm, InternalShowcaseForm, ParticipationLogForm,
    SMEEventScorecardForm, SMEStakeholderTargetForm
)
from .models import (
    SME, ExternalEvent, InternalShowcase, Stakeholder, SMEStakeholderTarget,
    SMEEventScorecard, EventBudget, ParticipationLog,
    MonthlyPlan, ProgrammeMilestone, ProgrammeRisk
)

SUGGESTED_INTERNAL_SHOWCASES = [
    {
        'proposed_date': date(2027, 3, 12),
        'title': 'Soweto Youth & SME Digital Innovation Hackathon',
        'event_format': '24-Hour Build Sprint / Hackathon',
        'purpose': 'Pair student developers and cybersecurity mentors with cohort SMEs to build working digital prototypes, cybersecurity checklists, and EdTech tools.',
        'sme_focus': 'Tekhov, BCAT Academy, EcoHarvest and digital-enabled SMEs',
        'invitees': 'UJ Faculty of Science/CBE, SWGC ICT students, Liquid Intelligent Technologies, Cybersecurity Hub SA, Vuka Development Centre',
        'expected_outputs': 'Working software/web prototypes, cybersecurity audit templates, and youth talent linkages',
        'lead_owner': 'SME Readiness Lead + Tech Partners',
        'success_measure': 'At least 3 functional SME digital tools or prototypes built in 24 hours',
        'status': 'Proposed',
        'location': 'UJ Soweto Campus / Soweto Innovation Hub (TBC)',
    },
    {
        'proposed_date': date(2027, 5, 7),
        'title': 'Gauteng GreenTech & Agri-Innovation Challenge',
        'event_format': 'Prototype & Sustainability Competition',
        'purpose': 'Competitive product validation and pitch challenge for sustainable agriculture, soil/crop tech, and clean-energy SMEs ahead of mid-year trade fairs.',
        'sme_focus': 'Temo Green Gold, EcoHarvest and green/agri-processing ventures',
        'invitees': 'Agricultural Research Council (ARC), GreenCape, GDARD, TIA, SAB Foundation, Food & Trees for Africa',
        'expected_outputs': 'Technical validation feedback, pilot farm site introductions, and commercialization grants shortlist',
        'lead_owner': 'Partnerships Lead',
        'success_measure': '2+ pilot or R&D validation agreements secured for competing SMEs',
        'status': 'Proposed',
        'location': 'Johannesburg / Soweto Agri-Hub (TBC)',
    },
    {
        'proposed_date': date(2027, 6, 11),
        'title': '60-Second Elevator Pitch & Traction Knock-Out',
        'event_format': 'Live Pitch Competition',
        'purpose': 'High-energy elimination pitch competition testing founder clarity, unit economics, and customer traction for seed/service voucher prizes.',
        'sme_focus': 'All 5 incubated SMEs (Tekhov, BCAT Academy, Temo Green Gold, EcoHarvest, Kuzozokuhle Properties)',
        'invitees': 'Jozi Angels, NYDA, GEP, SEDFA, Business Partners Limited, SAICA Enterprise Development',
        'expected_outputs': 'Ranked pitch scores, investor warm introductions, and targeted mentorship pairings',
        'lead_owner': 'Programme Manager + SME Readiness Lead',
        'success_measure': '100% of cohort pitches scored; top 2 winners matched to angel/DFI screening',
        'status': 'Proposed',
        'location': 'Johannesburg / Virtual Hybrid (TBC)',
    },
    {
        'proposed_date': date(2027, 8, 28),
        'title': 'Soweto Pop-Up Retail & Spaza Market Challenge',
        'event_format': 'Live Consumer Sales & Merchandising Competition',
        'purpose': 'Weekend township pop-up market where SMEs test live pricing, packaging, and customer conversion with real Soweto shoppers and spaza/tuckshop buyers.',
        'sme_focus': 'Consumer goods, agri-food, youth/women-led SMEs and local service brands',
        'invitees': 'United Soweto Business Alliance (USBA), SASTA (Spaza & Tuckshop Association), Zodwa Khoza Foundation, local shoppers',
        'expected_outputs': 'Actual weekend ZAR sales data, customer feedback logs, and township retail distribution leads',
        'lead_owner': 'Event / Logistics Lead + Stakeholder Lead',
        'success_measure': 'Each participating SME captures at least 15 verified customer/retailer leads',
        'status': 'Proposed',
        'location': 'Pimville / Vilakazi Precinct, Soweto (TBC)',
    },
    {
        'proposed_date': date(2027, 9, 24),
        'title': 'Smart Student Housing & Built-Environment Designathon',
        'event_format': 'Co-Creation Design Competition',
        'purpose': 'Collaborative design and compliance sprint solving NSFAS accreditation, energy efficiency, and student safety in township student accommodation.',
        'sme_focus': 'Kuzozokuhle Properties and built-environment / facilities SMEs',
        'invitees': 'UJ Student Accommodation & Residence Life, NSFAS Provider Relations, SAIBPP, PPRA, Watu Group',
        'expected_outputs': 'NSFAS accreditation readiness checklist, upgraded room/safety blueprint, and university referral pathway',
        'lead_owner': 'SME Readiness Lead',
        'success_measure': 'Completed accreditation roadmap and 2+ institutional housing introductions',
        'status': 'Proposed',
        'location': 'UJ Doornfontein / Soweto Campus (TBC)',
    },
    {
        'proposed_date': date(2027, 10, 22),
        'title': 'AI, POPIA & Digital Growth Implementation Sprint',
        'event_format': 'Hands-On Tooling Hackathon',
        'purpose': 'Practical 1-day sprint where SMEs implement AI marketing workflows, POPIA consent compliance, and automated bookkeeping before Flagship Demo Day.',
        'sme_focus': 'All incubated SMEs (led by Tekhov & EcoHarvest peer-sharing alongside industry mentors)',
        'invitees': 'IAB SA, Rogerwilco, VML South Africa, ICT SMME Chamber, TEDCOZA',
        'expected_outputs': 'Live digital marketing campaigns, POPIA-compliant lead capture forms, and updated financial decks',
        'lead_owner': 'Programme Coordinator + Digital Mentors',
        'success_measure': 'All 5 SMEs launch a live digital lead-capture asset before November Demo Day',
        'status': 'Proposed',
        'location': 'Incubation Hub / Computer Lab (TBC)',
    },
]


def build_calendar_events(external_events, internal_showcases, milestones):
    cal_items = []

    for ev in external_events:
        if not ev.start_date:
            continue
        end_exclusive = (ev.end_date + timedelta(days=1)) if ev.end_date else (ev.start_date + timedelta(days=1))
        cal_items.append({
            'id': f"ext_{ev.id}",
            'title': ev.name,
            'start': ev.start_date.isoformat(),
            'end': end_exclusive.isoformat(),
            'allDay': True,
            'backgroundColor': '#0d6efd',
            'borderColor': '#0a58ca',
            'extendedProps': {
                'category': 'external',
                'categoryLabel': 'External Event',
                'modelType': 'external_event',
                'recordId': ev.id,
                'dateRange': f"{ev.start_date} to {ev.end_date or ev.start_date}",
                'location': f"{ev.venue} ({ev.city_area})".strip(" ()"),
                'statusOrPriority': ev.priority or 'Standard',
                'sectorsOrFocus': ev.relevant_sectors or 'General SMEs',
                'notes': ev.selection_notes or ev.recommended_participation or '',
                'deadline': ev.registration_deadline or 'TBC',
                'url': ev.primary_url,
            }
        })

    for item in internal_showcases:
        if not item.proposed_date:
            continue
        cal_items.append({
            'id': f"int_{item.id}",
            'title': item.title,
            'start': item.proposed_date.isoformat(),
            'allDay': True,
            'backgroundColor': '#198754',
            'borderColor': '#146c43',
            'extendedProps': {
                'category': 'internal',
                'categoryLabel': 'Internal Showcase',
                'modelType': 'internal_showcase',
                'recordId': item.id,
                'dateRange': item.proposed_date.isoformat(),
                'location': item.location or 'TBC',
                'statusOrPriority': item.status or 'Proposed',
                'sectorsOrFocus': item.sme_focus or 'All SMEs',
                'notes': item.purpose or '',
                'deadline': item.event_format or '',
                'url': '',
            }
        })

    for ms in milestones:
        if not ms.start_date:
            continue
        end_exclusive = (ms.end_date + timedelta(days=1)) if ms.end_date else (ms.start_date + timedelta(days=1))
        cal_items.append({
            'id': f"ms_{ms.id}",
            'title': ms.activity,
            'start': ms.start_date.isoformat(),
            'end': end_exclusive.isoformat(),
            'allDay': True,
            'backgroundColor': '#fd7e14',
            'borderColor': '#ca6510',
            'extendedProps': {
                'category': 'milestone',
                'categoryLabel': 'Milestone',
                'modelType': 'milestone',
                'recordId': ms.id,
                'dateRange': f"{ms.start_date} to {ms.end_date or ms.start_date}",
                'location': ms.location or ms.owner or 'Programme',
                'statusOrPriority': ms.status or 'Planned',
                'sectorsOrFocus': ms.milestone_type or 'Programme Milestone',
                'notes': ms.action_required or '',
                'deadline': ms.deadline_note or '',
                'url': '',
            }
        })

    return cal_items


@require_POST
def update_calendar_date(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    model_type = payload.get('model_type')
    record_id = payload.get('record_id')
    start_str = payload.get('start')
    end_str = payload.get('end')

    if not start_str:
        return JsonResponse({'error': 'Missing start date'}, status=400)

    new_start = date.fromisoformat(start_str[:10])
    new_end = None
    if end_str:
        parsed_end = date.fromisoformat(end_str[:10])
        new_end = max(new_start, parsed_end - timedelta(days=1))

    if model_type == 'external_event':
        obj = get_object_or_404(ExternalEvent, pk=record_id)
        if obj.start_date and obj.end_date and not new_end:
            delta = new_start - obj.start_date
            obj.end_date = obj.end_date + delta
        elif new_end:
            obj.end_date = new_end
        obj.start_date = new_start
        obj.save()
    elif model_type == 'internal_showcase':
        obj = get_object_or_404(InternalShowcase, pk=record_id)
        obj.proposed_date = new_start
        obj.save()
    elif model_type == 'milestone':
        obj = get_object_or_404(ProgrammeMilestone, pk=record_id)
        if obj.start_date and obj.end_date and not new_end:
            delta = new_start - obj.start_date
            obj.end_date = obj.end_date + delta
        elif new_end:
            obj.end_date = new_end
        obj.start_date = new_start
        obj.save()
    else:
        return JsonResponse({'error': 'Unsupported calendar item type'}, status=400)

    return JsonResponse({'ok': True, 'start': new_start.isoformat()})


def calendar_view(request):
    calendar_events = build_calendar_events(
        ExternalEvent.objects.all(),
        InternalShowcase.objects.all(),
        ProgrammeMilestone.objects.all(),
    )
    return render(request, 'showcase/calendar.html', {
        'calendar_events': calendar_events,
    })


def sme_portal_view(request):
    """Read-only schedule portal for SMEs to see which events they attend and when."""
    all_smes = list(SME.objects.all())
    selected_sme_id = request.GET.get('sme', '')
    selected_sme = None
    if selected_sme_id.isdigit():
        selected_sme = next((s for s in all_smes if s.id == int(selected_sme_id)), None)

    scorecards_qs = SMEEventScorecard.objects.select_related('sme', 'event').order_by('event__start_date', 'sme__trading_name')
    if selected_sme:
        scorecards_qs = scorecards_qs.filter(sme=selected_sme)

    assigned_rows = []
    for sc in scorecards_qs:
        ev = sc.event
        assigned_rows.append({
            'sme_name': sc.sme.trading_name,
            'event_name': ev.name,
            'start_date': ev.start_date,
            'end_date': ev.end_date,
            'venue_city': f"{ev.venue} ({ev.city_area})".strip(" ()"),
            'deadline': ev.registration_deadline or 'TBC',
            'recommendation': sc.recommendation,
            'decision': sc.selection_decision,
            'url': ev.primary_url,
            'source': 'Scored / Assigned Event',
        })

    # Include internal showcases matching all SMEs or the selected SME's name/sector
    internal_rows = []
    for item in InternalShowcase.objects.all():
        focus_lower = (item.sme_focus or '').lower()
        applies = False
        if not selected_sme:
            applies = True
        else:
            name_match = selected_sme.trading_name.lower() in focus_lower
            cohort_match = any(k in focus_lower for k in ['all incubated', 'all 5', 'all smes', 'cohort'])
            sector_match = bool(selected_sme.sector) and any(
                word.strip().lower() in focus_lower
                for word in selected_sme.sector.replace('/', ',').split(',')
                if len(word.strip()) > 4
            )
            applies = name_match or cohort_match or sector_match

        if applies:
            internal_rows.append({
                'sme_name': selected_sme.trading_name if selected_sme else 'Cohort / Matching SMEs',
                'event_name': item.title,
                'start_date': item.proposed_date,
                'end_date': item.proposed_date,
                'venue_city': item.location or 'TBC',
                'deadline': item.event_format or 'Internal Activity',
                'recommendation': item.status,
                'decision': item.status,
                'url': '',
                'source': 'Internal Showcase / Hackathon',
            })

    schedule_items = sorted(
        assigned_rows + internal_rows,
        key=lambda r: (r['start_date'] or date(2027, 12, 31), r['event_name'])
    )

    return render(request, 'showcase/sme_portal.html', {
        'smes': all_smes,
        'selected_sme': selected_sme,
        'schedule_items': schedule_items,
        'assigned_count': len(assigned_rows),
        'internal_count': len(internal_rows),
    })


def dashboard(request):
    active_tab = request.GET.get('tab', 'smes')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'seed_suggested_showcases':
            created_count = 0
            for item in SUGGESTED_INTERNAL_SHOWCASES:
                _, created = InternalShowcase.objects.get_or_create(
                    title=item['title'],
                    defaults=item
                )
                if created:
                    created_count += 1
            messages.success(
                request,
                f"Added {created_count} new hackathon & competition showcases to your 2027 calendar."
            )
            return redirect('/?tab=internal')

        elif action == 'save_internal_showcase':
            form = InternalShowcaseForm(request.POST)
            if form.is_valid():
                ev = form.save()
                messages.success(request, f"Internal showcase '{ev.title}' added.")
                return redirect('/?tab=internal')
            messages.error(request, "Please check the internal showcase fields and try again.")
            active_tab = 'internal'

        elif action == 'update_internal_status':
            item = get_object_or_404(InternalShowcase, pk=request.POST.get('record_id'))
            item.status = request.POST.get('status', item.status)
            item.save()
            messages.success(request, f"Updated '{item.title}' to '{item.status}'.")
            return redirect('/?tab=internal')

        elif action == 'save_scorecard':
            existing = SMEEventScorecard.objects.filter(
                sme_id=request.POST.get('sme'),
                event_id=request.POST.get('event')
            ).first()
            form = SMEEventScorecardForm(request.POST, instance=existing)
            if form.is_valid():
                sc = form.save()
                messages.success(
                    request,
                    f"Scorecard saved: {sc.sme.trading_name} @ {sc.event.name} = {sc.total_score}/100 ({sc.recommendation})."
                )
                return redirect('/?tab=scorecards')
            messages.error(request, "Please check the scorecard values and try again.")
            active_tab = 'scorecards'

        elif action == 'update_scorecard_decision':
            sc = get_object_or_404(SMEEventScorecard, pk=request.POST.get('record_id'))
            sc.selection_decision = request.POST.get('selection_decision', sc.selection_decision)
            sc.save()
            messages.success(request, f"Updated {sc.sme.trading_name} decision to '{sc.selection_decision}'.")
            return redirect('/?tab=scorecards')

        elif action == 'save_budget':
            form = EventBudgetForm(request.POST)
            if form.is_valid():
                b = form.save()
                messages.success(
                    request,
                    f"Budget saved for {b.event.name}: Estimated Total R {b.estimated_total:,.2f}."
                )
                return redirect('/?tab=budgets')
            messages.error(request, "Please check the budget fields and try again.")
            active_tab = 'budgets'

        elif action == 'update_budget_status':
            b = get_object_or_404(EventBudget, pk=request.POST.get('record_id'))
            b.approval_status = request.POST.get('approval_status', b.approval_status)
            b.save()
            messages.success(request, f"Budget for {b.event.name} marked '{b.approval_status}'.")
            return redirect('/?tab=budgets')

        elif action == 'save_log':
            form = ParticipationLogForm(request.POST)
            if form.is_valid():
                log = form.save()
                messages.success(
                    request,
                    f"Participation logged for {log.sme.trading_name} at {log.event_name}."
                )
                return redirect('/?tab=logs')
            messages.error(request, "Please check the participation log fields and try again.")
            active_tab = 'logs'

        elif action == 'update_stakeholder':
            st = get_object_or_404(Stakeholder, pk=request.POST.get('stakeholder_id'))
            st.relationship_status = request.POST.get('relationship_status', st.relationship_status)
            st.save()
            messages.success(request, f"Updated {st.organisation} to '{st.relationship_status}'.")
            return redirect('/?tab=stakeholders')

        elif action == 'add_sme_target':
            sme = get_object_or_404(SME, pk=request.POST.get('sme_id'))
            form = SMEStakeholderTargetForm(request.POST)
            if form.is_valid():
                target = form.save(commit=False)
                target.sme = sme
                target.save()
                messages.success(request, f"Added {target.organisation_name} to {sme.trading_name}'s guest list.")
            return redirect('/?tab=smes')

        elif action == 'update_milestone_status':
            m = get_object_or_404(ProgrammeMilestone, pk=request.POST.get('record_id'))
            m.status = request.POST.get('status', m.status)
            m.save()
            messages.success(request, f"Milestone '{m.activity[:40]}...' updated to '{m.status}'.")
            return redirect('/?tab=plan')

        elif action == 'update_risk_status':
            r = get_object_or_404(ProgrammeRisk, pk=request.POST.get('record_id'))
            r.status = request.POST.get('status', r.status)
            r.save()
            messages.success(request, f"Risk status updated to '{r.status}'.")
            return redirect('/?tab=plan')

        elif action == 'delete_record':
            model_type = request.POST.get('model_type')
            record_id = request.POST.get('record_id')
            model_map = {
                'scorecard': (SMEEventScorecard, 'scorecards'),
                'budget': (EventBudget, 'budgets'),
                'log': (ParticipationLog, 'logs'),
                'internal': (InternalShowcase, 'internal'),
            }
            if model_type in model_map:
                model_cls, redirect_tab = model_map[model_type]
                get_object_or_404(model_cls, pk=record_id).delete()
                messages.info(request, "Record deleted.")
                return redirect(f'/?tab={redirect_tab}')

    smes = list(SME.objects.prefetch_related('targeted_stakeholders').all())
    external_events = list(ExternalEvent.objects.all())
    internal_showcases = list(InternalShowcase.objects.all())
    stakeholders = list(Stakeholder.objects.all())
    milestones = list(ProgrammeMilestone.objects.all())
    budgets = list(EventBudget.objects.select_related('sme', 'event').all())
    logs = list(ParticipationLog.objects.select_related('sme').all())

    totals = ParticipationLog.objects.aggregate(
        buyer_leads=Sum('qualified_buyer_leads'),
        confirmed_sales=Sum('confirmed_sales_zar'),
        potential_sales=Sum('potential_sales_zar'),
    )
    total_estimated_budget = sum((b.estimated_total for b in budgets), 0)

    event_cities = sorted({e.city_area for e in external_events if e.city_area})
    event_priorities = sorted({e.priority for e in external_events if e.priority})
    stakeholder_categories = sorted({s.category for s in stakeholders if s.category})
    stakeholder_priorities = sorted({s.priority for s in stakeholders if s.priority})

    cat_counts = Counter(s.category or 'Uncategorized' for s in stakeholders)
    chart_data = {
        'stakeholder_labels': list(cat_counts.keys()),
        'stakeholder_values': list(cat_counts.values()),
        'sme_names': [s.trading_name for s in smes],
        'sme_budgets': [float(sum(b.estimated_total for b in budgets if b.sme_id == s.id)) for s in smes],
        'sme_confirmed_sales': [float(sum(l.confirmed_sales_zar for l in logs if l.sme_id == s.id)) for s in smes],
        'sme_potential_sales': [float(sum(l.potential_sales_zar for l in logs if l.sme_id == s.id)) for s in smes],
    }

    context = {
        'active_tab': active_tab,
        'external_events_count': len(external_events),
        'internal_showcases_count': len(internal_showcases),
        'smes_count': len(smes),
        'stakeholders_count': len(stakeholders),
        'buyer_leads': totals['buyer_leads'] or 0,
        'confirmed_sales': totals['confirmed_sales'] or 0,
        'potential_sales': totals['potential_sales'] or 0,
        'total_estimated_budget': total_estimated_budget,
        'smes': smes,
        'external_events': external_events,
        'internal_showcases': internal_showcases,
        'stakeholders': stakeholders,
        'scorecards': SMEEventScorecard.objects.select_related('sme', 'event').all(),
        'budgets': budgets,
        'logs': logs,
        'monthly_plans': MonthlyPlan.objects.all(),
        'milestones': milestones,
        'risks': ProgrammeRisk.objects.all(),
        'event_cities': event_cities,
        'event_priorities': event_priorities,
        'stakeholder_categories': stakeholder_categories,
        'stakeholder_priorities': stakeholder_priorities,
        'internal_form': InternalShowcaseForm(),
        'scorecard_form': SMEEventScorecardForm(),
        'budget_form': EventBudgetForm(),
        'log_form': ParticipationLogForm(),
        'target_form': SMEStakeholderTargetForm(),
        'status_choices': ['Not approached', 'Contacted', 'Meeting booked', 'Proposal sent', 'Partner confirmed', 'Declined'],
        'internal_status_choices': ['Proposed', 'Confirmed', 'Completed'],
        'decision_choices': ['Pending', 'Approved', 'Deferred', 'Declined'],
        'budget_status_choices': ['Not approved', 'Pending Review', 'Approved'],
        'milestone_status_choices': ['Planned', 'In Progress', 'Completed'],
        'risk_status_choices': ['Open', 'Mitigated', 'Closed'],
        'chart_data': chart_data,
    }
    return render(request, 'showcase/dashboard.html', context)


def export_excel(request):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        smes_data = list(SME.objects.values(
            'trading_name', 'legal_name', 'sector', 'suburb_township',
            'business_stage', 'showcase_readiness', 'priority_events_notes',
            'additional_opportunities', 'potential_customers', 'data_sharing_consent'
        ))
        pd.DataFrame(smes_data).to_excel(writer, sheet_name='Incubated_SMEs', index=False)

        events_data = list(ExternalEvent.objects.values(
            'name', 'start_date', 'end_date', 'city_area', 'venue',
            'event_type', 'relevant_sectors', 'priority', 'registration_deadline',
            'organiser', 'contact_person', 'contact_email', 'phone', 'official_url'
        ))
        pd.DataFrame(events_data).to_excel(writer, sheet_name='External_Events_2027', index=False)

        internal_data = list(InternalShowcase.objects.values(
            'proposed_date', 'title', 'event_format', 'purpose',
            'sme_focus', 'invitees', 'lead_owner', 'status', 'location'
        ))
        pd.DataFrame(internal_data).to_excel(writer, sheet_name='Internal_Showcases', index=False)

        stakeholders_data = list(Stakeholder.objects.values(
            'category', 'organisation', 'physical_address', 'contact_person',
            'email_route', 'phone', 'suggested_ask', 'priority',
            'relationship_status', 'internal_owner', 'source_url'
        ))
        pd.DataFrame(stakeholders_data).to_excel(writer, sheet_name='Stakeholders', index=False)

        scorecard_rows = [
            {
                'SME': sc.sme.trading_name,
                'Event': sc.event.name,
                'Sector_Fit_30': sc.sector_fit,
                'Commercial_Readiness_20': sc.commercial_readiness,
                'Compliance_15': sc.compliance,
                'Delivery_Capacity_15': sc.delivery_capacity,
                'Pitch_Demo_10': sc.pitch_demo,
                'Strategic_Alignment_10': sc.strategic_alignment,
                'Total_Score_100': sc.total_score,
                'Recommendation': sc.recommendation,
                'Decision': sc.selection_decision,
                'Notes_Gaps': sc.notes_gaps,
            }
            for sc in SMEEventScorecard.objects.select_related('sme', 'event').all()
        ]
        pd.DataFrame(scorecard_rows).to_excel(writer, sheet_name='SME_Event_Scorecards', index=False)

        budget_rows = [
            {
                'Event': b.event.name,
                'SME': b.sme.trading_name if b.sme else 'Cohort',
                'Participation_Type': b.participation_type,
                'Subtotal_ZAR': float(b.subtotal),
                'Contingency_Pct': float(b.contingency_pct),
                'Contingency_ZAR': float(b.contingency_value),
                'Estimated_Total_ZAR': float(b.estimated_total),
                'Actual_Spend_ZAR': float(b.actual_spend) if b.actual_spend is not None else None,
                'Variance_ZAR': float(b.variance) if b.variance is not None else None,
                'Approval_Status': b.approval_status,
                'Funding_Source': b.funding_source,
            }
            for b in EventBudget.objects.select_related('sme', 'event').all()
        ]
        pd.DataFrame(budget_rows).to_excel(writer, sheet_name='Event_Budgets_ZAR', index=False)

        logs_data = [
            {
                'Event': l.event_name,
                'Date': l.event_date,
                'SME': l.sme.trading_name,
                'Participation_Type': l.participation_type,
                'Leads_Captured': l.leads_captured,
                'Qualified_Buyer_Leads': l.qualified_buyer_leads,
                'Buyer_Meetings': l.buyer_meetings,
                'Investor_Meetings': l.investor_meetings,
                'Potential_Sales_ZAR': float(l.potential_sales_zar),
                'Confirmed_Sales_ZAR': float(l.confirmed_sales_zar),
                'Follow_Up_Status': l.follow_up_status,
                'Outcome_Next_Action': l.outcome_next_action,
            }
            for l in ParticipationLog.objects.select_related('sme').all()
        ]
        pd.DataFrame(logs_data).to_excel(writer, sheet_name='Participation_Log', index=False)

        pd.DataFrame(list(MonthlyPlan.objects.values())).to_excel(writer, sheet_name='12_Month_Plan', index=False)
        pd.DataFrame(list(ProgrammeMilestone.objects.values())).to_excel(writer, sheet_name='Milestones', index=False)
        pd.DataFrame(list(ProgrammeRisk.objects.values())).to_excel(writer, sheet_name='Risks', index=False)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Gauteng_SME_Programme_2027_Export.xlsx"'
    return response