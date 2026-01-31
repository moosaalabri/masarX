from decimal import Decimal
import math
from .models import PricingRule, PlatformProfile

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return Decimal('0.00')

    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    
    return Decimal(c * r)

def get_pricing_breakdown(distance_km, weight_kg):
    """
    Returns a dictionary with pricing breakdown:
    {
        'price': Decimal,
        'platform_fee': Decimal,
        'platform_fee_percentage': Decimal,
        'driver_amount': Decimal,
        'error': str (optional)
    }
    """
    # 1. Find matching rule
    # We look for a rule that covers this distance and weight
    rule = PricingRule.objects.filter(
        min_distance__lte=distance_km,
        max_distance__gte=distance_km,
        min_weight__lte=weight_kg,
        max_weight__gte=weight_kg
    ).first()

    if not rule:
        # Fallback or Error
        # Try to find a rule just by distance if weight is slightly off? No, strict for now.
        return {
            'price': Decimal('0.000'),
            'platform_fee': Decimal('0.000'),
            'platform_fee_percentage': Decimal('0.00'),
            'driver_amount': Decimal('0.000'),
            'error': 'No pricing rule found for this distance/weight combination.'
        }

    total_price = rule.price

    # 2. Calculate Fees
    profile = PlatformProfile.objects.first()
    fee_percentage = profile.platform_fee_percentage if profile else Decimal('0.00')
    
    platform_fee = total_price * (fee_percentage / Decimal('100.00'))
    driver_amount = total_price - platform_fee

    return {
        'price': total_price,
        'platform_fee': platform_fee,
        'platform_fee_percentage': fee_percentage,
        'driver_amount': driver_amount
    }
