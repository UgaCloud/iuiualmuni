from atexit import register
from os import name
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('events/', views.event, name = 'event'),
    path('gallery/', views.gallery, name='gallery'),
    path('single-album/', views.gallery_single, name='gallery_single'),
    path('directory/', views.event, name = 'directory'),
    path('career/', views.career, name='career'),
    

    path('association-heads/', views.association_heads_view, name='association_heads'),
    path('committee-heads/', views.committee_heads_view, name='committee_heads'),
    # path('committee/', views.committee, name='committee'),

    path('members/', views.regular_members_view, name='members'),


    # path('members/', views.MemberListView.as_view(), name='members_list'),    
  
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
]