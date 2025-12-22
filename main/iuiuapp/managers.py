from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom manager for User model with Member integration"""
    
    def create_user(self, email, full_name, password=None, **extra_fields):
        """
        Create and save a regular user with given email and full name.
        Uses existing Member if one exists with the email, otherwise creates a new Member.
        """
        if not email:
            raise ValueError('Email is required')
        if not full_name:
            raise ValueError('Full name is required')
        
        email = self.normalize_email(email)
        
        # Import here to avoid circular import
        from .models import Member, generate_member_id, generate_student_id
        
        # Check if Member already exists with this email
        try:
            member = Member.objects.get(email=email)
            # Check if Member already has a user account
            if hasattr(member, 'user_account'):
                raise ValueError(f'Member with email {email} already has a user account')
        except Member.DoesNotExist:
            # Generate unique member ID
            while True:
                member_id = generate_member_id()
                if not Member.objects.filter(member_id=member_id).exists():
                    break
            
            # Generate student ID
            student_id = generate_student_id()
            
            # Create Member first
            member = Member.objects.create(
                member_id=member_id,
                student_id=student_id,
                full_name=full_name,
                email=email,
                is_active_member=True
            )
        
        # Create User linked to Member
        user = self.model(
            member=member,
            email=email,
            full_name=full_name,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, full_name, password=None, **extra_fields):
        """
        Create superuser - creates Member with admin prefix.
        """
        if not email:
            raise ValueError('Email is required')
        if not full_name:
            raise ValueError('Full name is required')
        
        email = self.normalize_email(email)
        
        # Set superuser fields
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # Import here to avoid circular import
        from .models import Member, generate_member_id, generate_student_id
        
        # Generate admin member ID
        while True:
            member_id = f"ADMIN_{generate_member_id()}"
            if not Member.objects.filter(member_id=member_id).exists():
                break
        
        # Generate admin student ID
        student_id = f"ADMIN_{generate_student_id()}"
        
        # Create Member with admin prefix
        member = Member.objects.create(
            member_id=member_id,
            student_id=student_id,
            full_name=full_name,
            email=email,
            batch="ADMIN",
            course="Administration",
            is_active_member=True
        )
        
        # Create User linked to Member
        user = self.model(
            member=member,
            email=email,
            full_name=full_name,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            
        user.save(using=self._db)
        return user