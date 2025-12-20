from django.http import request
from django.shortcuts import *
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .models import *
from django.utils import timezone

from django.core.paginator import *
from django.db.models import Q

from django.views.generic import DetailView
from django.views.generic.list import ListView

from django.db import transaction
from .forms import *






def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileRegistrationForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    # Save user first
                    user = user_form.save(commit=False)
                    user.is_active = True
                    user.is_verified = False
                    user.save()
                    
                    # Save profile with user reference
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.save()
                    
                    # Assign default role automatically (handled in Profile.save())
                    
                    # Create audit log entry
                    AuditLog.objects.create(
                        user=user,
                        action='REGISTER',
                        details={
                            'email': user.email,
                            'full_name': user.full_name,
                            'batch': profile.batch,
                            'gender': profile.gender,
                        },
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                # Auto-login the user after successful registration
                auth_login(request, user)
                
                # Create audit log for auto-login
                AuditLog.objects.create(
                    user=user,
                    action='LOGIN',
                    details={
                        'source': 'registration_auto_login',
                        'method': 'auto',
                    },
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(
                    request,
                    f'Registration successful! Welcome, {user.get_short_name()}!'
                )
                return redirect('members') 
                
            except Exception as e:
                messages.error(
                    request,
                    f'Registration failed: {str(e)}. Please try again.'
                )
        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileRegistrationForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'campuses': Campus.objects.filter(is_active=True)
    }
    return render(request, 'register.html', context)

class LoginView(View):
    """User login view using email and password"""
    
    def get(self, request):
        # If user is already logged in, redirect to dashboard
        if request.user.is_authenticated:
            return redirect('home')
        
        return render(request, 'login.html')
    
    def post(self, request):
        # IMPORTANT: Use the correct field names from your form
        email = request.POST.get('register_email')  # Changed from 'email'
        password = request.POST.get('register_password')  # Changed from 'password'
        remember_me = request.POST.get('customCheck1')  # Changed from 'remember_me'
        
        # Basic validation
        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'login.html')
        
        # Authenticate user using email
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if user is active
            if user.is_active:
                # Login the user
                auth_login(request, user)
                
                # Handle remember me (set session expiry)
                if remember_me:
                    # Set session to last 2 weeks
                    request.session.set_expiry(1209600)  # 2 weeks in seconds
                else:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                
                messages.success(request, f'Welcome back, {user.full_name}!')
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is inactive.')
        else:
            messages.error(request, 'Invalid email or password.')
        
        return render(request, 'login.html')


class LogoutView(View):
    """User logout view"""
    
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')


class ProfileDetailView(DetailView):
    """View for individual profile details"""
    model = Profile
    template_name = 'profile_detail.html'
    context_object_name = 'profile'
    
    def get_object(self):
        return get_object_or_404(
            Profile.objects.select_related('user', 'campus').prefetch_related('user__roles'),
            id=self.kwargs['pk'],
            is_public=True
        )



def association_heads_view(request):
    """
    View for displaying ONLY association heads (leaders)
    Excludes regular members and committee members
    """
    # Get all active leadership assignments
    active_leadership = AssociationLeadership.objects.filter(
        is_active=True
    ).select_related(
        'user__profile',
        'position'
    ).order_by('position__order')
    
    # Get the users from these leadership assignments
    leader_users = [assignment.user for assignment in active_leadership]
    
    # Get profiles of these leaders
    profiles = Profile.objects.filter(
        user__in=leader_users,
        is_public=True
    ).select_related('user', 'campus')
    
    context = {
        'leaders': active_leadership,
        'profiles': profiles,
        'page_title': 'Association Leadership',
    }
    
    return render(request, 'association_heads.html', context)

