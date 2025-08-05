from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Flashcard, Tag
from .serializers import FlashcardSerializer, TagSerializer, FlashcardVersionHistorySerializer
from .permissions import IsCuratorOrAdmin


class FlashcardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing flashcards."""
    
    serializer_class = FlashcardSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsCuratorOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Return active flashcards with filtering and search."""
        queryset = Flashcard.objects.filter(is_active=True).select_related('created_by').prefetch_related('tags')
        
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
            queryset = queryset.filter(tags__name__in=tag_list).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        """Set the created_by field when creating a new flashcard."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history for a flashcard."""
        flashcard = self.get_object()
        root_card = flashcard.parent_version or flashcard
        versions = Flashcard.objects.filter(
            Q(id=root_card.id) | Q(parent_version=root_card)
        ).order_by('-version')
        
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
            if (target_version.parent_version != current_card.parent_version and 
                target_version.id != (current_card.parent_version.id if current_card.parent_version else current_card.id)):
                return Response({'error': 'Invalid version'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new version based on target version
            new_version = current_card.create_new_version(
                title=target_version.title,
                phrase=target_version.phrase,
                definition=target_version.definition,
                front_image=target_version.front_image,
                back_image=target_version.back_image,
                created_by=request.user,
                tags=target_version.tags.all()
            )
            
            serializer = FlashcardSerializer(new_version)
            return Response(serializer.data)
            
        except Flashcard.DoesNotExist:
            return Response({'error': 'Version not found'}, status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsCuratorOrAdmin]
        return [permission() for permission in permission_classes]
