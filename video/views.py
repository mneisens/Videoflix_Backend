from django.shortcuts import render
from django.http import HttpResponse


def password_reset_preview(request):
    """Zeigt eine Vorschau der Passwort-Reset E-Mail an"""
    return render(request, 'video/password_reset_preview.html')
