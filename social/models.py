# Create your models here.
from email.policy import default

from django.db import models
from django.contrib.auth.models import User  # Import the User model

class Profile(models.Model):
    user      = models.OneToOneField(User, verbose_name=("User"), on_delete=models.CASCADE)
    display_name = models.CharField(max_length=60, blank=True)  # spec: max_length=60
    bio          = models.TextField(blank=True)
    joined_at   = models.DateTimeField(auto_now_add=True)
    following  = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)
    
    avatar = models.ImageField(
    upload_to='profile_pics/',
    blank=True,
    null=True
    )

    cover_photo = models.ImageField(
        upload_to='cover_pics/',
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default_avatar.png'  # Fallback URL for default avatar
    def get_cover_url(self):
        """Return the URL of the cover photo, or a fallback gradient."""
        if self.cover_photo and hasattr(self.cover_photo, 'url'):
            return self.cover_photo.url
        return '/static/images/default_cover_avatar.png'
    class Meta:
        ordering = ['-joined_at']  # Newest profiles first


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=280)  # spec: 280 char limit
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='post_images/',blank=True,null=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    def __str__(self):
        # use display_name if available
        name = self.author.profile.display_name if hasattr(self.author, 'profile') else self.author.username
        return f"{name}: {self.content[:30]}..."
    class Meta:
        ordering = ['-created_at']  # Newest posts first

    def can_edit(self, user):
        """Return True if the given user may edit this post.

        Only the author is allowed, and only within 15 minutes of creation.
        """
        if user != self.author:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.created_at <= timedelta(minutes=15)


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



