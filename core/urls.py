from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('shipment-request/', views.shipment_request, name='shipment_request'),
    path('accept-parcel/<int:parcel_id>/', views.accept_parcel, name='accept_parcel'),
    path('update-status/<int:parcel_id>/', views.update_status, name='update_status'),
    path('article/', views.article_detail, name='article_detail'),
    
    # AJAX for locations
    path('ajax/get-governates/', views.get_governates, name='get_governates'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    
    # Thawani Payment
    path('payment/initiate/<int:parcel_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Static pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
]