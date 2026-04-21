from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Q
from django.conf import settings
from django.utils import timezone
from .models import IssueReport, IssueCategory, IssueComment, IssueUpvote
from .forms import IssueReportForm, IssueCommentForm
from accounts.models import CitizenProfile, CitizenCertificate
from .utils import generate_certificate_number, generate_certificate_pdf
from .notifications import send_report_thankyou, send_certificate_notification


def home(request):
    stats = {
        'total_reports': IssueReport.objects.count(),
        'resolved': IssueReport.objects.filter(status='resolved').count(),
        'in_progress': IssueReport.objects.filter(status='in_progress').count(),
        'pending': IssueReport.objects.filter(status='pending').count(),
    }
    recent_reports = IssueReport.objects.select_related('citizen', 'category').order_by('-created_at')[:6]
    categories = IssueCategory.objects.filter(is_active=True).annotate(report_count=Count('issuereport'))
    top_citizens = CitizenProfile.objects.select_related('user').order_by('-points')[:5]

    emergency_numbers = [
        {'label': 'National Emergency', 'number': '112', 'icon': 'fas fa-sos'},
        {'label': 'Ambulance',          'number': '108', 'icon': 'fas fa-ambulance'},
        {'label': 'Police',             'number': '100', 'icon': 'fas fa-shield-alt'},
        {'label': 'Fire Service',       'number': '101', 'icon': 'fas fa-fire'},
        {'label': 'BESCOM Power',       'number': '1912', 'icon': 'fas fa-bolt'},
        {'label': 'Water Supply',       'number': '1800-425-0006', 'icon': 'fas fa-tint'},
    ]

    return render(request, 'home.html', {
        'stats': stats,
        'recent_reports': recent_reports,
        'categories': categories,
        'top_citizens': top_citizens,
        'emergency_numbers': emergency_numbers,
    })


@login_required
def dashboard(request):
    profile = request.user.profile
    my_reports = IssueReport.objects.filter(citizen=request.user).order_by('-created_at')

    stats = {
        'total': my_reports.count(),
        'pending': my_reports.filter(status='pending').count(),
        'in_progress': my_reports.filter(status__in=['acknowledged', 'in_progress']).count(),
        'resolved': my_reports.filter(status='resolved').count(),
        'points': profile.points,
        'certificates': profile.certificates_earned(),
    }

    recent = my_reports[:5]
    certificates = profile.certificates.all()
    progress = profile.progress_percentage
    points_needed = settings.POINTS_FOR_CERTIFICATE - (profile.points % settings.POINTS_FOR_CERTIFICATE)
    if points_needed == settings.POINTS_FOR_CERTIFICATE:
        points_needed = 0

    return render(request, 'reports/dashboard.html', {
        'stats': stats,
        'recent_reports': recent,
        'certificates': certificates,
        'progress': progress,
        'points_needed': points_needed,
        'profile': profile,
        'points_per_report': settings.POINTS_PER_REPORT,
        'points_threshold': settings.POINTS_FOR_CERTIFICATE,
    })


@login_required
def submit_report(request):
    if request.method == 'POST':
        form = IssueReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.citizen = request.user
            report.save()

            # Award points
            profile = request.user.profile
            profile.points += settings.POINTS_PER_REPORT
            profile.total_reports += 1
            report.points_awarded = settings.POINTS_PER_REPORT
            report.is_points_given = True
            report.save()

            # Check for certificate milestone
            old_points = profile.points - settings.POINTS_PER_REPORT
            new_points = profile.points
            threshold = settings.POINTS_FOR_CERTIFICATE

            old_milestones = old_points // threshold
            new_milestones = new_points // threshold

            profile.save()

            if new_milestones > old_milestones:
                milestone = new_milestones * threshold
                cert_number = generate_certificate_number(profile.id, milestone)
                certificate = CitizenCertificate.objects.create(
                    citizen=profile,
                    certificate_number=cert_number,
                    points_at_issue=new_points,
                    milestone=milestone,
                )
                # 🏆 Send certificate congratulations email + SMS
                send_certificate_notification(profile, certificate)

                messages.success(
                    request,
                    f'🎉 Congratulations! You have earned the Best Citizen Certificate! '
                    f'Certificate No: {cert_number}'
                )
                return redirect('certificate_detail', pk=certificate.pk)

            # ✅ Send thank-you email + SMS after every report
            send_report_thankyou(report, profile)

            messages.success(
                request,
                f'✅ Issue reported successfully! Report ID: {report.report_id}. '
                f'You earned {settings.POINTS_PER_REPORT} civic points! '
                f'A thank-you message has been sent to your email & mobile.'
            )
            return redirect('report_detail', pk=report.pk)
    else:
        form = IssueReportForm()
        if request.user.profile.ward_number:
            form.fields['ward_number'].initial = request.user.profile.ward_number

    return render(request, 'reports/report_form.html', {'form': form})


