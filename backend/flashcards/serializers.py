from rest_framework import serializers

from .models import (
    Flashcard, Tag, DailyCard, CardImage, ImageGenerationSettings,
    CardImagePreference, SiteSettings,
)


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
    # Foreign keys underneath, URL strings on the wire - the same shape the API
    # had when these were ImageFields, so nothing downstream had to change.
    #
    # There is no `generated_image` any more. It existed only because an AI
    # image lived somewhere a human upload did not, which forced every consumer
    # to remember a fallback. One card has one front image, whatever produced
    # it, and this is it.
    front_image = serializers.SerializerMethodField()
    back_image = serializers.SerializerMethodField()

    # Asymmetric on purpose: the API hands out a URL on read and takes a file on
    # write, and those cannot be the same declared field once the model field is
    # a foreign key. An upload creates a row in the media table and points the
    # card at it - precisely what accepting a generated image does.
    front_image_upload = serializers.ImageField(write_only=True, required=False, allow_null=True)
    back_image_upload = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Flashcard
        fields = [
            'id', 'title', 'phrase', 'definition', 'short_answer', 'front_image', 'back_image',
            'front_image_upload', 'back_image_upload',
            'tags', 'tag_names', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'is_active', 'version_group', 'version_number', 'is_live'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version_group', 'version_number', 'is_live']

    def _media_url(self, media):
        """
        Absolute URL for a media row, or None.

        A row can exist without a file - queued and failed generations do - so
        the file is checked, not just the pointer.
        """
        if media is None or not media.image:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(media.image.url) if request else media.image.url

    def get_front_image(self, obj):
        return self._media_url(obj.front_image)

    def get_back_image(self, obj):
        return self._media_url(obj.back_image)

    @staticmethod
    def _attach_uploads(card, front, back):
        """
        Store uploaded files as media rows and point the card at them.

        An upload is not special. It lands in the same table a generated image
        does, with a status saying where it came from and no prompt or model,
        because a photograph has neither.
        """
        slots = []
        for uploaded, slot in ((front, 'front_image'), (back, 'back_image')):
            if uploaded is None:
                continue
            media = CardImage.objects.create(
                version_group=card.version_group,
                card=card,
                status=CardImage.UPLOADED,
                prompt='',
                model='',
            )
            media.image.save(uploaded.name, uploaded, save=True)
            setattr(card, slot, media)
            slots.append(slot)
        if slots:
            card.save(update_fields=slots)
        return card

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        # Popped before the model call: these are serializer fields, not columns.
        front = validated_data.pop('front_image_upload', None)
        back = validated_data.pop('back_image_upload', None)
        flashcard = Flashcard.objects.create(**validated_data)

        # Uploads come second - a media row is keyed to the card's
        # version_group, which does not exist until the card does.
        self._attach_uploads(flashcard, front, back)

        # Handle tags
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            flashcard.tags.add(tag)

        return flashcard

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        front = validated_data.pop('front_image_upload', None)
        back = validated_data.pop('back_image_upload', None)
        
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

        # The new version inherits the old pointers through create_new_version;
        # an upload sent with this edit replaces them on the new row only, so
        # the previous version still shows what it showed.
        self._attach_uploads(new_version, front, back)

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
    card_title = serializers.CharField(source='card.title', read_only=True)
    # Computed, not stored. "Accepted" now means "the live card points at me",
    # so it is derived from the pointer rather than kept alongside it where the
    # two could disagree. The field name is unchanged so the admin screens that
    # show an accepted badge keep working.
    is_accepted = serializers.SerializerMethodField()

    class Meta:
        model = CardImage
        fields = [
            'id', 'version_group', 'card', 'card_title', 'status', 'image_url',
            'prompt', 'prompt_seed', 'look_and_feel', 'look_and_feel_override', 'model',
            'is_accepted',
            'attempts', 'error', 'cost_usd', 'provider_response_id',
            'requested_by_username', 'is_auto', 'created_at', 'updated_at',
            'started_at', 'finished_at',
        ]
        read_only_fields = fields

    def get_is_accepted(self, obj):
        return Flashcard.objects.filter(is_live=True, front_image=obj).exists()

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


class SiteSettingsSerializer(serializers.ModelSerializer):
    """
    The site-wide theme. Read by everyone, written by admins.

    `theme` needs no explicit validator: ModelSerializer renders it as a
    ChoiceField from the model's Theme choices, so an unknown id is already a
    400 rather than something that would leave every visitor unstyled.
    """

    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = SiteSettings
        fields = ['theme', 'updated_at', 'updated_by_username']
        read_only_fields = ['updated_at', 'updated_by_username']


class CardImageModelSerializer(serializers.Serializer):
    """Input for choosing the model used for one card."""

    model = serializers.CharField(
        required=True, allow_blank=True, max_length=200,
        help_text='OpenRouter model slug. Blank returns this card to the global default.',
    )


class CardImagePreferenceSerializer(serializers.ModelSerializer):
    """The stored per-card model choice."""

    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = CardImagePreference
        fields = ['version_group', 'model', 'updated_at', 'updated_by_username']
        read_only_fields = fields
