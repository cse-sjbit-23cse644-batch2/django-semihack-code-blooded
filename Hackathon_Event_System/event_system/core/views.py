import io
import os
import random
import json
import qrcode

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from .models import Event, Participant
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        return redirect('admin_login')
    return _wrapped_view

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def check_auth(request):
    return request.user.is_staff or 'participant_id' in request.session

def student_logout(request):
    from django.contrib.auth import logout as auth_logout
    if 'participant_id' in request.session:
        del request.session['participant_id']
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect('home')

def home(request):
    events = Event.objects.all()
    total_participants = Participant.objects.count()
    attended = Participant.objects.filter(attended=True).count()
    certificates_issued = Participant.objects.filter(attended=True, feedback_submitted=True).count()
    context = {
        'events': events,
        'total_participants': total_participants,
        'attended': attended,
        'certificates_issued': certificates_issued,
    }
    return render(request, 'home.html', context)

def login_view(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id', '').strip()
        email = request.POST.get('email', '').strip().lower()
        
        participant = Participant.objects.filter(student_id=student_id, email=email).first()
        
        if participant:
            # Login successful, set session and redirect
            request.session['participant_id'] = participant.id
            return redirect('certificate', participant_id=participant.id)
        else:
            return render(request, 'login.html', {'error': 'Invalid Student ID or Email address. Have you registered?'})
            
    return render(request, 'login.html')

def admin_login(request):
    from django.contrib.auth import authenticate, login as auth_login
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid Admin credentials or not authorized.'})
            
    return render(request, 'admin_login.html')

def register(request):
    events = Event.objects.all()

    if request.method == 'POST':
        student_id = request.POST.get('student_id', '').strip()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        event_id = request.POST.get('event')

        errors = {}
        if not student_id:
            errors['student_id'] = 'Student ID is required.'
        if not name:
            errors['name'] = 'Name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        if not event_id:
            errors['event'] = 'Please select an event.'

        if not errors:
            if Participant.objects.filter(student_id=student_id).exists():
                errors['student_id'] = 'This Student ID is already registered.'
            elif Participant.objects.filter(email=email).exists():
                errors['email'] = 'This email is already registered. Each participant can only register once.'

        if errors:
            return render(request, 'register.html', {'events': events, 'errors': errors, 'form_data': request.POST})

        event = get_object_or_404(Event, pk=event_id)
        participant = Participant.objects.create(student_id=student_id, name=name, email=email, event=event)

        # Generate QR code
        # Generate QR code using local IP so mobile scanning works
        local_ip = get_local_ip()
        attendance_url = f"http://{local_ip}:8000/attendance/{participant.id}/"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(attendance_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f'qr_{participant.id}.png')
        img.save(qr_path)
        participant.qr_code = f'qr_codes/qr_{participant.id}.png'
        participant.save()

        request.session['participant_id'] = participant.id

        return redirect('success', participant_id=participant.id)

    return render(request, 'register.html', {'events': events})


def success(request, participant_id):
    participant = get_object_or_404(Participant, pk=participant_id)
    return render(request, 'success.html', {'participant': participant})


@admin_required
def attendance(request, participant_id):
    participant = get_object_or_404(Participant, pk=participant_id)

    if participant.attended:
        message = 'already_marked'
    else:
        participant.attended = True
        participant.save()
        message = 'marked'

    return render(request, 'attendance.html', {'participant': participant, 'message': message})


def certificate(request, participant_id):
    participant = get_object_or_404(Participant, pk=participant_id)

    if not participant.attended:

        return HttpResponse(
            "Attendance required"
        )

    if not participant.feedback_submitted:

        return redirect(
            'feedback',
            participant_id=participant.id
        )

    return render(request, 'certificate.html', {'participant': participant})


def draw_certificate_border(canvas, doc):
    canvas.saveState()
    
    # Outer border
    canvas.setStrokeColor(colors.HexColor('#1a1a2e'))
    canvas.setLineWidth(6)
    canvas.rect(0.8 * inch, 0.8 * inch, landscape(A4)[0] - 1.6 * inch, landscape(A4)[1] - 1.6 * inch)
    
    # Inner border
    canvas.setStrokeColor(colors.HexColor('#4a4a8a'))
    canvas.setLineWidth(2)
    canvas.rect(0.9 * inch, 0.9 * inch, landscape(A4)[0] - 1.8 * inch, landscape(A4)[1] - 1.8 * inch)
    
    # Corner decorations
    canvas.setStrokeColor(colors.HexColor('#FFD700'))
    canvas.setLineWidth(3)
    
    d = 0.5 * inch
    w = landscape(A4)[0]
    h = landscape(A4)[1]
    
    # Bottom Left
    canvas.line(0.7 * inch, 0.9 * inch + d, 0.7 * inch, 0.7 * inch)
    canvas.line(0.7 * inch, 0.7 * inch, 0.9 * inch + d, 0.7 * inch)
    
    # Bottom Right
    canvas.line(w - 0.7 * inch, 0.9 * inch + d, w - 0.7 * inch, 0.7 * inch)
    canvas.line(w - 0.7 * inch, 0.7 * inch, w - (0.9 * inch + d), 0.7 * inch)
    
    # Top Left
    canvas.line(0.7 * inch, h - (0.9 * inch + d), 0.7 * inch, h - 0.7 * inch)
    canvas.line(0.7 * inch, h - 0.7 * inch, 0.9 * inch + d, h - 0.7 * inch)
    
    # Top Right
    canvas.line(w - 0.7 * inch, h - (0.9 * inch + d), w - 0.7 * inch, h - 0.7 * inch)
    # Draw Team Name at Top Right
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(colors.HexColor('#1a1a2e'))
    canvas.drawRightString(w - 1.2 * inch, h - 1.2 * inch, "Event Hub")
    
    canvas.restoreState()

def download_certificate(request, participant_id):
    participant = get_object_or_404(Participant, pk=participant_id)

    if not participant.attended or not participant.feedback_submitted:
        raise Http404("Certificate not available.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * inch,
        leftMargin=1.5 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Title'],
        fontSize=38,
        leading=46,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=15,
        leading=20,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Normal'],
        fontSize=34,
        leading=42,
        textColor=colors.HexColor('#4a4a8a'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    event_style = ParagraphStyle(
        'EventStyle',
        parent=styles['Normal'],
        fontSize=22,
        leading=28,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=25,
        alignment=TA_CENTER,
        fontName='Helvetica-BoldOblique',
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#888888'),
        spaceAfter=2,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    level_colors = {'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
    level_color = level_colors.get(participant.level, '#888888')

    story = [
        Spacer(1, 0.1 * inch),
        Paragraph("CERTIFICATE OF PARTICIPATION", title_style),
        HRFlowable(width="80%", thickness=1.5, color=colors.HexColor('#4a4a8a'), spaceBefore=5, spaceAfter=15),
        Paragraph("This is proudly presented to", body_style),
        Paragraph(participant.name, name_style),
        Paragraph("for successfully participating and demonstrating excellence in", body_style),
        Paragraph(participant.event.name, event_style),
    ]

    # Score & level table
    if participant.level:
        level_para = Paragraph(
            f'<font color="{level_color}"><b>{participant.level}</b></font>',
            ParagraphStyle('LP', fontSize=16, leading=20, alignment=TA_CENTER, fontName='Helvetica-Bold')
        )
        score_para = Paragraph(f'Score: <b>{participant.score}/100</b>', ParagraphStyle('SP', fontSize=14, leading=18, alignment=TA_CENTER, fontName='Helvetica', textColor=colors.HexColor('#333333')))
        table_data = [[score_para, level_para]]
        table = Table(table_data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEAFTER', (0, 0), (0, -1), 1, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
    else:
        score_para = Paragraph(f'Score: <b>{participant.score}/100</b>', ParagraphStyle('SP', fontSize=16, leading=20, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=colors.HexColor('#333333')))
        table_data = [[score_para]]
        table = Table(table_data, colWidths=[6 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
    
    # Wrap table in another table for border
    outer_table = Table([[table]], colWidths=[6.5 * inch])
    outer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#eeeeee')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
    ]))

    story.append(outer_table)
    story.append(Spacer(1, 0.25 * inch))
    
    story.append(Paragraph(f'Certificate ID: {participant.certificate_id}', meta_style))
    story.append(Paragraph(f'Verify at: {request.build_absolute_uri("/verify/")}{participant.certificate_id}/', meta_style))

    doc.build(story, onFirstPage=draw_certificate_border, onLaterPages=draw_certificate_border)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    safe_name = participant.name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{safe_name}.pdf"'
    return response


def verify(request, certificate_id=None):
    if not check_auth(request):
        return redirect('home')

    # When user submits form
    if request.method == "POST":

        cert_id = request.POST.get('certificate_id', '').strip()

        # Remove full URL if pasted
        if "verify/" in cert_id:
            cert_id = cert_id.split("verify/")[-1]

        return redirect('verify_id', certificate_id=cert_id)

    # When URL has certificate ID
    if certificate_id:

        try:
            participant = Participant.objects.get(
                certificate_id=certificate_id
            )

            valid = participant.attended

            return render(
                request,
                'verify.html',
                {
                    'participant': participant,
                    'valid': valid,
                    'searched': True
                }
            )

        except (Participant.DoesNotExist, ValidationError, ValueError):

            return render(
                request,
                'verify.html',
                {
                    'valid': False,
                    'searched': True,
                    'cert_id': certificate_id
                }
            )

    return render(request, 'verify.html')
def leaderboard(request):
    if not check_auth(request):
        return redirect('home')

    participants = (
        Participant.objects
        .filter(score__isnull=False)
        .order_by('-score')[:10]
    )

    return render(
        request,
        'leaderboard.html',
        {'participants': participants}
    )
def leaderboard_pdf(request):
    if not check_auth(request):
        return redirect('home')

    participants = (
        Participant.objects
        .filter(score__isnull=False)
        .order_by('-score')
    )

    data = [["Rank", "Name", "Event", "Score"]]

    rank = 1

    for p in participants:

        data.append([
            rank,
            p.name,
            p.event.name,
            p.score
        ])

        rank += 1

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = 'attachment; filename="leaderboard.pdf"'

    doc = SimpleDocTemplate(response)

    table = Table(data)

    doc.build([table])

    return response
@admin_required
def scan_qr(request):
    return render(request, 'scan.html')

def feedback(request, participant_id):

    participant = Participant.objects.get(id=participant_id)

    if request.method == "POST":

        participant.feedback_rating = request.POST.get('rating')
        participant.feedback_comments = request.POST.get('comments')
        participant.feedback_submitted = True
        participant.save()

        return redirect('certificate', participant_id=participant.id)

    return render(
        request,
        'feedback.html',
        {'participant': participant}
    )

@admin_required
def admin_dashboard(request):
    participants = Participant.objects.all().order_by('-registered_at')
    return render(request, 'admin_dashboard.html', {'participants': participants})

@admin_required
def toggle_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            participant_id = data.get('id')
            participant = Participant.objects.get(id=participant_id)
            
            participant.attended = not participant.attended
            participant.save()
            
            return JsonResponse({'success': True, 'attended': participant.attended, 'score': participant.score})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@admin_required
def update_score(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            participant_id = data.get('id')
            score_val = data.get('score')
            participant = Participant.objects.get(id=participant_id)
            
            if score_val == '':
                participant.score = None
            else:
                participant.score = int(score_val)
            
            participant.save()
            return JsonResponse({'success': True, 'score': participant.score})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})