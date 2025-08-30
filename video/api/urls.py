from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.TestView.as_view(), name='test'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.ActivateAccountView.as_view(), name='activate_account'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', views.PasswordConfirmView.as_view(), name='password_confirm'),
]
