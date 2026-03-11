import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import PostForm, CommentForm, profileForm, CustomUserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import Profile, Post, Comment
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.urls import reverse
from .utils import send_html_email
from django.core.mail import send_mail
from decouple import config


def _get_profile_for(user):
    #ensure user has a profile, create if missing
    prof, _ = Profile.objects.get_or_create(user=user, defaults={'display_name': user.username})
    return prof


def home(request):
    """Root entry point. Always send unauthenticated users to login page,
    authenticated users to their feed."""
    if request.user.is_authenticated:
        return redirect('feed')
    return render(request, 'social/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('feed')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()  # Save only once

            try:
                send_html_email(
                    subject='Welcome to ConnectHub! 🎉',
                    template_name='emails/welcome_email.html',
                    context={'username': user.username},
                    recipient_email=user.email
                )
            except Exception as e:
                print("Email failed:", e)

            login(request, user)

            messages.success(
                request,
                f'Welcome, {user.username}! Account created successfully.'
            )

            return redirect('feed')

        else:
            messages.error(request, 'Please fix the errors below.')

    else:
        form = CustomUserCreationForm()

    return render(request, 'social/register.html', {'form': form})

@login_required
@require_POST
def follow(request, username):
    target_user = get_object_or_404(User, username=username)
    profile = _get_profile_for(request.user)
    target_profile = _get_profile_for(target_user)
    if profile == target_profile:
        # can't follow yourself, just go back
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))
    
    is_following = target_profile in profile.following.all()
    
    if is_following:
        profile.following.remove(target_profile)
    else:
        # New follow - send notification email
        profile.following.add(target_profile)
        
        # Send "new follower" email to the target user
        if target_user.email:
            send_mail(
                subject=f'{request.user.username} is now following you! 🎉',
                # template_name='emails/new_follower.html',
                message=f'Hi {target_user.username},\n\n{request.user.username} has started following you on ConnectHub! Check out their profile and posts.\n\nBest,\nThe ConnectHub Team',
                # context={
                #     'follower_username': request.user.username,
                #     'profile_url': f'https://{request.get_host()}/profile/{request.user.username}/'
                # },
                from_email=config('EMAIL_HOST_USER', default=''),
                # recipient_email=target_user.email,
                recipient_list=[target_user.email],
                fail_silently=False  # Don't raise error if email fails to send

            )
            
    
    # return to referring page so follow works from different contexts
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))



@login_required
def feed(request):
    followed_profiles = request.user.profile.following.all()
    followed_users    = User.objects.filter(profile__in=followed_profiles)
    posts = Post.objects.filter(
        author__in=list(followed_users) + [request.user]
    ).order_by('-created_at').select_related('author', 'author__profile')

    # suggested users: those the current user does *not* follow (and not themself)
    suggestions = User.objects.exclude(pk__in=followed_users.values_list('pk', flat=True))
    suggestions = suggestions.exclude(pk=request.user.pk)
    # random ordering so that the list feels dynamic
    suggestions = suggestions.order_by('?')[:5]

    return render(request, 'social/feed.html', {
        'posts': posts,
        'suggestions': suggestions,
    })

@login_required
def discover(request):
    posts = Post.objects.all().order_by('-created_at').select_related('author')
    return render(request, 'social/discover.html', {'posts': posts})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
        
            post.author = request.user
            post.save()
            messages.success(request, 'Post created.')
              
            return redirect('profile')
    else:
        form = PostForm()
    return render(request, 'social/create_post.html', {'form': form})


@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('feed')))


def _profile_context_for_user(viewer, target_user):
    # returns context dict used by both user_profile and my_profile
    user_posts = Post.objects.filter(author=target_user)
    user_comments = Comment.objects.filter(author=target_user)
    post_count = user_posts.count()
    comment_count = user_comments.count()
    # follower/following counts for displaying on profile page
    target_prof = _get_profile_for(target_user)
    follower_count = target_prof.followers.count()
    following_count = target_prof.following.count()
    is_following = False
    if viewer.is_authenticated and viewer != target_user:
        viewer_prof = _get_profile_for(viewer)
        is_following = target_prof in viewer_prof.following.all()
    return {
        'target_user': target_user,
        'post_count': post_count,
        'comment_count': comment_count,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
        'posts': user_posts.order_by('-created_at')
    }


def user_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    context = _profile_context_for_user(request.user, target_user)
    return render(request, 'social/profile.html', context)


@login_required
def profile(request):
    prof = _get_profile_for(request.user)
    if request.method == 'POST':
        form = profileForm(request.POST, request.FILES, instance=prof)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = profileForm(instance=prof)
    context = _profile_context_for_user(request.user, request.user)
    context['form'] = form
    return render(request, 'social/profile.html', context)

@login_required

def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        # BOTH request.POST and request.FILES must be passed
        form = profileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # If a new avatar was uploaded AND an old one exists, delete the old file
            if 'avatar' in request.FILES and profile.avatar:
                old_path = profile.avatar.path  # Full path on disk
                if os.path.isfile(old_path):
                    os.remove(old_path)         # Delete old file
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = profileForm(instance=profile)  # Pre-fill with current data
    return render(request, 'social/edit_profile.html', {'form': form})

@login_required
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    post.delete()
    return redirect('feed')


@login_required
@require_POST
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    comment.delete()
    return redirect('feed')


@login_required
def edit_post(request, pk):
    """Allow the author to update a post during a short grace period.

    - only the original author may edit
    - editing is permitted for fifteen minutes after creation
    """
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        messages.error(request, "You don't have permission to edit that post.")
        return redirect('feed')

    # enforce 15‑minute window using model helper
    if not post.can_edit(request.user):
        messages.error(request, "The editing window for this post has expired.")
        return redirect('feed')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated.')
            return redirect('feed')
    else:
        form = PostForm(instance=post)

    return render(request, 'social/edit_post.html', {'form': form, 'post': post})


def search(request):
    query = request.GET.get('q', '') if request.method == 'GET' else request.POST.get('q', '')
    users = User.objects.filter(username__icontains=query)
    posts = Post.objects.filter(content__icontains=query).select_related('author')
    return render(request, 'social/search_results.html', {
        'query': query,
        'users': users,
        'posts': posts
    })


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.likes.count()})
    return redirect(request.META.get('HTTP_REFERER', reverse('home')))

