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
def submit_feedback(request, pk):
    report = get_object_or_404(IssueReport, pk=pk, citizen=request.user)
    if report.status != 'resolved':
        messages.error(request, 'You can only provide feedback for resolved reports.')
        return redirect('report_detail', pk=pk)
        
    if hasattr(report, 'feedback'):
        messages.info(request, 'You have already submitted feedback for this report.')
        return redirect('report_detail', pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
                
            from .models import ReportFeedback
            ReportFeedback.objects.create(
                report=report,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Thank you for your feedback!')
        except (TypeError, ValueError):
            messages.error(request, 'Invalid rating provided.')
            
    return redirect('report_detail', pk=pk)

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

    q = request.GET.get('q', '').strip()
    if q:
        from django.db.models import Q
        recent = my_reports.filter(
            Q(report_id__icontains=q) | 
            Q(location__icontains=q) | 
            Q(category__name__icontains=q) |
            Q(title__icontains=q)
        )
    else:
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

def ai_suggest_category(request):
    text = request.GET.get('text', '').lower()
    if not text:
        return JsonResponse({'category_id': None})
    
    mapping = {
        'waste': ['garbage', 'trash', 'waste', 'dustbin', 'cleaning', 'dump'],
        'road': ['pothole', 'road', 'asphalt', 'cracks', 'repair', 'broken'],
        'street light': ['light', 'dark', 'bulb', 'street light', 'pole'],
        'water': ['water', 'pipe', 'leak', 'drinking', 'supply', 'tap'],
        'drainage': ['drain', 'sewage', 'clog', 'overflow', 'smell', 'block', 'gutter'],
        'transport': ['bus', 'stand', 'station', 'transport'],
    }
    
    best_match = None
    max_score = 0
    
    for cat_name, keywords in mapping.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > max_score:
            max_score = score
            best_match = cat_name
            
    if best_match:
        category = IssueCategory.objects.filter(name__icontains=best_match).first()
        if category:
            return JsonResponse({'category_id': category.id, 'category_name': category.name})
            
    return JsonResponse({'category_id': None})

def chatbot_response(request):
    import re
    from .models import IssueReport
    
    text = request.GET.get('text', '').strip()
    if not text:
        return JsonResponse({'reply': 'Please ask a question or provide your Report ID.'})
        
    # Check if the user provided a Report ID like TCC2024XXXXXX
    match = re.search(r'TCC\d+', text, re.IGNORECASE)
    if match:
        report_id = match.group(0).upper()
        report = IssueReport.objects.filter(report_id=report_id).first()
        if report:
            status_map = {
                'pending': 'Pending Review',
                'acknowledged': 'Acknowledged',
                'in_progress': 'In Progress',
                'resolved': 'Resolved',
                'closed': 'Closed',
                'rejected': 'Rejected'
            }
            status = status_map.get(report.status, report.status)
            return JsonResponse({'reply': f'Report {report_id} "{report.title}" is currently: **{status}**.'})
        else:
            return JsonResponse({'reply': f'Sorry, I could not find a report with ID {report_id}.'})
            
    text_lower = text.lower()
    if 'hello' in text_lower or 'hi' in text_lower:
        return JsonResponse({'reply': 'Hello! I am the Tumakuru Civic Bot. How can I help you today? You can ask me about the status of your report by typing its ID.'})
    if 'point' in text_lower or 'reward' in text_lower:
        return JsonResponse({'reply': 'You earn 5 points for every valid report. Reach 100 points to get a Best Citizen Certificate!'})
        
    return JsonResponse({'reply': 'I am a simple bot. To check your report status, please provide the Report ID (e.g., TCC2024123456). For other issues, please contact the helpline.'})

@login_required
def analytics_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied. You must be an admin to view analytics.')
        return redirect('home')
        
    # Status distribution
    status_counts = IssueReport.objects.values('status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in status_counts:
        status_labels.append(item['status'].title().replace('_', ' '))
        status_data.append(item['count'])
        
    # Categories distribution
    category_counts = IssueReport.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
    cat_labels = [c['category__name'] for c in category_counts if c['category__name']]
    cat_data = [c['count'] for c in category_counts if c['category__name']]
    
    # Simple Monthly Trends (assuming current year)
    import datetime
    current_year = datetime.datetime.now().year
    monthly_data = []
    for m in range(1, 13):
        monthly_data.append(IssueReport.objects.filter(created_at__year=current_year, created_at__month=m).count())
        
    context = {
        'status_labels': status_labels,
        'status_data': status_data,
        'cat_labels': cat_labels,
        'cat_data': cat_data,
        'monthly_data': monthly_data,
        'year': current_year,
    }
    
    return render(request, 'reports/analytics.html', context)

def volunteer_list(request):
    from .models import VolunteerTask, VolunteerLog
    tasks = VolunteerTask.objects.filter(is_active=True).order_by('-created_at')
    user_tasks = []
    if request.user.is_authenticated:
        user_tasks = VolunteerLog.objects.filter(citizen=request.user).values_list('task_id', flat=True)
        
    return render(request, 'reports/volunteer_list.html', {'tasks': tasks, 'user_tasks': user_tasks})

@login_required
def volunteer_signup(request, task_id):
    from .models import VolunteerTask, VolunteerLog
    task = get_object_or_404(VolunteerTask, id=task_id)
    log, created = VolunteerLog.objects.get_or_create(task=task, citizen=request.user)
    if created:
        messages.success(request, f'Thank you for volunteering for "{task.title}". You will earn {task.points_reward} points upon completion.')
    else:
        messages.info(request, f'You are already signed up for "{task.title}".')
    return redirect('volunteer_list')

def ward_statistics(request):
    """Public page showing bar chart of issues per ward."""
    # Get total issues per ward
    ward_counts = IssueReport.objects.values('ward_number').annotate(
        total=Count('id'),
        resolved=Count('id', filter=Q(status='resolved')),
        in_progress=Count('id', filter=Q(status__in=['in_progress', 'acknowledged'])),
        pending=Count('id', filter=Q(status='pending'))
    ).order_by('ward_number')
    
    # We want to format this for Chart.js
    labels = []
    total_data = []
    resolved_data = []
    
    # Pre-populate all 35 wards
    ward_dict = {str(i): {'total': 0, 'resolved': 0} for i in range(1, 36)}
    
    for item in ward_counts:
        w = str(item['ward_number'])
        if w in ward_dict:
            ward_dict[w]['total'] = item['total']
            ward_dict[w]['resolved'] = item['resolved']
            
    for i in range(1, 36):
        labels.append(f"Ward {i}")
        total_data.append(ward_dict[str(i)]['total'])
        resolved_data.append(ward_dict[str(i)]['resolved'])
        
    context = {
        'labels': labels,
        'total_data': total_data,
        'resolved_data': resolved_data,
        'total_issues': sum(total_data),
        'total_resolved': sum(resolved_data),
    }
    
    return render(request, 'reports/statistics.html', context)

