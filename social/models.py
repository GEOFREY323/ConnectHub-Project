# Create your models here.
from django.db import models
from django.contrib.auth.models import User  # Import the User model

class profile(models.Model):
    user      = models.OneToOneField(User, verbose_name=("User"), on_delete=models.CASCADE)
    display_name = models.CharField(max_length=60, blank=True)  # spec: max_length=60
    bio          = models.TextField(blank=True)
    joined_at   = models.DateTimeField(auto_now_add=True)
    following  = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    def __str__(self):
        # display_name may be blank, fall back to username
        return self.display_name or self.user.username
    class Meta:
        ordering = ['-joined_at']  # Newest profiles first


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=280)  # spec: 280 char limit
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    def __str__(self):
        # use display_name if available
        name = self.author.profile.display_name if hasattr(self.author, 'profile') else self.author.username
        return f"{name}: {self.content[:30]}..."
    class Meta:
        ordering = ['-created_at']  # Newest posts first


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)  # spec: max_length=500
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        name = self.author.profile.display_name if hasattr(self.author, 'profile') else self.author.username
        return f"{name} on {self.post.author.username}'s post: {self.content[:30]}..."  # Show first 30 chars
    class Meta:
        ordering = ['created_at']  # Oldest comments first



