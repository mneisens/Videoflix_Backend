from django.urls import path
from . import views

urlpatterns = [
    path('video/', views.VideoListView.as_view(), name='video_list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', views.HLSManifestView.as_view(), name='hls_manifest'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment_name>', views.HLSVideoSegmentView.as_view(), name='hls_segment'),
    path('video/<int:video_id>/direct/', views.DirectVideoView.as_view(), name='direct_video'),
]
