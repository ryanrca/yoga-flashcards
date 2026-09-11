from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                 'daily_email_enabled', 'email_verified', 'date_joined', 'is_active', 'last_login',
                 'is_deleted', 'deleted_at']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'is_deleted', 'deleted_at']
    
    def update(self, instance, validated_data):
        """Allow admins to update user role and active status."""
        # Only allow role updates if the requesting user is an admin. Fails
        # closed: with no request in context we cannot prove admin, so the
        # role change is dropped rather than allowed through.
        if 'role' in validated_data:
            request = self.context.get('request')
            requester = getattr(request, 'user', None)
            if not (requester and requester.is_authenticated and requester.is_admin()):
                validated_data.pop('role')
        
        return super().update(instance, validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate_email(self, value):
        # Includes soft-deleted accounts: the row still owns the address, and an
        # admin can restore it. Registering over it would strand the old account.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with that email address already exists')
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        
        # Generate username from email (use part before @)
        email = validated_data['email']
        base_username = email.split('@')[0]
        username = base_username
        
        # Handle duplicate usernames by appending numbers
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        validated_data['username'] = username
        
        user = User.objects.create_user(**validated_data)
        # Create user profile
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            # Use email to find the account, then authenticate with its username.
            # Deleted accounts are excluded outright so they can never be logged
            # back into. filter().first() rather than get(): email is not unique
            # on the model, and a duplicate must not raise MultipleObjectsReturned.
            user_obj = User.objects.filter(email=email, is_deleted=False).order_by('pk').first()
            user = None
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)

            if not user:
                # Same message whether the account is missing, deleted or the
                # password is wrong, so login cannot be used to enumerate accounts.
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for a user editing their own profile.

    Deliberately narrow: `role` and `is_active` are not writable here. The
    previous code reused UserSerializer, whose role guard reads
    self.context['request'] -- the profile view passed no context, so the
    guard never fired and any user could PUT {"role": "admin"} on themselves.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'daily_email_enabled']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('That email address is already in use')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing the logged-in user's password."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'avatar', 'favorite_cards']


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user management with full control."""
    
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    username = serializers.CharField(read_only=True)  # Auto-generated from email
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                 'is_active', 'daily_email_enabled', 'email_verified', 'date_joined', 'last_login',
                 'password', 'is_deleted', 'deleted_at']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'is_deleted', 'deleted_at']
    
    def create(self, validated_data):
        """Create user with password, auto-generating username from email."""
        password = validated_data.pop('password', None)
        
        # Always generate username from email
        email = validated_data['email']
        base_username = email.split('@')[0]
        username = base_username
        
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        validated_data['username'] = username
        
        user = User.objects.create_user(**validated_data, password=password)
        UserProfile.objects.create(user=user)
        return user
    
    def update(self, instance, validated_data):
        """Update user, optionally changing password."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
