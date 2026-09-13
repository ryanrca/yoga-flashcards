from django.core.files.storage import default_storage
from rest_framework import serializers

from .models import Flashcard, Tag, DailyCard, CardImage, ImageGenerationSettings


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class FlashcardSerializer(serializers.ModelSerializer):
    """Serializer for Flashcard model."""
    
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    generated_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'title', 'phrase', 'definition', 'short_answer', 'front_image', 'back_image',
            'generated_image',
            'tags', 'tag_names', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'is_active', 'version_group', 'version_number', 'is_live'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version_group', 'version_number', 'is_live']

    def get_generated_image(self, obj):
        """
        URL of the accepted AI image, or None.

        Deliberately the only image field non-admins ever see: an image that has
        not been accepted, and the prompt behind any image, stay in the admin
        API. The list view annotates `accepted_image_path` to avoid a query per
        card; a lone object (the daily card) falls back to a direct lookup.
        """
        if hasattr(obj, 'accepted_image_path'):
            path = obj.accepted_image_path
        else:
            path = (
                CardImage.objects.filter(
                    version_group=obj.version_group,
                    is_accepted=True,
                    status=CardImage.SUCCEEDED,
                )
                .values_list('image', flat=True)
                .first()
            )
        if not path:
            return None
        url = default_storage.url(path)
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        flashcard = Flashcard.objects.create(**validated_data)
        
        # Handle tags
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            flashcard.tags.add(tag)
        
        return flashcard

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        
        # Prepare tags list for new version
        tags_to_set = None
        
        # Check if 'tags' field exists in request data (FormData from frontend)
        if 'tags' in self.context['request'].data:
            # Get tag IDs - could be [''] if all tags removed, or list of IDs
            tag_ids = self.context['request'].data.getlist('tags', [])
            tags_to_set = []
            for tag_id in tag_ids:
                # Skip empty string marker
                if tag_id == '':
                    continue
                try:
                    tag = Tag.objects.get(id=int(tag_id))
                    tags_to_set.append(tag)
                except (Tag.DoesNotExist, ValueError):
                    pass
        # Handle tag names (sent as JSON)
        elif tag_names is not None:
            tags_to_set = []
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                tags_to_set.append(tag)
        
        # Create new version instead of updating in place
        new_version = instance.create_new_version(
            updated_by=self.context['request'].user,
            tags=tags_to_set,
            **validated_data
        )
        
        return new_version


class FlashcardVersionHistorySerializer(serializers.ModelSerializer):
    """Serializer for flashcard version history."""
    
    tags = TagSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'title', 'phrase', 'definition', 'short_answer', 'tags', 'created_by_username',
            'created_at', 'updated_at', 'version_number', 'is_live', 'is_active'
        ]


class DailyCardSerializer(serializers.ModelSerializer):
    """Serializer for DailyCard model."""
    
    card = FlashcardSerializer(read_only=True)
    
    class Meta:
        model = DailyCard
        fields = ['id', 'card', 'date', 'created_at']


class CardImageSerializer(serializers.ModelSerializer):
    """
    Admin-only view of a generation, prompt included.

    Never nest this in FlashcardSerializer: the prompt and unaccepted images
    must not reach non-admin clients.
    """

    image_url = serializers.SerializerMethodField()
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    accepted_by_username = serializers.CharField(source='accepted_by.username', read_only=True)
    card_title = serializers.CharField(source='card.title', read_only=True)

    class Meta:
        model = CardImage
        fields = [
            'id', 'version_group', 'card', 'card_title', 'status', 'image_url',
            'prompt', 'prompt_seed', 'look_and_feel', 'look_and_feel_override', 'model',
            'is_accepted', 'accepted_at', 'accepted_by_username',
            'attempts', 'error', 'cost_usd', 'provider_response_id',
            'requested_by_username', 'is_auto', 'created_at', 'updated_at',
            'started_at', 'finished_at',
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class CardImageCreateSerializer(serializers.Serializer):
    """Input for queueing a generation. Every field is optional."""

    prompt = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=False,
        help_text='Full prompt override. Blank composes it from the card text and look and feel.',
    )
    look_and_feel_override = serializers.CharField(
        required=False, allow_blank=True,
        help_text='Style guidance for this image only. Blank uses the global setting.',
    )
    model = serializers.CharField(
        required=False, allow_blank=True,
        help_text='OpenRouter model slug. Blank uses the global default.',
    )


class ImageGenerationSettingsSerializer(serializers.ModelSerializer):
    """The global look and feel, default model and bot switches."""

    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = ImageGenerationSettings
        fields = [
            'look_and_feel', 'model', 'enabled', 'auto_generate_new_cards',
            'max_attempts', 'updated_at', 'updated_by_username',
        ]
        read_only_fields = ['updated_at', 'updated_by_username']

    def validate_max_attempts(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError('max_attempts must be between 1 and 10.')
        return value
