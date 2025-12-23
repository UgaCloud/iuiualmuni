from django.http import request
from django.shortcuts import *
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.http import JsonResponse











def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    member = Member.objects.create(
                        full_name=user_form.cleaned_data['full_name'],
                        email=user_form.cleaned_data['email'],
                        batch=user_form.cleaned_data['batch'],
                        course=user_form.cleaned_data['course'],
                        phone=user_form.cleaned_data.get('phone', ''),
                        graduation_year=user_form.cleaned_data.get('graduation_year')
                    )
                    
                    profile = profile_form.save(commit=False)
                    profile.member = member
                    profile.save()
                    
                    AuditLog.objects.create(
                        member=member,
                        action='MEMBER_CREATE',
                        details={
                            'email': member.email,
                            'full_name': member.full_name,
                            'batch': member.batch,
                        },
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                messages.success(request, 'Registration successful! You are now a member.')
                messages.info(request, 'The admin will review your registration.')
                return redirect('members') 
                
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
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
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'login.html')
    
    def post(self, request):
        email = request.POST.get('register_email')
        password = request.POST.get('register_password')
        remember_me = request.POST.get('customCheck1')
        
        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'login.html')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                
                if remember_me:
                    request.session.set_expiry(1209600)
                else:
                    request.session.set_expiry(0)
                
                if hasattr(user, 'member'):
                    AuditLog.objects.create(
                        user=user,
                        member=user.member,
                        action='LOGIN',
                        details={
                            'source': 'manual_login',
                            'method': 'email_password',
                        },
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                messages.success(request, f'Welcome back, {user.full_name}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is inactive.')
        else:
            messages.error(request, 'Invalid email or password.')
        
        return render(request, 'login.html')

class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'member'):
            AuditLog.objects.create(
                user=request.user,
                member=request.user.member,
                action='LOGOUT',
                details={'source': 'manual_logout'},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')

class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'profile_detail.html'
    context_object_name = 'profile'
    
    def get_object(self):
        return get_object_or_404(
            Profile.objects.select_related('member', 'campus'),
            id=self.kwargs['pk'],
            is_public=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = context['profile']
        
        if hasattr(profile.member, 'user_account'):
            user = profile.member.user_account
            context['is_association_leader'] = user.is_association_leader
            context['current_leadership'] = user.current_leadership_assignment
            context['leadership_history'] = user.leadership_history[:5]
            context['active_committees'] = user.active_committees
        else:
            context['is_association_leader'] = False
            context['current_leadership'] = None
            context['leadership_history'] = []
            context['active_committees'] = []
        
        return context

def association_heads_view(request):
    """
    View for displaying ONLY association heads (leaders)
    Excludes regular members and committee members
    """
    # Get all active leadership assignments
    active_leadership = AssociationLeadership.objects.filter(
        is_active=True
    ).select_related(
        'user__member__profile',
        'position'
    ).order_by('position__order')
    
    # Create a list of tuples with leader and profile
    leaders_with_profiles = []
    for leader in active_leadership:
        # Get the profile for this leader's member
        try:
            profile = Profile.objects.get(member=leader.user.member, is_public=True)
        except Profile.DoesNotExist:
            profile = None
        
        leaders_with_profiles.append({
            'leader': leader,
            'profile': profile
        })
    
    paginator = Paginator(leaders_with_profiles, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Association Leadership',
    }
    
    return render(request, 'association_heads.html', context)






def committee_heads_view(request):
    committee_heads = CommitteeMembership.objects.filter(
        Q(role__icontains='chair') | 
        Q(role__icontains='coordinator') |
        Q(role__icontains='head') |
        Q(role__icontains='lead'),
        is_active=True
    ).select_related(
        'user__member__profile',
        'committee'
    ).order_by('committee__order', 'user__full_name')
    
    seen_users = set()
    unique_committee_heads = []
    for head in committee_heads:
        if head.user.id not in seen_users:
            unique_committee_heads.append(head)
            seen_users.add(head.user.id)
    
    head_members = [head.user.member for head in unique_committee_heads]
    profiles = Profile.objects.filter(
        member__in=head_members,
        is_public=True
    ).select_related('member', 'campus')
    
    context = {
        'committee_heads': unique_committee_heads,
        'profiles': profiles,
        'page_title': 'Committee Leadership',
    }
    
    return render(request, 'committee_heads.html', context)

def regular_members_view(request):
    association_leader_user_ids = AssociationLeadership.objects.filter(
        is_active=True
    ).values_list('user_id', flat=True)
    
    active_committee_user_ids = CommitteeMembership.objects.filter(
        is_active=True
    ).values_list('user_id', flat=True).distinct()
    
    excluded_user_ids = set(list(association_leader_user_ids) + list(active_committee_user_ids))
    
    excluded_member_ids = []
    for user_id in excluded_user_ids:
        try:
            user = User.objects.get(id=user_id)
            excluded_member_ids.append(user.member.id)
        except User.DoesNotExist:
            pass
    
    profiles_list = Profile.objects.filter(
        is_public=True
    ).exclude(
        member_id__in=excluded_member_ids
    ).select_related('member', 'campus').order_by('member__full_name')
    
    paginator = Paginator(profiles_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Our Members',
        'total_members': profiles_list.count(),
    }
    
    return render(request, 'members.html', context)

def all_members_directory_view(request):
    profiles_list = Profile.objects.filter(
        is_public=True
    ).select_related('member', 'campus').order_by('member__full_name')
    
    batch_filter = request.GET.get('batch')
    campus_filter = request.GET.get('campus')
    
    if batch_filter:
        profiles_list = profiles_list.filter(member__batch=batch_filter)
    if campus_filter:
        profiles_list = profiles_list.filter(campus_id=campus_filter)
    
    for profile in profiles_list:
        profile.is_leader = False
        profile.is_committee_member = False
        
        if hasattr(profile.member, 'user_account'):
            user = profile.member.user_account
            profile.is_leader = user.is_association_leader
            profile.is_committee_member = user.active_committees.exists()
    
    paginator = Paginator(profiles_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    batches = Member.objects.values_list('batch', flat=True).distinct().order_by('-batch')
    campuses = Campus.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'batches': batches,
        'campuses': campuses,
        'page_title': 'Members Directory',
    }
    
    return render(request, 'members_committee.html', context)

def index(request):

    jobs = JobAdvertisement.objects.filter(is_active=True).order_by('-display_order', '-posted_date')[:6]
    
    # Get the closest upcoming event (the one that is soonest)
    upcoming_event = Event.objects.filter(
        event_date__gte=timezone.now(),
        is_active=True
    ).order_by('event_date').first()
    
    context = {
        'upcoming_event': upcoming_event,
        'jobs': jobs,  # Changed from 'job' to 'jobs' to match template variable name
    }
    
    if request.user.is_authenticated:
        context['welcome_message'] = f"Welcome back, {request.user.get_short_name()}!"
        if hasattr(request.user, 'member'):
            context['member'] = request.user.member
            context['member_id'] = request.user.member.member_id
    
    return render(request, 'index.html', context)

def about(request):
    active_leadership = AssociationLeadership.objects.filter(
        is_active=True
    ).select_related(
        'user__member__profile',
        'position'
    ).order_by('position__order')
    
    # Create a list of tuples with leader and profile
    leaders_with_profiles = []
    for leader in active_leadership:
        # Get the profile for this leader's member
        try:
            profile = Profile.objects.get(member=leader.user.member, is_public=True)
        except Profile.DoesNotExist:
            profile = None
        
        leaders_with_profiles.append({
            'leader': leader,
            'profile': profile
        })
    
    context = {
        'leaders_with_profiles': leaders_with_profiles,
        'page_title': 'Association Leadership',
    }
    return render(request, 'about.html', context)


def event(request):
    # -----------------------------
    # GET FILTER PARAMS & ACTIVE TAB
    # -----------------------------
    year = request.GET.get('year')
    place = request.GET.get('place')
    event_type = request.GET.get('type')
    status = request.GET.get('status')
    active_tab = request.GET.get('tab', 'active')
    
    # -----------------------------
    # BASE QUERYSETS FOR BOTH TABS
    # -----------------------------
    # Get all events first
    all_events = Event.objects.all()
    
    # Apply filters function
    def apply_filters(queryset):
        qs = queryset
        
        # YEAR FILTER
        if year and year != 'Year':
            try:
                qs = qs.filter(event_date__year=int(year))
            except ValueError:
                pass
        
        # PLACE FILTER
        if place and place != 'Place':
            qs = qs.filter(location__icontains=place)
        
        # EVENT TYPE FILTER
        if event_type and event_type != 'Type':
            event_type_map = {
                'Meetup': 'MEETUP',
                'Seminar': 'SEMINAR',
                'Get Together': 'GET_TOGETHER',
                'Workshop': 'WORKSHOP',
                'Conference': 'CONFERENCE',
                'Other': 'OTHER',
            }
            db_event_type = event_type_map.get(event_type)
            if db_event_type:
                qs = qs.filter(event_type=db_event_type)
        
        # STATUS FILTER (only if not "All")
        if status and status != 'Status' and status != 'All':
            if status == 'Active':
                qs = qs.filter(is_active=True)
            elif status == 'Inactive':
                qs = qs.filter(is_active=False)
        
        return qs.order_by('-event_date')
    
    # Get filtered active and inactive events
    active_events_qs = apply_filters(all_events.filter(is_active=True))
    inactive_events_qs = apply_filters(all_events.filter(is_active=False))
    
    # Determine which tab is active and paginate accordingly
    if active_tab == 'active':
        # Paginate active events
        paginator = Paginator(active_events_qs, 3)
    else:
        # Paginate inactive events  
        paginator = Paginator(inactive_events_qs, 3)
    
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # -----------------------------
    # FILTER DATA
    # -----------------------------
    all_years = Event.objects.dates('event_date', 'year', order='DESC')
    years_list = [y.year for y in all_years]
    
    locations = (
        Event.objects
        .exclude(location__isnull=True)
        .exclude(location__exact='')
        .values_list('location', flat=True)
        .distinct()
    )
    
    # -----------------------------
    # CONTEXT
    # -----------------------------
    context = {
        'events': page_obj,  # For backward compatibility with event_list.html
        'active_events': active_events_qs,  # All filtered active events (no pagination)
        'inactive_events': inactive_events_qs,  # All filtered inactive events (no pagination)
        'active_tab': active_tab,
        'active_count': Event.objects.filter(is_active=True).count(),
        'inactive_count': Event.objects.filter(is_active=False).count(),
        'years': years_list,
        'locations': locations,
        'now': timezone.now(),
        'status_filter': status if status and status != 'Status' else None,
        'year_filter': year if year and year != 'Year' else None,
        'place_filter': place if place and place != 'Place' else None,
        'type_filter': event_type if event_type and event_type != 'Type' else None,
    }
    
    return render(request, 'event.html', context)


def single_event(request, event_slug):
    try:
        event = Event.objects.get(slug=event_slug)
    except Event.DoesNotExist:
        from django.http import Http404
        raise Http404("Event not found")
    
    context = {
        'event': event,
    }
    
    return render(request, 'single-event.html', context)

def contact(request):
    return render(request, 'contact.html')

def gallery(request):
    category = request.GET.get('category', 'All')
    
    albums = GalleryAlbum.objects.filter(is_active=True).prefetch_related('images')
    
    if category != 'All':
        category_map = {
            'Seminar': 'SEMINAR',
            'Event': 'MEETUP', 
            'Picnic': 'GET_TOGETHER'  
        }
        db_event_type = category_map.get(category)
        if db_event_type:
            albums = albums.filter(event__event_type=db_event_type)
    
   
    albums = albums.order_by('-album_date')
    
  
    paginator = Paginator(albums, 6) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'albums': page_obj,
        'current_category': category,
    }
    
    return render(request, 'gallery.html', context)

def gallery_single(request, album_slug=None):
    if album_slug:
        try:
            album = GalleryAlbum.objects.prefetch_related('images').get(slug=album_slug, is_active=True)
        except GalleryAlbum.DoesNotExist:
            album = GalleryAlbum.objects.prefetch_related('images').filter(is_active=True).first()
    else:
        album = GalleryAlbum.objects.prefetch_related('images').filter(is_active=True).first()
    
    if not album:
        context = {'album': None, 'images': []}
    else:
        images = album.images.all().order_by('order', '-created_at')
        context = {
            'album': album,
            'images': images,
        }
    
    return render(request, 'single-album.html', context)



def directory(request):
    return render(request, 'directory.html')

def career(request):
    # Get only active job advertisements
    jobs = JobAdvertisement.objects.filter(is_active=True).order_by('-display_order', '-posted_date')[:6]
    context = {
        'jobs': jobs,
    }
    return render(request, 'career.html', context)

def loginview(request):
    return render(request, 'login.html')

@login_required
def dashboard(request):
    context = {}
    if hasattr(request.user, 'member'):
        member = request.user.member
        context['member'] = member
        try:
            context['profile'] = Profile.objects.get(member=member)
        except Profile.DoesNotExist:
            context['profile'] = None
        context['is_leader'] = request.user.is_association_leader
        context['current_leadership'] = request.user.current_leadership_assignment
        context['active_committees'] = request.user.active_committees
        context['total_members'] = Member.objects.filter(is_active_member=True).count()
        context['total_users'] = User.objects.filter(is_active=True).count()
        context['total_leaders'] = AssociationLeadership.objects.filter(is_active=True).count()
    return render(request, 'dashboard.html', context)



@login_required
def profile_update(request):
    if not hasattr(request.user, 'member'):
        messages.error(request, 'No member account found.')
        return redirect('dashboard')
    
    member = request.user.member
    try:
        profile = Profile.objects.get(member=member)
    except Profile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        member_form = MemberUpdateForm(request.POST, instance=member)
        profile_form = ProfileRegistrationForm(request.POST, request.FILES, instance=profile)
        
        if member_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    member_form.save()
                    profile_instance = profile_form.save(commit=False)
                    profile_instance.member = member
                    profile_instance.save()
                    
                    if member.email != request.user.email:
                        request.user.email = member.email
                        request.user.save()
                    
                    AuditLog.objects.create(
                        user=request.user,
                        member=member,
                        action='PROFILE_UPDATE',
                        details={'fields_updated': list(request.POST.keys())},
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Update failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        member_form = MemberUpdateForm(instance=member)
        profile_form = ProfileRegistrationForm(instance=profile)
    
    context = {
        'member_form': member_form,
        'profile_form': profile_form,
        'member': member,
        'profile': profile,
    }
    return render(request, 'profile_update.html', context)



@user_passes_test(lambda u: u.is_staff)
def admin_create_user_account(request, member_id):
    member = get_object_or_404(Member, member_id=member_id)
    
    if hasattr(member, 'user_account'):
        messages.warning(request, 'This member already has a login account.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if not password or not confirm_password:
            messages.error(request, 'Both password fields are required.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            try:
                with transaction.atomic():
                    user = User.objects.create(
                        member=member,
                        email=member.email,
                        full_name=member.full_name,
                        is_active=True,
                        is_verified=True
                    )
                    user.set_password(password)
                    user.save()
                    
                    AuditLog.objects.create(
                        user=request.user,
                        member=member,
                        action='USER_CREATE',
                        details={'source': 'admin', 'admin_user': request.user.email},
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                messages.success(request, f'Login account created for {member.full_name}.')
                return redirect('admin_dashboard')
                
            except Exception as e:
                messages.error(request, f'Account creation failed: {str(e)}')
    
    context = {'member': member}
    return render(request, 'admin_create_user_account.html', context)


@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    members_without_accounts = Member.objects.filter(
        is_active_member=True
    ).exclude(
        user_account__isnull=False
    ).order_by('-created_at')
    
    recent_members = Member.objects.filter(
        is_active_member=True
    ).order_by('-created_at')[:10]
    
    context = {
        'members_without_accounts': members_without_accounts,
        'recent_members': recent_members,
        'total_members': Member.objects.filter(is_active_member=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_without_accounts': members_without_accounts.count(),
    }
    return render(request, 'admin_dashboard.html', context)





