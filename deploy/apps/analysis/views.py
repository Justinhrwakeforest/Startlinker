from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import PitchDeckAnalysis
from .serializers import (
    PitchDeckAnalysisSerializer,
    PitchDeckUploadSerializer,
    AnalysisListSerializer
)
from .permissions import IsProSubscriber
from .tasks import analyze_deck


class PitchDeckUploadView(APIView):
    """Handle pitch deck upload and trigger analysis."""
    permission_classes = [IsAuthenticated, IsProSubscriber]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        serializer = PitchDeckUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            analysis = serializer.save()
            
            # Trigger async analysis
            analyze_deck.delay(analysis.id)
            
            return Response({
                'id': analysis.id,
                'status': analysis.status,
                'message': 'Your pitch deck has been uploaded and is being analyzed.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PitchDeckAnalysisDetailView(generics.RetrieveAPIView):
    """Get analysis details and results."""
    permission_classes = [IsAuthenticated]
    serializer_class = PitchDeckAnalysisSerializer
    
    def get_object(self):
        analysis_id = self.kwargs.get('pk')
        return get_object_or_404(
            PitchDeckAnalysis,
            id=analysis_id,
            user=self.request.user
        )


class PitchDeckAnalysisListView(generics.ListAPIView):
    """List user's pitch deck analyses."""
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisListSerializer
    
    def get_queryset(self):
        return PitchDeckAnalysis.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class AnalysisFeatureView(APIView):
    """
    Show feature information for non-pro users.
    This endpoint is accessible to all authenticated users.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        is_pro = hasattr(request.user, 'subscription') and request.user.subscription.is_active_pro
        
        return Response({
            'is_pro': is_pro,
            'feature': {
                'name': 'AI-Powered Pitch Deck Analysis',
                'description': 'Get instant, actionable feedback on your pitch deck from our AI analyst.',
                'benefits': [
                    'Slide-by-slide analysis with specific feedback',
                    'Overall score and investor readiness assessment',
                    'Design and clarity ratings for each slide',
                    'Identification of missing elements',
                    'Actionable suggestions for improvement'
                ],
                'requirements': 'Founder Pro subscription required'
            }
        })
