from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from .managers import CustomUserManager
import random
import string
from PIL import Image


def generate_member_id():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"MEM-{rand}"


def generate_student_id():
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"IUAA-{rand}"


class Member(models.Model):
    member_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Member ID"
    )
    
    full_name = models.CharField(
        max_length=150,
        verbose_name="Full Name"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address"
    )
    
    student_id = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Student ID"
    )
    
    course = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Course/Department"
    )
    
    batch = models.CharField(
        max_length=10,
        verbose_name="Batch Year"
    )
    
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Graduation Year"
    )
    
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, verbose_name="Address")
    
    current_job = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Current Job/Position"
    )
    
    current_company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Current Company/Organization"
    )
    
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn Profile")
    github_url = models.URLField(blank=True, verbose_name="GitHub Profile")
    portfolio_url = models.URLField(blank=True, verbose_name="Portfolio Website")
    
    is_active_member = models.BooleanField(
        default=True,
        verbose_name="Active Member"
    )
    
    joined_date = models.DateField(
        default=timezone.now,
        verbose_name="Member Since"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['full_name']
        verbose_name = "Member"
        verbose_name_plural = "Members"
        indexes = [
            models.Index(fields=['member_id']),
            models.Index(fields=['email']),
            models.Index(fields=['full_name']),
            models.Index(fields=['batch']),
            models.Index(fields=['graduation_year']),
            models.Index(fields=['is_active_member']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.member_id})"
    
    def save(self, *args, **kwargs):
        if not self.member_id:
            while True:
                generated_id = generate_member_id()
                if not Member.objects.filter(member_id=generated_id).exists():
                    self.member_id = generated_id
                    break
        
        if not self.student_id:
            self.student_id = generate_student_id()
        
        super().save(*args, **kwargs)
    
    @property
    def is_user(self):
        return hasattr(self, 'user_account')
    
    def create_user_account(self, password=None):
        from django.contrib.auth.hashers import make_password
        
        if hasattr(self, 'user_account'):
            raise ValidationError("Member already has a user account")
        
        user = User.objects.create(
            member=self,
            email=self.email,
            full_name=self.full_name,
            password=make_password(password) if password else make_password(None)
        )
        
        return user


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.is_default:
            existing_default = Role.objects.filter(
                is_default=True
            ).exclude(id=self.id).exists()
            if existing_default:
                raise ValidationError("There can only be one default role")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Campus(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"
    
    def __str__(self):
        return self.name


class Committee(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Committee Name")
    description = models.TextField(blank=True, verbose_name="Description")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL Slug")
    is_active = models.BooleanField(default=True, verbose_name="Active Committee")
    order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Committee"
        verbose_name_plural = "Committees"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name


class LeadershipPosition(models.Model):
    POSITION_CHOICES = [
        ('PRESIDENT', 'President'),
        ('VICE_PRESIDENT', 'Vice President'),
        ('SECRETARY', 'Secretary'),
        ('TREASURER', 'Treasurer'),
        ('PUBLIC_RELATIONS_OFFICER', 'Public Relations Officer'),
        ('EXECUTIVE_MEMBER', 'Executive Member'),
    ]
    
    code = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        unique=True,
        verbose_name="Position Code"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Role Description"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Position"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'code']
        verbose_name = "Leadership Position"
        verbose_name_plural = "Leadership Positions"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return self.display_title
    
    @property
    def display_title(self):
        return dict(self.POSITION_CHOICES).get(self.code, self.code.replace('_', ' ').title())


class User(AbstractBaseUser, PermissionsMixin):
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name='user_account',
        verbose_name="Member"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Login Email"
    )
    
    full_name = models.CharField(
        max_length=150,
        verbose_name="Full Name"
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='users',
        verbose_name="User Roles"
    )
    
    committees = models.ManyToManyField(
        Committee,
        through='CommitteeMembership',
        related_name='committee_members',
        blank=True,
        verbose_name="Committees"
    )
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['member']),
        ]
    
    def __str__(self):
        return self.full_name
    
    def save(self, *args, **kwargs):
        if self.member:
            self.email = self.member.email
            self.full_name = self.member.full_name
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.full_name.split()[0] if ' ' in self.full_name else self.full_name
    
    def has_role(self, role_name):
        return self.roles.filter(name=role_name).exists()
    
    def get_default_role(self):
        default_role = self.roles.filter(is_default=True).first()
        if not default_role:
            default_role = self.roles.first()
        return default_role
    
    @property
    def student_id(self):
        return self.member.student_id
    
    @property
    def member_id(self):
        return self.member.member_id
    
    @property
    def is_association_leader(self):
        return self.leadership_assignments.filter(is_active=True).exists()
    
    @property
    def current_leadership_assignment(self):
        return self.leadership_assignments.filter(is_active=True).first()
    
    @property
    def leadership_history(self):
        return self.leadership_assignments.all().order_by('-start_date')
    
    @property
    def active_committees(self):
        return self.committee_memberships.filter(is_active=True).select_related('committee')
    
    @property
    def is_student(self):
        return self.has_role('Student')
    
    @property
    def is_alumni(self):
        return self.has_role('Alumni')
    
    @property
    def is_admin(self):
        return self.has_role('Admin') or self.is_superuser
    
    @property
    def is_staff_member(self):
        return self.has_role('Staff')
    
    @property
    def batch(self):
        return self.member.batch
    
    @property
    def graduation_year(self):
        return self.member.graduation_year
    
    @property
    def course(self):
        return self.member.course


