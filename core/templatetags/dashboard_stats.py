from django import template
from django.contrib.auth.models import User
from core.models import Parcel, Profile
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import json

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    # User Stats
    total_users = User.objects.count()
    drivers_count = Profile.objects.filter(role='car_owner').count()
    shippers_count = Profile.objects.filter(role='shipper').count()

    # Parcel Stats
    total_parcels = Parcel.objects.count()
    delivered_parcels = Parcel.objects.filter(status='delivered').count()
    pending_parcels = Parcel.objects.filter(status='pending').count()
    
    # Financials
    # Summing price of delivered parcels (assuming delivered = revenue realized)
    # If payments are enabled, we might want to check payment_status='paid' as well.
    # For now, sticking to delivered as a safe proxy for completed business.
    total_revenue = Parcel.objects.filter(status='delivered').aggregate(Sum('price'))['price__sum'] or 0
    
    # Recent Activity
    recent_parcels = Parcel.objects.select_related('shipper', 'shipper__profile').order_by('-created_at')[:5]

    # Chart Data (Last 7 Days)
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    
    daily_counts = []
    for date_str in dates:
        # We'll use created_at__date lookup
        count = Parcel.objects.filter(created_at__date=date_str).count()
        daily_counts.append(count)

    return {
        'total_users': total_users,
        'drivers_count': drivers_count,
        'shippers_count': shippers_count,
        'total_parcels': total_parcels,
        'delivered_parcels': delivered_parcels,
        'pending_parcels': pending_parcels,
        'total_revenue': total_revenue,
        'recent_parcels': recent_parcels,
        'chart_labels': json.dumps(dates),
        'chart_data': json.dumps(daily_counts),
    }