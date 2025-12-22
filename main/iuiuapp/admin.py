from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django import forms
from .models import Member, User, Profile, Role, Campus, AuditLog, Committee, CommitteeMembership, LeadershipPosition, AssociationLeadership


class UserCreationForm(forms.ModelForm):
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
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            full_name=self.cleaned_data["full_name"],
            password=self.cleaned_data["password1"]
        )
        self.instance = user
        return user

    def save_m2m(self):
        # No-op since add form doesn't handle m2m fields
        pass



class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    max_num = 1
    min_num = 1
    
    fieldsets = (
        ('Profile Details', {
            'fields': ('gender', 'campus', 'bio', 'photo', 'is_public')
        }),
    )


class CommitteeMembershipInline(admin.TabularInline):
    model = CommitteeMembership
    extra = 1
    verbose_name = 'Committee Membership'
    verbose_name_plural = 'Committee Memberships'
    fields = ('committee', 'role', 'start_date', 'end_date', 'is_active')
    autocomplete_fields = ['committee']


class AssociationLeadershipInline(admin.TabularInline):
    model = AssociationLeadership
    extra = 0
    max_num = 1
    verbose_name = 'Association Leadership'
    verbose_name_plural = 'Association Leadership Assignments'
    fields = ('position', 'start_date', 'end_date', 'is_active', 'notes')
    readonly_fields = ('is_active',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    add_form = UserCreationForm
    
    list_display = ('member_id_display', 'email', 'full_name', 'is_active', 'is_association_leader_display', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'roles')
    search_fields = ('member__member_id', 'email', 'full_name', 'member__student_id')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('member', 'email', 'password')
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
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified'),
        }),
    )
    
    inlines = [CommitteeMembershipInline, AssociationLeadershipInline]
    
    readonly_fields = ('date_joined', 'last_login', 'updated_at')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    def is_association_leader_display(self, obj):
        return obj.is_association_leader
    is_association_leader_display.short_description = 'Association Leader'
    is_association_leader_display.boolean = True
    
    def member_id_display(self, obj):
        return obj.member.member_id if hasattr(obj, 'member') else 'N/A'
    member_id_display.short_description = 'Member ID'
    member_id_display.admin_order_field = 'member__member_id'
    
    def save_model(self, request, obj, form, change):
        if not change:
            if not hasattr(obj, 'member'):
                member = Member.objects.create(
                    full_name=obj.full_name,
                    email=obj.email
                )
                obj.member = member
        super().save_model(request, obj, form, change)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'student_id', 'full_name', 'email', 'batch', 'course', 'is_active_member', 'has_user_account')
    list_filter = ('is_active_member', 'batch', 'graduation_year', 'joined_date')
    search_fields = ('member_id', 'student_id', 'full_name', 'email', 'course', 'batch')
    list_editable = ('is_active_member',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Identification', {
            'fields': ('member_id', 'student_id', 'full_name', 'email')
        }),
        ('Academic Information', {
            'fields': ('course', 'batch', 'graduation_year')
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
        ('Membership Status', {
            'fields': ('is_active_member', 'joined_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('member_id', 'student_id', 'created_at', 'updated_at')
    
    def has_user_account(self, obj):
        return hasattr(obj, 'user_account')
    has_user_account.short_description = 'Has User Account'
    has_user_account.boolean = True
    
    inlines = [ProfileInline]
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    actions = ['create_user_account']
    
    @admin.action(description='Create user account for selected members')
    def create_user_account(self, request, queryset):
        created = 0
        for member in queryset:
            if not hasattr(member, 'user_account'):
                try:
                    member.create_user_account()
                    created += 1
                except Exception as e:
                    self.message_user(request, f"Error creating account for {member.email}: {str(e)}", level='error')
        self.message_user(request, f"Created user accounts for {created} members.")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('member_full_name', 'member_id_display', 'gender_display', 'campus_name', 'is_public', 'is_association_leader_display')
    list_filter = ('gender', 'campus', 'is_public', 'created_at')
    search_fields = ('member__full_name', 'member__member_id', 'member__email', 'member__student_id')
    list_editable = ('is_public',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Member Information', {
            'fields': ('member', 'member_id_display', 'email_display', 'gender', 'is_association_leader_field')
        }),
        ('Profile Details', {
            'fields': ('campus', 'bio', 'photo_preview', 'photo', 'is_public')
        }),
    )
    
    readonly_fields = ('member_id_display', 'email_display', 'photo_preview', 'is_association_leader_field')
    
    def member_full_name(self, obj):
        return obj.member.full_name
    member_full_name.short_description = 'Name'
    member_full_name.admin_order_field = 'member__full_name'
    
    def member_id_display(self, obj):
        return obj.member.member_id
    member_id_display.short_description = 'Member ID'
    
    def gender_display(self, obj):
        return obj.gender_display
    gender_display.short_description = 'Gender'
    gender_display.admin_order_field = 'gender'
    
    def email_display(self, obj):
        return obj.member.email
    email_display.short_description = 'Email'
    
    def campus_name(self, obj):
        return obj.campus.name if obj.campus else "N/A"
    campus_name.short_description = 'Campus'
    
    def is_association_leader_display(self, obj):
        return obj.is_association_leader
    is_association_leader_display.short_description = 'Association Leader'
    is_association_leader_display.boolean = True
    
    def is_association_leader_field(self, obj):
        if obj.is_association_leader:
            if hasattr(obj.member, 'user_account'):
                assignment = obj.member.user_account.current_leadership_assignment
                if assignment:
                    return f"Yes - {assignment.position.display_title}"
        return "No"
    is_association_leader_field.short_description = 'Association Leadership'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.photo.url)
        return "No photo"
    photo_preview.short_description = 'Photo Preview'
    
    actions = ['export_gender_stats']
    
    def export_gender_stats(self, request, queryset):
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
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one role.", level='error')
            return
        
        Role.objects.filter(is_default=True).update(is_default=False)
        
        role = queryset.first()
        role.is_default = True
        role.save()
        self.message_user(request, f"'{role.name}' is now the default role.")


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    list_editable = ('is_active',)
    ordering = ('name',)
    
    def profile_count(self, obj):
        return obj.profiles.count()
    profile_count.short_description = 'Number of Profiles'


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
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
    list_display = ('user', 'committee', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'committee', 'role', 'start_date')
    search_fields = ('user__full_name', 'user__member__member_id', 'committee__name', 'role')
    list_editable = ('is_active', 'role')
    ordering = ('-start_date',)
    autocomplete_fields = ['user', 'committee']


@admin.register(LeadershipPosition)
class LeadershipPositionAdmin(admin.ModelAdmin):
    list_display = ('display_title', 'code', 'order', 'is_active', 'current_leader', 'assignment_count')
    list_filter = ('is_active',)
    search_fields = ('code', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'code')
    
    def current_leader(self, obj):
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
    list_display = ('user', 'position_display', 'start_date', 'end_date', 'is_active', 'is_current')
    list_filter = ('is_active', 'position', 'start_date')
    search_fields = ('user__full_name', 'user__member__member_id', 'position__code', 'notes')
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
    list_display = ('user_display', 'member_display', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__full_name', 'user__member__member_id', 'member__full_name', 'member__member_id', 'ip_address')
    readonly_fields = ('user_display', 'member_display', 'action', 'details', 'ip_address', 'user_agent', 'timestamp')
    ordering = ('-timestamp',)
    
    def user_display(self, obj):
        if obj.user:
            if hasattr(obj.user, 'member'):
                return f"{obj.user.full_name} ({obj.user.member.member_id})"
            return f"{obj.user.full_name} (No Member)"
        return "Unknown User"
    user_display.short_description = 'User'
    
    def member_display(self, obj):
        if obj.member:
            return f"{obj.member.full_name} ({obj.member.member_id})"
        return "Unknown Member"
    member_display.short_description = 'Member'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = 'Alumni Association System Admin'
admin.site.site_title = 'Alumni Association System'
admin.site.index_title = 'Welcome to Alumni Association Administration'