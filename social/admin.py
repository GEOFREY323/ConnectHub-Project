from django.contrib import admin

# Register your models here.
from .models import profile, Post, Comment
admin.site.register(profile)
admin.site.register(Post)
admin.site.register(Comment)