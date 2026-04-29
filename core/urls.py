from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('logout/', views.student_logout, name='logout'),
    path('success/<int:participant_id>/', views.success, name='success'),
    path('attendance/<int:participant_id>/', views.attendance, name='attendance'),
    path('certificate/<int:participant_id>/', views.certificate, name='certificate'),
    path('certificate/<int:participant_id>/download/', views.download_certificate, name='download_certificate'),
    path('verify/', views.verify, name='verify'),
    path('verify/<str:certificate_id>/', views.verify, name='verify_id'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('leaderboard/pdf/',views.leaderboard_pdf,name='leaderboard_pdf'),
    path('scan/',views.scan_qr,name='scan_qr'),
    path('feedback/<int:participant_id>/',views.feedback,name='feedback'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('ajax/toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),
    path('ajax/update-score/', views.update_score, name='update_score'),
    path('ajax/verify-payment/', views.verify_payment, name='verify_payment'),
]