class AssociationLeadership(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leadership_assignments',
        verbose_name="Leader"
    )
    
    position = models.ForeignKey(
        LeadershipPosition,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Leadership Position"
    )
    
    start_date = models.DateField(
        default=timezone.now,
        verbose_name="Start Date"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End Date"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Currently Active"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position__order', '-start_date']
        verbose_name = "Association Leadership"
        verbose_name_plural = "Association Leadership"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        status = "Active" if self.is_active else "Past"
        return f"{self.user.full_name} - {self.position.display_title} ({status})"
    
    def clean(self):
        if self.is_active and self.position_id:
            active_conflicts = AssociationLeadership.objects.filter(
                position_id=self.position_id,
                is_active=True
            ).exclude(id=self.id)
            
            if active_conflicts.exists():
                raise ValidationError(
                    f"Only one active {self.position.display_title} can exist at a time."
                )
        
        if self.is_active and self.user_id:
            user_active_positions = AssociationLeadership.objects.filter(
                user_id=self.user_id,
                is_active=True
            ).exclude(id=self.id)
            
            if user_active_positions.exists():
                raise ValidationError(
                    f"{self.user.full_name if hasattr(self, 'user') else 'This user'} already holds an active leadership position."
                )
        
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_current(self):
        return self.is_active and (
            not self.end_date or 
            self.end_date >= timezone.now().date()
        )


class CommitteeMembership(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='committee_memberships',
        verbose_name="Member"
    )
    
    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Committee"
    )
    
    role = models.CharField(
        max_length=100,
        default="Member",
        verbose_name="Role in Committee"
    )
    
    start_date = models.DateField(
        default=timezone.now,
        verbose_name="Start Date"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End Date"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Membership"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['committee__order', 'role', 'user__full_name']
        verbose_name = "Committee Membership"
        verbose_name_plural = "Committee Memberships"
        unique_together = ['user', 'committee']
        indexes = [
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.committee.name} ({self.role})"
    
    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('P', 'Prefer not to say'),
    ]
    
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Member"
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='P',
        verbose_name="Gender"
    )
    
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        verbose_name="Campus"
    )
    
    bio = models.TextField(blank=True, verbose_name="Biography")
    photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name="Profile Photo"
    )
    
    is_public = models.BooleanField(
        default=True,
        verbose_name="Public Profile"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['member__full_name']
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(fields=['is_public']),
            models.Index(fields=['gender']),
        ]
    
    def __str__(self):
        return f"{self.member.full_name} - {self.member.batch}"
    
    @property
    def name(self):
        return self.member.full_name
    
    @property
    def email(self):
        return self.member.email
    
    @property
    def student_id(self):
        return self.member.student_id
    
    @property
    def member_id(self):
        return self.member.member_id
    
    @property
    def campus_name(self):
        return self.campus.name if self.campus else "N/A"
    
    @property
    def gender_display(self):
        return dict(self.GENDER_CHOICES).get(self.gender, 'Not specified')
    
    @property
    def is_association_leader(self):
        if self.member.is_user:
            return self.member.user_account.is_association_leader
        return False
    
    @property
    def current_leadership_info(self):
        if self.member.is_user:
            assignment = self.member.user_account.current_leadership_assignment
            if assignment:
                return {
                    'title': assignment.position.display_title,
                    'start_date': assignment.start_date,
                    'is_current': assignment.is_current
                }
        return None
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Resize photo if it exists
        if self.photo:
            img = Image.open(self.photo)
            # Resize to 397x556, maintaining aspect ratio
            img.thumbnail((397, 556), Image.Resampling.LANCZOS)
            # Create a new image with the exact size, centered
            new_img = Image.new('RGB', (397, 556), (255, 255, 255))
            # Calculate position to center the image
            x = (397 - img.width) // 2
            y = (556 - img.height) // 2
            new_img.paste(img, (x, y))
            # Save the resized image back
            from io import BytesIO
            from django.core.files.base import ContentFile
            buffer = BytesIO()
            new_img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            self.photo.save(self.photo.name, ContentFile(buffer.read()), save=False)
        
        super().save(*args, **kwargs)
        
        if is_new and self.member.is_user:
            user = self.member.user_account
            if not user.roles.exists():
                default_role = Role.objects.filter(is_default=True).first()
                if default_role:
                    user.roles.add(default_role)
                else:
                    alumni_role, created = Role.objects.get_or_create(name='Alumni')
                    user.roles.add(alumni_role)


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('REGISTER', 'Registration'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('ROLE_CHANGE', 'Role Change'),
        ('LEADERSHIP_ASSIGN', 'Leadership Assignment'),
        ('LEADERSHIP_REVOKE', 'Leadership Revocation'),
        ('COMMITTEE_JOIN', 'Committee Join'),
        ('COMMITTEE_LEAVE', 'Committee Leave'),
        ('MEMBER_CREATE', 'Member Created'),
        ('USER_CREATE', 'User Account Created'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name="User"
    )
    
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name="Member"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    
    details = models.JSONField(default=dict, verbose_name="Action Details")
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address"
    )
    
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['member', 'action']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        user_id = self.user.member_id if self.user else 'No User'
        member_id = self.member.member_id if self.member else 'No Member'
        return f"{user_id}/{member_id} - {self.action} - {self.timestamp}"


