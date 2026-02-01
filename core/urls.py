from django.urls import path
from . import views, api_views

urlpatterns = [
    path('', views.index, name='index'),
    path('track/', views.track_parcel, name='track'),
    path('register/', views.register, name='register'),
    path('register/shipper/', views.register_shipper, name='register_shipper'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('verify-registration/', views.verify_registration, name='verify_registration'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('login/2fa/select/', views.select_2fa_method, name='select_2fa_method'),
    path('login/2fa/verify/', views.verify_2fa_otp, name='verify_2fa_otp'),
    path('logout/', views.logout, name='logout'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('shipment-request/', views.shipment_request, name='shipment_request'),
    path('update-status/<int:parcel_id>/', views.update_status, name='update_status'),
    path('initiate-payment/<int:parcel_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    
    path('article/', views.article_detail, name='article_detail'),
    path('ajax/get-governates/', views.get_governates, name='get_governates'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('contact/', views.contact, name='contact'),
    
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    
    path('rate-driver/<int:parcel_id>/', views.rate_driver, name='rate_driver'),
    
    # OTP Login / Passwordless
    path('ajax/request-login-otp/', views.request_login_otp, name='request_login_otp'),
    path('ajax/verify-login-otp/', views.verify_login_otp, name='verify_login_otp'),
    
    # Chatbot
    path('ajax/chatbot/', views.chatbot, name='chatbot'),
    
    # Document Generation
    path('parcel-label/<int:parcel_id>/', views.generate_parcel_label, name='generate_parcel_label'),
    path('invoice/<int:parcel_id>/', views.generate_invoice, name='generate_invoice'),
    
    # QR Scanner
    path('scan-qr/', views.scan_qr_view, name='scan_qr'),
    path('ajax/get-parcel-details/', views.get_parcel_details, name='get_parcel_details'),
    path('ajax/update-parcel-status/', views.update_parcel_status_ajax, name='update_parcel_status_ajax'),
    
    path('edit-parcel/<int:parcel_id>/', views.edit_parcel, name='edit_parcel'),
    path('cancel-parcel/<int:parcel_id>/', views.cancel_parcel, name='cancel_parcel'),
    
    path('accept-parcel/<int:parcel_id>/', views.accept_parcel, name='accept_parcel'),
    path('reject-parcel/<int:parcel_id>/', views.reject_parcel, name='reject_parcel'),
    
    path('report-driver/<int:parcel_id>/', views.report_driver, name='report_driver'),
    
    # API Endpoints (for Mobile App)
    path('api/v1/parcels/', api_views.ParcelListCreateView.as_view(), name='api_parcel_list'),
    path('api/v1/parcels/<int:pk>/', api_views.ParcelDetailView.as_view(), name='api_parcel_detail'),
    path('api/v1/pricing/', api_views.PriceCalculatorView.as_view(), name='api_pricing'),
    path('api/v1/profile/', api_views.UserProfileView.as_view(), name='api_profile'),
]
