from django.urls import path
from .views import profile , RegisterView
from . import views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='registration'),
    path('profile/', profile, name='users-profile'),
    path('user/<int:user_id>/', views.view_user, name='view_user'),
    path('', views.views.accounts_views.index, name='index')
]