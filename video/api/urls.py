from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_view, name='test'),
    path('register/', views.register_user, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('login/', views.login_user, name='login'),
]
