from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.PitchDeckAnalysisListView.as_view(), name='analysis-list'),
    path('upload/', views.PitchDeckUploadView.as_view(), name='analysis-upload'),
    path('feature/', views.AnalysisFeatureView.as_view(), name='analysis-feature'),
    path('<int:pk>/', views.PitchDeckAnalysisDetailView.as_view(), name='analysis-detail'),
]