from django.urls import path
from . import views

urlpatterns = [
    path('', views.VideoListView.as_view(), name='video_list'),
    path('<int:movie_id>/<str:resolution>/index.m3u8', views.HLSManifestView.as_view(), name='hls_manifest'),
    path('<int:movie_id>/<str:resolution>/<str:segment>', views.HLSVideoSegmentView.as_view(), name='hls_segment'),
    path('queue/status/', views.QueueStatusView.as_view(), name='queue_status'),
    path('queue/manage/', views.QueueManagementView.as_view(), name='queue_manage'),
    path('<int:video_id>/direct/', views.DirectVideoView.as_view(), name='direct_video'),
]
