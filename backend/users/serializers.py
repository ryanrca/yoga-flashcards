from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                 'daily_email_enabled', 'email_verified', 'date_joined', 'is_active', 'last_login']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login']
    
    def update(self, instance, validated_data):
        """Allow admins to update user role and active status."""
        # Only allow role updates if user is admin
        if 'role' in validated_data:
            request = self.context.get('request')
            if request and hasattr(request, 'user') and request.user.role != 'admin':
                validated_data.pop('role')
        
        return super().update(instance, validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']

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
            # Use email to find user, then authenticate with username
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
                
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return data


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
                 'is_active', 'daily_email_enabled', 'email_verified', 'date_joined', 'last_login', 'password']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login']
    
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
