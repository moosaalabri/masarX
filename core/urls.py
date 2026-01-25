from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

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
]