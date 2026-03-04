import os

from django import forms
from .models import Comment, Profile, Post
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    """Custom registration form that includes email field"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='We\'ll send you a welcome email to confirm your account.'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }
    
    def clean_email(self):
        """Validate that email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email
    
    def save(self, commit=True):
        """Save user with email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class profileForm(forms.ModelForm):
  class Meta:
    model  = Profile
    fields = ['display_name', 'bio', 'avatar']   # display name, bio, and avatar
    widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell people about yourself...'}),
            'display_name': forms.TextInput(attrs={'placeholder': 'Your display name'}),
        }    
  def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # 1. Check file size (limit to 2MB)
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if avatar.size > max_size:
                raise forms.ValidationError(
                    f'Image file too large. Maximum size is 2MB. '
                    f'Your file is {avatar.size // 1024 // 1024:.1f}MB.'
                )
            # 2. Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'Unsupported file type: {ext}. '
                    f'Allowed types: {', '.join(allowed_extensions)}'
                )
        print(avatar)
        return avatar

# user is assigned in the view, not the form

class PostForm(forms.ModelForm):
  class Meta:
    model  = Post
    fields = ['content', 'image']   # Only show the content and image fields to users
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # 1. Check file size (limit to 2MB)
            max_size = 2 * 1024 * 1024  # 2MB in bytes
            if image.size > max_size:
                raise forms.ValidationError(
                    f'Image file too large. Maximum size is 2MB. '
                    f'Your file is {image.size // 1024 // 1024:.1f}MB.'
                )
            # 2. Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'Unsupported file type: {ext}. '
                    f'Allowed types: {', '.join(allowed_extensions)}'
                )
        return image
# author is assigned in the view, not the form

class CommentForm(forms.ModelForm):
  class Meta:
    model  = Comment
    fields = ['content']   # Only show the content field to users
# author and post are assigned in the view, not the form
