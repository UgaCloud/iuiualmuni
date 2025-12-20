# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from .managers import CustomUserManager
import random
import string


def generate_student_id():
    """Generate student ID: IUAA-XXXXXX"""
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"IUAA-{rand}"


class Role(models.Model):
    """User role for permissions only - NOT for leadership positions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(
        default=False,
        help_text="Assign this role to new users automatically"
    )
    
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
    """Campus model for physical locations"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Campus"
        verbose_name_plural = "Campuses"
    
    def __str__(self):
        return self.name


class Committee(models.Model):
    """Committees under the alumni association - separate from leadership"""
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
    """
    Association-wide leadership positions (President, Secretary, etc.).
    FIX 1: Removed title-code redundancy. Only 'code' is unique identifier.
    Display title is automatically derived from code for admin convenience.
    """
    # Core leadership positions for the alumni association
    POSITION_CHOICES = [
        ('PRESIDENT', 'President'),
        ('VICE_PRESIDENT', 'Vice President'),
        ('SECRETARY', 'Secretary'),
        ('TREASURER', 'Treasurer'),
        ('PUBLIC_RELATIONS_OFFICER', 'Public Relations Officer'),
        ('EXECUTIVE_MEMBER', 'Executive Member'),
    ]
    
    # FIX: Use code as the unique identifier, remove separate title field
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
        verbose_name="Display Order",
        help_text="Lower numbers appear first"
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
        """Automatically derive display title from code"""
        return dict(self.POSITION_CHOICES).get(self.code, self.code.replace('_', ' ').title())
    
    def save(self, *args, **kwargs):
        # FIX: No need to auto-populate title since we use property
        super().save(*args, **kwargs)


