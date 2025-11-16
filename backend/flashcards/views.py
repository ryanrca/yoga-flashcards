from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Flashcard, Tag
from .serializers import FlashcardSerializer, TagSerializer, FlashcardVersionHistorySerializer
from .permissions import IsCuratorOrAdmin
from .pagination import CardPagination


class FlashcardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing flashcards."""
    
    serializer_class = FlashcardSerializer
    pagination_class = CardPagination
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsCuratorOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Return active live flashcards with filtering and search."""
        queryset = Flashcard.objects.filter(is_active=True, is_live=True).select_related('created_by').prefetch_related('tags')
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(phrase__icontains=search) |
                Q(definition__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()
        
        # Tag filtering
        tags = self.request.query_params.get('tags', None)
        if tags:
            tag_list = tags.split(',')
            # Convert to integers if they're tag IDs, otherwise assume they're names
            try:
                tag_ids = [int(tag) for tag in tag_list]
                queryset = queryset.filter(tags__id__in=tag_ids).distinct()
            except ValueError:
                # If conversion fails, assume they're tag names
                queryset = queryset.filter(tags__name__in=tag_list).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the created_by field when creating a new flashcard."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history for a flashcard."""
        flashcard = self.get_object()
        versions = flashcard.get_version_history()
        
        serializer = FlashcardVersionHistorySerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def revert_version(self, request, pk=None):
        """Revert to a specific version of a flashcard."""
        current_card = self.get_object()
        version_id = request.data.get('version_id')
        
        if not version_id:
            return Response({'error': 'version_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_version = Flashcard.objects.get(id=version_id)
            
            # Verify this version belongs to the same card family
            if target_version.version_group != current_card.version_group:
                return Response({'error': 'Invalid version - not part of same card'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Use model method to revert
            new_version = target_version.revert_to_this_version(reverted_by=request.user)
            
            serializer = FlashcardSerializer(new_version)
            return Response(serializer.data)
            
        except Flashcard.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = CardPagination
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsCuratorOrAdmin]
        return [permission() for permission in permission_classes]
