from django import forms
from .models import Comment, profile, Post
from django.contrib.auth.forms import UserCreationForm

class profileForm(forms.ModelForm):
  class Meta:
    model  = profile
    fields = ['display_name', 'bio']   # Allow editing display name and bio
# user is assigned in the view, not the form

class PostForm(forms.ModelForm):
  class Meta:
    model  = Post
    fields = ['content']   # Only show the content field to users
# author is assigned in the view, not the form

class CommentForm(forms.ModelForm):
  class Meta:
    model  = Comment
    fields = ['content']   # Only show the content field to users
# author and post are assigned in the view, not the form