def report_list(request):
    reports = IssueReport.objects.select_related('citizen', 'category').all()

    # Filters
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    ward = request.GET.get('ward', '')
    q = request.GET.get('q', '')

    if status:
        reports = reports.filter(status=status)
    if category:
        reports = reports.filter(category__id=category)
    if ward:
        reports = reports.filter(ward_number=ward)
    if q:
        reports = reports.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(report_id__icontains=q))

    categories = IssueCategory.objects.filter(is_active=True)
    wards = [(str(i), f"Ward {i}") for i in range(1, 36)]

    return render(request, 'reports/report_list.html', {
        'reports': reports,
        'categories': categories,
        'wards': wards,
        'current_status': status,
        'current_category': category,
        'current_ward': ward,
        'query': q,
        'status_choices': IssueReport.STATUS_CHOICES,
    })


def report_detail(request, pk):
    report = get_object_or_404(IssueReport.objects.select_related('citizen', 'category'), pk=pk)
    comments = report.comments.select_related('author').all()
    comment_form = IssueCommentForm()
    user_upvoted = False

    if request.user.is_authenticated:
        user_upvoted = IssueUpvote.objects.filter(issue=report, citizen=request.user).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = IssueCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.issue = report
            comment.author = request.user
            comment.is_official = request.user.is_staff
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('report_detail', pk=pk)

    return render(request, 'reports/report_detail.html', {
        'report': report,
        'comments': comments,
        'comment_form': comment_form,
        'user_upvoted': user_upvoted,
    })


@login_required
def upvote_report(request, pk):
    report = get_object_or_404(IssueReport, pk=pk)
    upvote, created = IssueUpvote.objects.get_or_create(issue=report, citizen=request.user)
    if created:
        report.upvotes += 1
        report.save()
    return JsonResponse({'upvotes': report.upvotes, 'upvoted': created})


def leaderboard(request):
    citizens = CitizenProfile.objects.select_related('user').filter(
        total_reports__gt=0
    ).order_by('-points')[:50]

    return render(request, 'reports/leaderboard.html', {
        'citizens': citizens,
        'threshold': settings.POINTS_FOR_CERTIFICATE,
    })


@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(CitizenCertificate, pk=pk, citizen=request.user.profile)
    return render(request, 'reports/certificate.html', {'certificate': certificate})


@login_required
def download_certificate(request, pk):
    certificate = get_object_or_404(CitizenCertificate, pk=pk, citizen=request.user.profile)
    profile = request.user.profile

    buffer = generate_certificate_pdf(profile, certificate)

    if buffer:
        certificate.is_downloaded = True
        certificate.save()
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="BestCitizen_{certificate.certificate_number}.pdf"'
        return response
    else:
        messages.error(request, 'Could not generate PDF. Please install reportlab: pip install reportlab')
        return redirect('certificate_detail', pk=pk)


@login_required
def my_reports(request):
    reports = IssueReport.objects.filter(citizen=request.user).order_by('-created_at')
    return render(request, 'reports/my_reports.html', {'reports': reports})


