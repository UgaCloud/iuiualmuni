# accounts/utils.py
import random
import string
from django.db.models import Count
from .models import Profile
from django.utils import timezone
from .models import *

def promote_to_leader(user, position_code, notes=""):
    """
    Promote an existing user to a leadership position
    """
    try:
        # Check if user already has an active leadership position
        if AssociationLeadership.objects.filter(user=user, is_active=True).exists():
            raise ValueError(f"{user.full_name} already has an active leadership position")
        
        # Get the position
        position = LeadershipPosition.objects.get(code=position_code, is_active=True)
        
        # Check if position is already occupied
        if AssociationLeadership.objects.filter(position=position, is_active=True).exists():
            # Deactivate current holder
            current_holder = AssociationLeadership.objects.get(
                position=position, 
                is_active=True
            )
            current_holder.is_active = False
            current_holder.end_date = timezone.now().date()
            current_holder.save()
        
        # Create new leadership assignment
        leadership = AssociationLeadership.objects.create(
            user=user,
            position=position,
            start_date=timezone.now().date(),
            is_active=True,
            notes=notes
        )
        
        return leadership
    
    except LeadershipPosition.DoesNotExist:
        raise ValueError(f"Position with code '{position_code}' does not exist")
    except Exception as e:
        raise ValueError(f"Error promoting user: {str(e)}")

def demote_leader(user, position_code=None):
    """
    Remove leadership from a user
    """
    try:
        if position_code:
            # Demote from specific position
            position = LeadershipPosition.objects.get(code=position_code)
            leadership = AssociationLeadership.objects.get(
                user=user,
                position=position,
                is_active=True
            )
        else:
            # Demote from any active position
            leadership = AssociationLeadership.objects.get(
                user=user,
                is_active=True
            )
        
        leadership.is_active = False
        leadership.end_date = timezone.now().date()
        leadership.save()
        
        return leadership
    
    except AssociationLeadership.DoesNotExist:
        raise ValueError(f"{user.full_name} is not an active leader")
    except Exception as e:
        raise ValueError(f"Error demoting user: {str(e)}")





def get_gender_statistics():
    """Get statistics about gender distribution"""
    stats = Profile.objects.values('gender').annotate(
        count=Count('gender')
    ).order_by('-count')
    
    # Convert to more readable format
    total = sum(item['count'] for item in stats)
    result = {
        'total': total,
        'breakdown': []
    }
    
    gender_map = dict(Profile.GENDER_CHOICES)
    for item in stats:
        result['breakdown'].append({
            'gender_code': item['gender'],
            'gender_name': gender_map.get(item['gender'], 'Unknown'),
            'count': item['count'],
            'percentage': round((item['count'] / total * 100), 2) if total > 0 else 0
        })
    
    return result

# Example usage in a view:
# def gender_dashboard(request):
#     if not request.user.is_staff:
#         raise PermissionDenied
    
#     stats = get_gender_statistics()
#     context = {
#         'gender_stats': stats,
#         'male_count': sum(item['count'] for item in stats['breakdown'] if item['gender_code'] == 'M'),
#         'female_count': sum(item['count'] for item in stats['breakdown'] if item['gender_code'] == 'F'),
#     }
#     return render(request, 'admin/gender_dashboard.html', context)