class Event(models.Model):
    EVENT_TYPES = [
        ('MEETUP', 'Meetup'),
        ('SEMINAR', 'Seminar'),
        ('GET_TOGETHER', 'Get Together'),
        ('WORKSHOP', 'Workshop'),
        ('CONFERENCE', 'Conference'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name="Event Title"
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL Slug"
    )
    
    description = models.TextField(
        verbose_name="Event Description"
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        default='MEETUP',
        verbose_name="Event Type"
    )
    
    event_date = models.DateTimeField(
        verbose_name="Event Date & Time"
    )
    
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End Date & Time"
    )
    
    location = models.CharField(
        max_length=200,
        verbose_name="Location"
    )
    
    venue = models.TextField(
        blank=True,
        verbose_name="Venue Details"
    )
    
    image = models.ImageField(
        upload_to='events/',
        blank=True,
        null=True,
        verbose_name="Event Image"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Event"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured Event"
    )
    
    max_attendees = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maximum Attendees"
    )
    
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Registration Deadline"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events',
        verbose_name="Created By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = "Event"
        verbose_name_plural = "Events"
        indexes = [
            models.Index(fields=['event_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_upcoming(self):
        return self.event_date > timezone.now()
    
    @property
    def is_past(self):
        return self.event_date < timezone.now()
    
    @property
    def days_until_event(self):
        if self.is_upcoming:
            return (self.event_date.date() - timezone.now().date()).days
        return 0
    
    @property
    def can_register(self):
        if not self.is_upcoming:
            return False
        if self.registration_deadline:
            return timezone.now() < self.registration_deadline
        return True
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('ATTENDED', 'Attended'),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name="Event"
    )
    
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        verbose_name="Member"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Registration Status"
    )
    
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registered_at']
        verbose_name = "Event Registration"
        verbose_name_plural = "Event Registrations"
        unique_together = ['event', 'member']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['member', 'status']),
        ]
    
    def __str__(self):
        return f"{self.member.full_name} - {self.event.title}"


class GalleryAlbum(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Album Title"
    )
    
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name="URL Slug"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Album Description"
    )
    
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='albums',
        verbose_name="Related Event"
    )
    
    album_date = models.DateField(
        default=timezone.now,
        verbose_name="Album Date"
    )
    
    cover_image = models.ImageField(
        upload_to='gallery/covers/',
        blank=True,
        null=True,
        verbose_name="Cover Image"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Album"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured Album"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_albums',
        verbose_name="Created By"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-album_date']
        verbose_name = "Gallery Album"
        verbose_name_plural = "Gallery Albums"
        indexes = [
            models.Index(fields=['album_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.title
    
    def total_images(self):
        return self.images.count()
    total_images.short_description = "Total Images"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while GalleryAlbum.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class GalleryImage(models.Model):
    album = models.ForeignKey(
        GalleryAlbum,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Album"
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Image Title"
    )
    
    image = models.ImageField(
        upload_to='gallery/images/',
        verbose_name="Image File"
    )
    
    caption = models.TextField(
        blank=True,
        verbose_name="Caption"
    )
    
    taken_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date Taken"
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Featured Image"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"
        indexes = [
            models.Index(fields=['album', 'is_featured']),
            models.Index(fields=['album', 'order']),
        ]
    
    def __str__(self):
        return self.title or f"Image in {self.album.title}"    
    



class JobAdvertisement(models.Model):
    # Basic Information
    title = models.CharField(max_length=200, verbose_name="Job Title")
    company_name = models.CharField(max_length=200, verbose_name="Company Name")
    company_logo = models.ImageField(upload_to='company-logos/',blank=True,null=True,verbose_name="Company Logo")
    
    short_description = models.TextField(verbose_name="Short Description",help_text="Brief description of the job")
    
    # Advertisement Detailsation_url = models.URLField(max_length=500,verbose_name="Application URL",help_text="External link where candidates can apply")
    
    # Status & Dates
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active Advertisement"
    )
    
    is_expired = models.BooleanField(
        default=False,
        verbose_name="Expired"
    )
    
    posted_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Posted Date"
    )
    
    # Display order
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Display Order",
        help_text="Higher number appears first"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-display_order', '-posted_date']
        verbose_name = "Job Advertisement"
        verbose_name_plural = "Job Advertisements"
    
    def __str__(self):
        return f"{self.title} - {self.company_name}"
    
    
    
    
    
    
    
    


    
    