def committee_heads_view(request):
    """
    View for displaying committee heads/leaders
    Separate from association leadership
    """
    # Get committee heads (you can define what makes someone a committee head)
    # For example: people with specific roles in committees
    committee_heads = CommitteeMembership.objects.filter(
        Q(role__icontains='chair') | 
        Q(role__icontains='coordinator') |
        Q(role__icontains='head') |
        Q(role__icontains='lead'),
        is_active=True
    ).select_related(
        'user__profile',
        'committee'
    ).order_by('committee__order', 'user__full_name')
    
    # Get unique users to avoid duplicates
    seen_users = set()
    unique_committee_heads = []
    for head in committee_heads:
        if head.user.id not in seen_users:
            unique_committee_heads.append(head)
            seen_users.add(head.user.id)
    
    # Get their profiles
    head_users = [head.user for head in unique_committee_heads]
    profiles = Profile.objects.filter(
        user__in=head_users,
        is_public=True
    ).select_related('user', 'campus')
    
    context = {
        'committee_heads': unique_committee_heads,
        'profiles': profiles,
        'page_title': 'Committee Leadership',
    }
    
    return render(request, 'committee_heads.html', context)

def regular_members_view(request):
    """
    View for displaying ONLY regular members (not association or committee heads)
    """
    # Get all association leaders
    association_leader_ids = AssociationLeadership.objects.filter(
        is_active=True
    ).values_list('user_id', flat=True)
    
    # Get all active committee members (potential committee heads)
    active_committee_members = CommitteeMembership.objects.filter(
        is_active=True
    ).values_list('user_id', flat=True).distinct()
    
    # Combine both to exclude
    excluded_user_ids = set(list(association_leader_ids) + list(active_committee_members))
    
    # Get profiles of users who are NOT leaders or committee members
    # and have public profiles
    profiles_list = Profile.objects.filter(
        is_public=True
    ).exclude(
        user_id__in=excluded_user_ids
    ).select_related('user', 'campus').order_by('user__full_name')
    
    # Pagination
    paginator = Paginator(profiles_list, 8)  # 8 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Our Members',
        'total_members': profiles_list.count(),
    }
    
    return render(request, 'members.html', context)

def all_members_directory_view(request):
    """
    View for displaying ALL members with filtering options
    """
    # Get all public profiles
    profiles_list = Profile.objects.filter(
        is_public=True
    ).select_related('user', 'campus').order_by('user__full_name')
    
    # Apply filters if provided
    batch_filter = request.GET.get('batch')
    campus_filter = request.GET.get('campus')
    
    if batch_filter:
        profiles_list = profiles_list.filter(batch=batch_filter)
    if campus_filter:
        profiles_list = profiles_list.filter(campus_id=campus_filter)
    
    # Get leadership status for each profile
    for profile in profiles_list:
        profile.is_leader = profile.user.is_association_leader
        profile.is_committee_member = profile.user.active_committees.exists()
    
    # Pagination
    paginator = Paginator(profiles_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    batches = Profile.objects.values_list('batch', flat=True).distinct().order_by('-batch')
    campuses = Campus.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'batches': batches,
        'campuses': campuses,
        'page_title': 'Members Directory',
    }
    
    return render(request, 'members_committee.html', context)



# Create your views here.
def index(request):
    """Home page view after login"""
    context = {}
    if request.user.is_authenticated:
        context['welcome_message'] = f"Welcome back, {request.user.get_short_name()}!"
    return render(request, 'index.html')

def about(request):

    """ View for displaying ONLY association heads (leaders)
    Excludes regular members and committee members
    """
    # Get all active leadership assignments
    active_leadership = AssociationLeadership.objects.filter(
        is_active=True
    ).select_related(
        'user__profile',
        'position'
    ).order_by('position__order')
    
    # Get the users from these leadership assignments
    leader_users = [assignment.user for assignment in active_leadership]
    
    # Get profiles of these leaders
    profiles = Profile.objects.filter(
        user__in=leader_users,
        is_public=True
    ).select_related('user', 'campus')
    
    context = {
        'leaders': active_leadership,
        'profiles': profiles,
        'page_title': 'Association Leadership',
    }

    return render(request, 'about.html', context)

def event(request):
    return render(request, 'event.html')

def contact(request):
    return render(request, 'contact.html')

def gallery(request):
    return render(request, 'gallery.html')


def gallery_single(request):
    return render(request, 'single-album.html')

def directory(request):
    return render(request, 'directory.html')

def career(request):
    return render(request, 'career.html')


def loginview(request):
    return render(request, 'login.html')