def emergency_contacts(request):
    """Emergency contacts directory for Tumakuru City."""

    police_contacts = [
        {'name': 'National Emergency Helpline', 'desc': 'Police · Fire · Ambulance — All in one', 'number': '112', 'icon': 'fas fa-sos', 'color': '#C0392B', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Police Control Room', 'desc': 'Tumakuru District Police Control Room', 'number': '100', 'icon': 'fas fa-shield-alt', 'color': '#1A5276', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Tumakuru SP Office', 'desc': 'Superintendent of Police, Tumakuru', 'number': '0816-2272700', 'icon': 'fas fa-user-shield', 'color': '#1F618D', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Tumakuru City Police', 'desc': 'City Police Station, Tumakuru', 'number': '0816-2272300', 'icon': 'fas fa-building', 'color': '#2874A6', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Anti-Corruption Bureau', 'desc': 'Report corruption and bribery', 'number': '1064', 'icon': 'fas fa-balance-scale', 'color': '#6C3483', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Cyber Crime Helpline', 'desc': 'Online fraud, cyber abuse, hacking', 'number': '1930', 'icon': 'fas fa-laptop', 'color': '#1A5276', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    medical_contacts = [
        {'name': 'Ambulance (CATS)', 'desc': 'Centralised Accident & Trauma Services', 'number': '108', 'icon': 'fas fa-ambulance', 'color': '#C0392B', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Health Helpline', 'desc': 'Karnataka Health Department', 'number': '104', 'icon': 'fas fa-heartbeat', 'color': '#E74C3C', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'District Hospital Tumakuru', 'desc': 'B.H. Road, Tumakuru — General & Emergency', 'number': '0816-2272326', 'icon': 'fas fa-hospital', 'color': '#C0392B', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'SSIMC Hospital', 'desc': 'SS Institute of Medical Sciences, Tumakuru', 'number': '0816-2282222', 'icon': 'fas fa-hospital-alt', 'color': '#E74C3C', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Blood Bank — District Hospital', 'desc': 'Emergency blood requirement', 'number': '0816-2272326', 'icon': 'fas fa-tint', 'color': '#922B21', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Mental Health Helpline', 'desc': 'NIMHANS — Suicide & mental health crisis', 'number': '080-46110007', 'icon': 'fas fa-brain', 'color': '#7D3C98', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'iCall Mental Health', 'desc': 'Free counselling helpline', 'number': '9152987821', 'icon': 'fas fa-comment-medical', 'color': '#8E44AD', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'COVID / Epidemic Helpline', 'desc': 'Karnataka State Health Department', 'number': '104', 'icon': 'fas fa-virus', 'color': '#117A65', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    fire_contacts = [
        {'name': 'Fire Emergency', 'desc': 'National fire emergency number', 'number': '101', 'icon': 'fas fa-fire', 'color': '#E67E22', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Tumakuru Fire Station', 'desc': 'Main Fire Station, B.H. Road, Tumakuru', 'number': '0816-2272101', 'icon': 'fas fa-fire-extinguisher', 'color': '#D35400', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Fire & Emergency Services', 'desc': 'Karnataka State Fire & Emergency Services', 'number': '0816-2271101', 'icon': 'fas fa-truck', 'color': '#CA6F1E', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    bescom_contacts = [
        {'name': 'BESCOM 24×7 Helpline', 'desc': 'Power failure, transformer issues, electrical hazard', 'number': '1912', 'icon': 'fas fa-bolt', 'color': '#F39C12', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'BESCOM Tumakuru Division', 'desc': 'Divisional Office — Tumakuru', 'number': '0816-2272933', 'icon': 'fas fa-plug', 'color': '#D4AC0D', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'BESCOM Customer Care', 'desc': 'Billing issues, new connections', 'number': '1800-425-9181', 'icon': 'fas fa-headset', 'color': '#F1C40F', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Electrical Accident Helpline', 'desc': 'Report live wires, electrical accidents', 'number': '1912', 'icon': 'fas fa-exclamation-triangle', 'color': '#E67E22', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    traffic_contacts = [
        {'name': 'Traffic Control Room', 'desc': 'Tumakuru City Traffic Police', 'number': '0816-2220100', 'icon': 'fas fa-traffic-light', 'color': '#2980B9', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Road Accident Helpline', 'desc': 'National Highways & road accident response', 'number': '1073', 'icon': 'fas fa-car-crash', 'color': '#E74C3C', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Traffic Complaint — TCC', 'desc': 'Illegal parking, signal issues, road encroachments', 'number': '0816-2272300', 'icon': 'fas fa-parking', 'color': '#1A5276', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'NHAI Helpline', 'desc': 'National Highway issues & accidents', 'number': '1033', 'icon': 'fas fa-road', 'color': '#117A65', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    forest_contacts = [
        {'name': 'Forest / Poaching Helpline', 'desc': 'Report poaching, illegal logging, forest fires', 'number': '1916', 'icon': 'fas fa-tree', 'color': '#1E8449', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Karnataka Forest Dept', 'desc': 'District Forest Office, Tumakuru', 'number': '0816-2272546', 'icon': 'fas fa-leaf', 'color': '#27AE60', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Wildlife Crime Helpline', 'desc': 'Stray wild animals, wildlife trafficking', 'number': '1800-425-0061', 'icon': 'fas fa-paw', 'color': '#117A65', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Animal Helpline', 'desc': 'Stray dog attacks, animal cruelty', 'number': '1962', 'icon': 'fas fa-dog', 'color': '#1E8449', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    water_contacts = [
        {'name': 'TCC Water Supply Helpline', 'desc': 'Water shortage, leakage, billing — Toll Free', 'number': '1800-425-0006', 'icon': 'fas fa-tint', 'color': '#2471A3', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'TCC Main Office', 'desc': 'Tumakuru City Corporation, B.H. Road', 'number': '0816-2272233', 'icon': 'fas fa-city', 'color': '#1F618D', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Drainage & Sanitation', 'desc': 'Blocked drains, sewage overflow, flooding', 'number': '0816-2272445', 'icon': 'fas fa-water', 'color': '#2E86C1', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Solid Waste Management', 'desc': 'Garbage collection, illegal dumping complaints', 'number': '0816-2272500', 'icon': 'fas fa-trash-alt', 'color': '#27AE60', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
    ]

    govt_contacts = [
        {'name': 'District Collector Office', 'desc': 'Revenue, disaster management, welfare', 'number': '0816-2272020', 'icon': 'fas fa-landmark', 'color': '#1A5276', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Zilla Panchayat Tumakuru', 'desc': 'Rural development, gram panchayat services', 'number': '0816-2272630', 'icon': 'fas fa-sitemap', 'color': '#117A65', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Ration / Food Dept', 'desc': 'PDS — Ration card, food supply grievances', 'number': '1967', 'icon': 'fas fa-shopping-basket', 'color': '#E67E22', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Labour Department', 'desc': 'Labour issues, wage disputes, welfare', 'number': '155214', 'icon': 'fas fa-hard-hat', 'color': '#D35400', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Electricity Ombudsman', 'desc': 'Unresolved BESCOM consumer complaints', 'number': '080-23320088', 'icon': 'fas fa-gavel', 'color': '#F39C12', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Consumer Helpline', 'desc': 'Consumer fraud, product complaints', 'number': '1915', 'icon': 'fas fa-balance-scale', 'color': '#6C3483', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'ASI — Archaeology Survey', 'desc': 'Heritage monument damage / encroachment', 'number': '011-23018174', 'icon': 'fas fa-monument', 'color': '#784212', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Disaster Management', 'desc': 'Karnataka SDMA — Flood, earthquake, disaster', 'number': '1070', 'icon': 'fas fa-house-damage', 'color': '#C0392B', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    social_contacts = [
        {'name': 'Women Helpline', 'desc': 'Domestic violence, harassment, safety', 'number': '181', 'icon': 'fas fa-female', 'color': '#C0392B', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Child Helpline', 'desc': 'Child abuse, missing children, child labour', 'number': '1098', 'icon': 'fas fa-child', 'color': '#8E44AD', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Senior Citizen Helpline', 'desc': 'Elder abuse, pension, welfare', 'number': '14567', 'icon': 'fas fa-user-tie', 'color': '#7D6608', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Anti-Human Trafficking', 'desc': 'Report trafficking, forced labour', 'number': '1800-419-8588', 'icon': 'fas fa-hands', 'color': '#6C3483', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Suicide Prevention', 'desc': 'iCall / NIMHANS crisis support', 'number': '9152987821', 'icon': 'fas fa-heart', 'color': '#E74C3C', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Drug Abuse Helpline', 'desc': 'MANAS — drug, alcohol de-addiction', 'number': '14446', 'icon': 'fas fa-pills', 'color': '#117A65', 'avail': '24×7', 'avail_class': 'avail-24'},
        {'name': 'Disability Helpline', 'desc': 'Divyang welfare and assistance', 'number': '1800-111-100', 'icon': 'fas fa-wheelchair', 'color': '#2471A3', 'avail': 'Office Hours', 'avail_class': 'avail-day'},
        {'name': 'Karnataka CM Helpline', 'desc': 'Chief Minister Helpline — state grievances', 'number': '1902', 'icon': 'fas fa-star', 'color': '#1A5276', 'avail': '24×7', 'avail_class': 'avail-24'},
    ]

    return render(request, 'emergency.html', {
        'police_contacts': police_contacts,
        'medical_contacts': medical_contacts,
        'fire_contacts': fire_contacts,
        'bescom_contacts': bescom_contacts,
        'traffic_contacts': traffic_contacts,
        'forest_contacts': forest_contacts,
        'water_contacts': water_contacts,
        'govt_contacts': govt_contacts,
        'social_contacts': social_contacts,
    })
