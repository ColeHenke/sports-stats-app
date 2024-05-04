from django.urls import path
from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('search/', views.search, name='search'),
  path('login_user/', views.login_user, name='login_user'), 
  path('register/', views.register, name='register'),
  path('logout_user/', views.logout_user, name='logout_user'), 
  path('fetch-scores/', views.fetch_scores, name='fetch-scores'),
]
