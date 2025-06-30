from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Card, CardVersion, Tag
from .serializers import (
    CardSerializer, CardListSerializer, 
    CardVersionSerializer, TagSerializer
)
from .services import CardService
from .pagination import CardPagination


class CardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing flashcards"""
    permission_classes = [IsAuthenticated]
    pagination_class = CardPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'phrase', 'definition']
    ordering_fields = ['title', 'created_at', 'updated_at', 'views']
    ordering = ['-updated_at']
    filterset_fields = ['enabled', 'tags']
    
    def get_queryset(self):
        """Get cards excluding soft-deleted ones"""
        return Card.objects.filter(deleted_at__isnull=True).prefetch_related('tags', 'versions')
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return CardListSerializer
        return CardSerializer
    
    def perform_create(self, serializer):
        """Set the created_by field to current user"""
        serializer.save(created_by=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a card and increment view count"""
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def revert_version(self, request, pk=None):
        """Revert card to a specific version"""
        card = self.get_object()
        version_id = request.data.get('version_id')
        
        if not version_id:
            return Response(
                {'error': 'version_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            updated_card = CardService.revert_to_version(card, version_id, request.user)
            serializer = self.get_serializer(updated_card)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        """Soft delete a card"""
        card = self.get_object()
        card.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tags"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class CardVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing card versions"""
    serializer_class = CardVersionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get versions for a specific card"""
        card_id = self.kwargs.get('card_pk')
        if card_id:
            return CardVersion.objects.filter(card_id=card_id)
        return CardVersion.objects.none()
