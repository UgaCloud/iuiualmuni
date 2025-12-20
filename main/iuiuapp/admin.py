# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import User, Profile, Role, Campus, AuditLog, Committee, CommitteeMembership, LeadershipPosition, AssociationLeadership


class UserCreationForm(forms.ModelForm):
    """Form for creating users in admin - without requiring student_id"""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'full_name')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileInline(admin.StackedInline):
    """Inline profile editing within User admin"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    max_num = 1
    min_num = 1
    
    fieldsets = (
        ('Academic Information', {
            'fields': ('course', 'batch', 'campus', 'graduation_year')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Professional Information', {
            'fields': ('current_job', 'current_company')
        }),
        ('Social Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Profile Details', {
            'fields': ('bio', 'photo', 'is_public')
        }),
    )


class CommitteeMembershipInline(admin.TabularInline):
    """Inline committee memberships within User admin"""
    model = CommitteeMembership
    extra = 1
    verbose_name = 'Committee Membership'
    verbose_name_plural = 'Committee Memberships'
    fields = ('committee', 'role', 'start_date', 'end_date', 'is_active')
    autocomplete_fields = ['committee']


class AssociationLeadershipInline(admin.TabularInline):
    """Inline association leadership assignments within User admin"""
    model = AssociationLeadership
    extra = 0
    max_num = 1  # Users can only have one active leadership position
    verbose_name = 'Association Leadership'
    verbose_name_plural = 'Association Leadership Assignments'
    fields = ('position', 'start_date', 'end_date', 'is_active', 'notes')
    readonly_fields = ('is_active',)
    
    def get_queryset(self, request):
        """Only show active leadership assignments by default"""
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with leadership and committee management"""
    model = User
    add_form = UserCreationForm
    
    list_display = ('student_id', 'email', 'full_name', 'is_active', 'is_association_leader_display', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'roles')
    search_fields = ('student_id', 'email', 'full_name')
    ordering = ('-date_joined',)
    
    # Fields for viewing user
    fieldsets = (
        ('Authentication', {
            'fields': ('student_id', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('full_name',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'roles')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
    )
    
    # Fields for creating user (without student_id)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified'),
        }),
    )
    
    # Inlines for profile, committee memberships, and leadership
    inlines = [ProfileInline, CommitteeMembershipInline, AssociationLeadershipInline]
    
    readonly_fields = ('student_id', 'date_joined', 'last_login', 'updated_at')
    
    def get_inline_instances(self, request, obj=None):
        """Only show inlines when editing existing user"""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    def is_association_leader_display(self, obj):
        """Display leadership status in list view"""
        return obj.is_association_leader
    is_association_leader_display.short_description = 'Association Leader'
    is_association_leader_display.boolean = True
    
    def save_model(self, request, obj, form, change):
        """
        Auto-generate student ID for new users if not provided
        """
        if not change and not obj.student_id:
            from .models import generate_student_id
            # Generate unique student ID
            while True:
                new_id = generate_student_id()
                if not User.objects.filter(student_id=new_id).exists():
                    obj.student_id = new_id
                    break
        super().save_model(request, obj, form, change)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile admin"""
    list_display = ('user_full_name', 'student_id', 'gender_display', 'course', 'batch', 'campus_name', 'is_public', 'is_association_leader_display')
    list_filter = ('gender', 'campus', 'batch', 'is_public', 'created_at')
    search_fields = ('user__full_name', 'user__student_id', 'user__email', 'course', 'batch')
    list_editable = ('is_public',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'student_id_display', 'email_display', 'gender', 'is_association_leader_field')
        }),
        ('Academic Information', {
            'fields': ('course', 'batch', 'campus', 'graduation_year')
        }),
        ('Professional Information', {
            'fields': ('current_job', 'current_company')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address', 'linkedin_url', 'github_url', 'portfolio_url')
        }),
        ('Profile Details', {
            'fields': ('bio', 'photo_preview', 'photo', 'is_public')
        }),
    )
    
    readonly_fields = ('student_id_display', 'email_display', 'photo_preview', 'is_association_leader_field')
    
    def user_full_name(self, obj):
        return obj.user.full_name
    user_full_name.short_description = 'Name'
    user_full_name.admin_order_field = 'user__full_name'
    
    def student_id(self, obj):
        return obj.user.student_id
    student_id.short_description = 'Student ID'
    student_id.admin_order_field = 'user__student_id'
    
    def gender_display(self, obj):
        return obj.gender_display
    gender_display.short_description = 'Gender'
    gender_display.admin_order_field = 'gender'
    
    def student_id_display(self, obj):
        return obj.user.student_id
    student_id_display.short_description = 'Student ID'
    
    def email_display(self, obj):
        return obj.user.email
    email_display.short_description = 'Email'
    
    def campus_name(self, obj):
        return obj.campus.name if obj.campus else "N/A"
    campus_name.short_description = 'Campus'
    
    def is_association_leader_display(self, obj):
        return obj.is_association_leader
    is_association_leader_display.short_description = 'Association Leader'
    is_association_leader_display.boolean = True
    
    def is_association_leader_field(self, obj):
        """Display leadership status in detail view"""
        if obj.is_association_leader:
            assignment = obj.user.current_leadership_assignment
            if assignment:
                return f"Yes - {assignment.position.display_title}"
        return "No"
    is_association_leader_field.short_description = 'Association Leadership'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.photo.url)
        return "No photo"
    photo_preview.short_description = 'Photo Preview'
    
    # Add actions for gender analysis
    actions = ['export_gender_stats']
    
    def export_gender_stats(self, request, queryset):
        """Export gender statistics for selected profiles"""
        from django.http import HttpResponse
        import csv
        
        gender_counts = {}
        for profile in queryset:
            gender_counts[profile.gender] = gender_counts.get(profile.gender, 0) + 1
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="gender_statistics.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Gender', 'Count', 'Percentage'])
        
        total = queryset.count()
        gender_map = dict(Profile.GENDER_CHOICES)
        
        for gender_code, count in gender_counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            writer.writerow([
                gender_map.get(gender_code, 'Unknown'),
                count,
                f"{percentage:.2f}%"
            ])
        
        writer.writerow(['TOTAL', total, '100%'])
        
        self.message_user(request, f"Exported gender statistics for {total} profiles.")
        return response
    
    export_gender_stats.short_description = "Export gender statistics"


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Role admin - for permissions only"""
    list_display = ('name', 'is_default', 'user_count')
    list_filter = ('is_default',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    actions = ['set_as_default']
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Number of Users'
    
    @admin.action(description='Set as default role')
    def set_as_default(self, request, queryset):
        """Set selected role as default (only one can be default)"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one role.", level='error')
            return
        
        # Remove default from all roles
        Role.objects.filter(is_default=True).update(is_default=False)
        
        # Set selected as default
        role = queryset.first()
        role.is_default = True
        role.save()
        self.message_user(request, f"'{role.name}' is now the default role.")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    """Campus admin"""
    list_display = ('name', 'code', 'profile_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'address')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    def profile_count(self, obj):
        return obj.profiles.count()
    profile_count.short_description = 'Number of Profiles'


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    """Committee admin"""
    list_display = ('name', 'slug', 'member_count', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'description')
    list_editable = ('is_active', 'order')
    ordering = ('order', 'name')
    prepopulated_fields = {'slug': ('name',)}
    
    def member_count(self, obj):
        return obj.members.filter(committeemembership__is_active=True).count()
    member_count.short_description = 'Active Members'


@admin.register(CommitteeMembership)
class CommitteeMembershipAdmin(admin.ModelAdmin):
    """Committee Membership admin"""
    list_display = ('user', 'committee', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'committee', 'role', 'start_date')
    search_fields = ('user__full_name', 'user__student_id', 'committee__name', 'role')
    list_editable = ('is_active', 'role')
    ordering = ('-start_date',)
    autocomplete_fields = ['user', 'committee']


@admin.register(LeadershipPosition)
class LeadershipPositionAdmin(admin.ModelAdmin):
    """Leadership Position admin"""
    list_display = ('display_title', 'code', 'order', 'is_active', 'current_leader', 'assignment_count')
    list_filter = ('is_active',)
    search_fields = ('code', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'code')
    
    def current_leader(self, obj):
        """Show current active leader for this position"""
        assignment = obj.assignments.filter(is_active=True).first()
        if assignment:
            return assignment.user.full_name
        return "Vacant"
    current_leader.short_description = 'Current Leader'
    
    def assignment_count(self, obj):
        return obj.assignments.count()
    assignment_count.short_description = 'Total Assignments'


@admin.register(AssociationLeadership)
class AssociationLeadershipAdmin(admin.ModelAdmin):
    """Association Leadership admin"""
    list_display = ('user', 'position_display', 'start_date', 'end_date', 'is_active', 'is_current')
    list_filter = ('is_active', 'position', 'start_date')
    search_fields = ('user__full_name', 'user__student_id', 'position__code', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('position__order', '-start_date')
    autocomplete_fields = ['user', 'position']
    
    def position_display(self, obj):
        return obj.position.display_title
    position_display.short_description = 'Position'
    position_display.admin_order_field = 'position__order'
    
    def is_current(self, obj):
        return obj.is_current
    is_current.short_description = 'Current'
    is_current.boolean = True
    
    fieldsets = (
        ('Leadership Assignment', {
            'fields': ('user', 'position', 'is_active')
        }),
        ('Term Details', {
            'fields': ('start_date', 'end_date', 'notes')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """AuditLog admin - read only"""
    list_display = ('user_display', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__full_name', 'user__student_id', 'ip_address')
    readonly_fields = ('user_display', 'action', 'details', 'ip_address', 'user_agent', 'timestamp')
    ordering = ('-timestamp',)
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.full_name} ({obj.user.student_id})"
        return "Unknown User"
    user_display.short_description = 'User'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Optional: Customize admin site headers
admin.site.site_header = 'Alumni Association System Admin'
admin.site.site_title = 'Alumni Association System'
admin.site.index_title = 'Welcome to Alumni Association Administration'