class AssociationLeadership(models.Model):
    """
    Assigns association leadership positions to existing users.
    FIX 2: Added validation to ensure user can hold only ONE active leadership position.
    FIX 3: Improved related_name clarity for single active position.
    """
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        # FIX 3: Clearer naming - 'leadership_assignments' indicates this is a history
        related_name='leadership_assignments',
        verbose_name="Leader"
    )
    
    position = models.ForeignKey(
        LeadershipPosition,
        on_delete=models.CASCADE,
        # FIX 3: Clearer naming - 'assignments' indicates multiple can exist over time
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
        verbose_name="Currently Active",
        help_text="Uncheck when the leader resigns or completes term"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Optional notes about this leadership term"
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
        """FIX 2 & 4: Comprehensive validation for leadership constraints"""
        
        # FIX 2: Ensure only one active user per leadership position at a time
        if self.is_active and self.position_id:
            active_conflicts = AssociationLeadership.objects.filter(
                position_id=self.position_id,
                is_active=True
            ).exclude(id=self.id)
            
            if active_conflicts.exists():
                raise ValidationError(
                    f"Only one active {self.position.display_title} can exist at a time. "
                    f"Please deactivate the current leader first."
                )
        
        # FIX 2: Ensure user can hold only ONE active association leadership position at a time
        if self.is_active and self.user_id:
            user_active_positions = AssociationLeadership.objects.filter(
                user_id=self.user_id,
                is_active=True
            ).exclude(id=self.id)
            
            if user_active_positions.exists():
                raise ValidationError(
                    f"{self.user.full_name if hasattr(self, 'user') else 'This user'} "
                    f"already holds an active leadership position. A user can only hold "
                    f"one active association leadership position at a time."
                )
        
        # FIX 4: Keep date validations intact
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        # FIX 4: Ensure clean() is always called on save
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_current(self):
        """Check if this leadership assignment is current"""
        return self.is_active and (
            not self.end_date or 
            self.end_date >= timezone.now().date()
        )


class CommitteeMembership(models.Model):
    """Tracks user membership in committees - separate from association leadership"""
    user = models.ForeignKey(
        'User',
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
        verbose_name="Role in Committee",
        help_text="e.g., Coordinator, Volunteer, Member"
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
        # FIX 4: Keep date validation
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for alumni association members"""
    student_id = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name="Student ID"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address"
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
    
    # User roles for permissions (Student, Alumni, Admin, Staff)
    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='users',
        verbose_name="User Roles"
    )
    
    # Committees the user belongs to
    committees = models.ManyToManyField(
        Committee,
        through=CommitteeMembership,
        related_name='committee_members',
        blank=True,
        verbose_name="Committees"
    )
    
    # Fix permission conflicts
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
            models.Index(fields=['student_id']),
            models.Index(fields=['email']),
            models.Index(fields=['full_name']),
        ]
    
    def __str__(self):
        return self.student_id
    
    def save(self, *args, **kwargs):
        # Auto-generate student_id if it doesn't exist
        if not self.student_id:
            self.student_id = generate_student_id()
        
        # For superusers, make sure they have an admin student_id
        if self.is_superuser and not self.student_id.startswith('ADMIN_'):
            # Regenerate with ADMIN_ prefix
            while True:
                new_student_id = f"ADMIN_{generate_student_id()}"
                if not User.objects.filter(student_id=new_student_id).exists():
                    self.student_id = new_student_id
                    break
        
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
    
    # Leadership-related properties
    @property
    def is_association_leader(self):
        """Check if user currently holds any association leadership position"""
        return self.leadership_assignments.filter(is_active=True).exists()
    
    @property
    def current_leadership_assignment(self):
        """Get user's current association leadership assignment, if any"""
        # FIX 3: Renamed for clarity - this is the assignment, not just the position
        return self.leadership_assignments.filter(is_active=True).first()
    
    @property
    def leadership_history(self):
        """Get user's complete leadership history"""
        return self.leadership_assignments.all().order_by('-start_date')
    
    # Committee-related properties
    @property
    def active_committees(self):
        """Get user's active committee memberships"""
        return self.committee_memberships.filter(is_active=True).select_related('committee')
    
    # Role-based properties (for templates)
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


class Profile(models.Model):
    """Extended profile information for all users"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="User"
    )
    
    # Add gender field
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='P',
        verbose_name="Gender"
    )
    
    course = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Course/Department",
        help_text="e.g., Computer Science, Business Administration"
    )
    
    batch = models.CharField(
        max_length=10,
        verbose_name="Batch Year",
        help_text="Format: YYYY or YYYY-YYYY"
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
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, verbose_name="Address")
    
    # Academic Information
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Graduation Year"
    )
    
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
    
    # Social Links
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn Profile")
    github_url = models.URLField(blank=True, verbose_name="GitHub Profile")
    portfolio_url = models.URLField(blank=True, verbose_name="Portfolio Website")
    
    # Status
    is_public = models.BooleanField(
        default=True,
        verbose_name="Public Profile",
        help_text="If checked, profile will be visible in directory"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__full_name']
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        indexes = [
            models.Index(fields=['batch']),
            models.Index(fields=['graduation_year']),
            models.Index(fields=['is_public']),
            models.Index(fields=['gender']),  # Added index for gender queries
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.batch}"
    
    @property
    def name(self):
        return self.user.full_name
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def student_id(self):
        return self.user.student_id
    
    @property
    def campus_name(self):
        return self.campus.name if self.campus else "N/A"
    
    @property
    def gender_display(self):
        """Return the human-readable gender value"""
        return dict(self.GENDER_CHOICES).get(self.gender, 'Not specified')
    
    @property
    def is_association_leader(self):
        """Convenience property to check if user is a leader"""
        return self.user.is_association_leader
    
    @property
    def current_leadership_info(self):
        """Get current leadership information, if any"""
        assignment = self.user.current_leadership_assignment
        if assignment:
            return {
                'title': assignment.position.display_title,
                'start_date': assignment.start_date,
                'is_current': assignment.is_current
            }
        return None
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.user.roles.exists():
            default_role = Role.objects.filter(is_default=True).first()
            if default_role:
                self.user.roles.add(default_role)
            else:
                alumni_role, created = Role.objects.get_or_create(name='Alumni')
                self.user.roles.add(alumni_role)


class AuditLog(models.Model):
    """Audit log for tracking user activities"""
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
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name="User"
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
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.student_id if self.user else 'Unknown'} - {self.action} - {self.timestamp}"

















