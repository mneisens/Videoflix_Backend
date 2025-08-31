from django.urls import path
from . import views

urlpatterns = [
    path('csrf-token/', views.CSRFTokenView.as_view(), name='csrf_token'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.ActivateAccountView.as_view(), name='activate_account'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', views.PasswordConfirmView.as_view(), name='password_confirm'),
    path('video/', views.VideoListView.as_view(), name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', views.HLSManifestView.as_view(), name='hls_manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment_name>', views.HLSVideoSegmentView.as_view(), name='hls_segment'),
    path('video/<int:movie_id>/<str:resolution>/', views.VideoView.as_view(), name='video'),
]
