from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import api_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('login/select-method/', views.select_2fa_method, name='select_2fa_method'),
    path('login/verify-2fa/', views.verify_2fa_otp, name='verify_2fa_otp'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Registration Flow
    path('register/', views.register, name='register'),
    path('register/shipper/', views.register_shipper, name='register_shipper'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('register/verify/', views.verify_registration, name='verify_registration'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset_form.html',
        email_template_name='core/emails/password_reset_email.txt',
        html_email_template_name='core/emails/password_reset_email.html',
        subject_template_name='core/emails/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan-qr/', views.scan_qr_view, name='scan_qr'),
    path('shipment-request/', views.shipment_request, name='shipment_request'),
    path('parcel/<int:parcel_id>/edit/', views.edit_parcel, name='edit_parcel'),
    path('parcel/<int:parcel_id>/cancel/', views.cancel_parcel, name='cancel_parcel'),
    path('track/', views.track_parcel, name='track'),
    path('accept-parcel/<int:parcel_id>/', views.accept_parcel, name='accept_parcel'),
    path('update-status/<int:parcel_id>/', views.update_status, name='update_status'),
    path('rate-driver/<int:parcel_id>/', views.rate_driver, name='rate_driver'),
    path('parcel/<int:parcel_id>/label/', views.generate_parcel_label, name='generate_parcel_label'),
    path('parcel/<int:parcel_id>/invoice/', views.generate_invoice, name='generate_invoice'),
    path('initiate-payment/<int:parcel_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    
    path('article/1/', views.article_detail, name='article_detail'),
    path('ajax/get-governates/', views.get_governates, name='get_governates'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    path('ajax/chatbot/', views.chatbot, name='chatbot'),
    path('ajax/get-parcel-details/', views.get_parcel_details, name='get_parcel_details'),
    path('ajax/update-parcel-status/', views.update_parcel_status_ajax, name='update_parcel_status_ajax'),
    
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('contact/', views.contact, name='contact'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/verify-otp/', views.verify_otp_view, name='verify_otp'),
    
    # OTP Login
    path('login/request-otp/', views.request_login_otp, name='request_login_otp'),
    path('login/verify-otp/', views.verify_login_otp, name='verify_login_otp'),

    # API Endpoints (Standard)
    path('api/auth/token/', api_views.CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/parcels/', api_views.ParcelListCreateView.as_view(), name='api_parcel_list'),
    path('api/parcels/<int:pk>/', api_views.ParcelDetailView.as_view(), name='api_parcel_detail'),
    path('api/track/<str:tracking_number>/', api_views.PublicParcelTrackView.as_view(), name='api_track_parcel'),
    path('api/profile/', api_views.UserProfileView.as_view(), name='api_user_profile'),
    
    # Aliases for mobile app compatibility (API v1)
    path('api/shipments/', api_views.ParcelListCreateView.as_view(), name='api_shipment_list'),
    path('api/shipments/<int:pk>/', api_views.ParcelDetailView.as_view(), name='api_shipment_detail'),

    # Root-level Aliases (for apps hardcoded to /shipments/)
    path('shipments/', api_views.ParcelListCreateView.as_view(), name='root_shipment_list'),
    path('shipments/<int:pk>/', api_views.ParcelDetailView.as_view(), name='root_shipment_detail'),
]
