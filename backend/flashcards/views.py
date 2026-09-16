from django.db.models import Exists, F, OuterRef, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Flashcard, Tag, CardImage, Favorite, ImageGenerationSettings, SiteSettings
from .serializers import (
    FlashcardSerializer, TagSerializer, FlashcardVersionHistorySerializer,
    CardImageSerializer, CardImageCreateSerializer, ImageGenerationSettingsSerializer,
    CardImageModelSerializer, SiteSettingsSerializer,
)
from .permissions import IsCuratorOrAdmin, IsAdminOnly
from .pagination import CardPagination
from .services import CardImageService


class FlashcardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing flashcards."""
    
    serializer_class = FlashcardSerializer
    pagination_class = CardPagination
    
    def get_permissions(self):
        """
        Set permissions based on action.

        This override is what actually decides access, so the `images` action
        has to be named here: permission_classes declared on an @action are
        ignored once get_permissions is overridden. Images and prompts are
        admin-only, while cards themselves stay curator-editable.
        """
        # `favorite` has to be named here for the same reason `images` does, and
        # it matters more: the else branch below locks every unnamed action to
        # curators, so without this an ordinary user could not favourite
        # anything - which is the one thing favourites are for.
        if self.action in ['list', 'retrieve', 'favorite']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['images', 'image_model']:
            permission_classes = [IsCuratorOrAdmin]
        else:
            permission_classes = [IsCuratorOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Return active live flashcards with filtering and search."""
        # This used to carry a Subquery annotation to find each card's accepted
        # image without a query per row. The card points at its media directly
        # now, so an ordinary join does the same job and says what it means.
        queryset = (
            Flashcard.objects.filter(is_active=True, is_live=True)
            .select_related('created_by', 'front_image', 'back_image')
            .prefetch_related('tags')
        )

        user = self.request.user

        # Annotated, not computed per row: the grid draws a heart on every card,
        # and resolving that one at a time would be a page of queries.
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, version_group=OuterRef('version_group')
                    )
                )
            )

        # ?favorites=true narrows this same list rather than adding a second
        # endpoint with its own shape. Because the base query already filters
        # is_live, a favourite always resolves to whichever version is current:
        # favourite v1, a curator publishes v4, and the user is shown v4.
        if self.request.query_params.get('favorites') in ('true', '1'):
            if not user.is_authenticated:
                return queryset.none()
            queryset = queryset.filter(
                version_group__in=Favorite.objects.filter(user=user).values('version_group')
            )

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

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """
        Toggle this card in the caller's favourites. Clicking the heart again
        removes it.

        Keyed on version_group, so the favourite belongs to the card family: a
        later edit cannot lose it, and the favourites list always resolves to the
        version that is live now.

        favorite_count is incremented when a favourite is added and deliberately
        NOT decremented when one is removed. It is a lifetime tally of how often
        a card has been favourited, not a count of who currently has it - those
        two numbers diverge the first time anyone unfavourites, by design.
        """
        card = self.get_object()
        existing = Favorite.objects.filter(
            user=request.user, version_group=card.version_group
        )

        if existing.exists():
            existing.delete()
            favorited = False
        else:
            Favorite.objects.create(
                user=request.user, version_group=card.version_group
            )
            # F() rather than read-modify-write: two people favouriting at once
            # would otherwise lose an increment.
            Flashcard.objects.filter(version_group=card.version_group).update(
                favorite_count=F('favorite_count') + 1
            )
            favorited = True

        card.refresh_from_db()
        return Response({
            'favorited': favorited,
            'favorite_count': card.favorite_count,
        })

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get version history for a flashcard."""
        flashcard = self.get_object()
        versions = flashcard.get_version_history()
        
        serializer = FlashcardVersionHistorySerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'post'], url_path='images',
            permission_classes=[IsCuratorOrAdmin])
    def images(self, request, pk=None):
        """
        Curator or admin: the card's generation history, and queueing a new one.

        GET also returns `preview`, the prompt a new generation would use right
        now, so the admin screen can prefill the editable prompt box without a
        second round trip.

        POST queues a row; it does not call OpenRouter. The bot picks it up, so
        an admin clicking regenerate repeatedly cannot start parallel provider
        calls for the same card.
        """
        card = self.get_object()

        if request.method == 'GET':
            images = CardImage.objects.filter(version_group=card.version_group).select_related(
                'card', 'requested_by'
            )
            override = request.query_params.get('look_and_feel_override', '')
            return Response({
                'preview': CardImageService.preview_prompt(card, override),
                'images': CardImageSerializer(images, many=True, context={'request': request}).data,
            })

        serializer = CardImageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        config = ImageGenerationSettings.load()
        if not config.enabled:
            return Response(
                {'error': 'Image generation is disabled in the global settings.'},
                status=status.HTTP_409_CONFLICT,
            )

        image = CardImageService.queue(
            card,
            prompt=data.get('prompt', ''),
            look_and_feel_override=data.get('look_and_feel_override', ''),
            model=data.get('model', ''),
            requested_by=request.user,
        )
        return Response(
            CardImageSerializer(image, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get', 'put'], url_path='image-model')
    def image_model(self, request, pk=None):
        """
        Read or set the image model for this card.

        Stored against the card's version_group, so the choice survives edits to
        the card text. A blank model returns the card to the global default.
        """
        card = self.get_object()

        if request.method == 'GET':
            config = ImageGenerationSettings.load()
            model = CardImageService.effective_model(card)
            return Response({
                'model': model,
                'model_source': 'card' if model != config.model else 'global',
                'global_model': config.model,
            })

        serializer = CardImageModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        CardImageService.set_model(card, serializer.validated_data['model'], user=request.user)

        config = ImageGenerationSettings.load()
        model = CardImageService.effective_model(card)
        return Response({
            'model': model,
            'model_source': 'card' if model != config.model else 'global',
            'global_model': config.model,
        })

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


class CardImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Curator and admin access to generated images and their prompts.

    Read-only by design: history is append-only, so there is no update or
    destroy. Accepting, withdrawing and regenerating are explicit actions.
    """

    serializer_class = CardImageSerializer
    permission_classes = [IsCuratorOrAdmin]
    pagination_class = CardPagination

    def get_queryset(self):
        queryset = CardImage.objects.select_related('card', 'requested_by')
        version_group = self.request.query_params.get('version_group')
        if version_group:
            queryset = queryset.filter(version_group=version_group)
        image_status = self.request.query_params.get('status')
        if image_status:
            queryset = queryset.filter(status=image_status)
        return queryset

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Make this the image the rest of the users see."""
        image = self.get_object()
        try:
            CardImageService.accept(image, user=request.user)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CardImageSerializer(image, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def unaccept(self, request, pk=None):
        """Withdraw the image from public view. The row is kept."""
        image = self.get_object()
        CardImageService.unaccept(image)
        return Response(CardImageSerializer(image, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """
        Queue a fresh generation seeded from this row's prompt.

        Creates a new row, leaving this one intact, so the history shows every
        prompt that was ever tried.
        """
        source = self.get_object()
        if source.card is None:
            return Response(
                {'error': 'The card version behind this image no longer exists; regenerate from the card instead.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CardImageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # The model deliberately falls back to the card's current choice rather
        # than the one this row used. "Regenerate with same prompt" is how you
        # compare a prompt you like across models: change the model, regenerate,
        # and the same prompt is sent to the new one.
        image = CardImageService.queue(
            source.card,
            prompt=data.get('prompt', '') or source.prompt,
            look_and_feel_override=data.get('look_and_feel_override', '') or source.look_and_feel_override,
            model=data.get('model', '') or CardImageService.effective_model(source.card),
            requested_by=request.user,
        )
        return Response(
            CardImageSerializer(image, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class ImageGenerationSettingsView(APIView):
    """
    Curator or admin: the global look and feel, default model and bot switches.

    Curators are included because this is the deck's visual direction, which is
    editorial work. Narrow it to IsAdminOnly if the master switch and attempt
    cap should stay with admins.
    """

    permission_classes = [IsCuratorOrAdmin]

    def get(self, request):
        config = ImageGenerationSettings.load()
        return Response(ImageGenerationSettingsSerializer(config).data)

    def put(self, request):
        config = ImageGenerationSettings.load()
        serializer = ImageGenerationSettingsSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)


class SiteSettingsView(APIView):
    """
    The theme every visitor sees.

    GET is AllowAny deliberately: the SPA resolves the theme on every page
    load, including for anonymous visitors, so gating it would leave signed-out
    users on the fallback palette.

    PUT is IsAdminOnly. Appearance is a whole-site decision, unlike the image
    settings next door, which curators share because that is editorial work.
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminOnly()]

    def get(self, request):
        data = SiteSettingsSerializer(SiteSettings.load()).data

        user = request.user
        if not (user and user.is_authenticated and user.is_admin()):
            # The audit fields name an admin. An anonymous visitor only needs
            # to know which palette to paint, so do not hand out a username.
            return Response({'theme': data['theme']})

        return Response(data)

    def put(self, request):
        config = SiteSettings.load()
        serializer = SiteSettingsSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)
