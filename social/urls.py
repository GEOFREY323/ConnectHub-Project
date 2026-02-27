from django.urls import path
from . import views

urlpatterns = [
    # Auth & Home
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    

    path('feed/', views.feed, name='feed'),
    path('discover/', views.discover, name='discover'),


    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('profile/<str:username>/follow/', views.follow, name='follow'),

    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),


    path('profile/', views.my_profile, name='my_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),


    path('search/', views.search, name='search'),
]