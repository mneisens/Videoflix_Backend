from django.urls import path
from . import views

urlpatterns = [
    path('preview/password-reset/', views.password_reset_preview, name='password_reset_preview'),
]
