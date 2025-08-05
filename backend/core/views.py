from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from flashcards.services import DailyCardService


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for Kubernetes readiness probes."""
    return JsonResponse({'status': 'healthy'})


@api_view(['GET'])
@permission_classes([AllowAny])
def daily_card(request):
    """Get the card of the day - available to all users."""
    card = DailyCardService.get_daily_card()
    if card:
        from flashcards.serializers import FlashcardSerializer
        serializer = FlashcardSerializer(card)
        return Response(serializer.data)
    else:
        return Response({'message': 'No cards available'}, status=404)
