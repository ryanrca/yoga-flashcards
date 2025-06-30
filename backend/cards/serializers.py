from rest_framework import serializers
from .models import Card, CardVersion, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CardVersionSerializer(serializers.ModelSerializer):
    """Serializer for CardVersion model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = CardVersion
        fields = [
            'id', 'title', 'phrase', 'definition', 'created_at',
            'created_by', 'created_by_username', 'version_number'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'version_number']


class CardSerializer(serializers.ModelSerializer):
    """Serializer for Card model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    versions = CardVersionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'title', 'phrase', 'definition', 'created_at', 'updated_at',
            'deleted_at', 'created_by', 'created_by_username', 'views', 'enabled',
            'front_photo', 'back_photo', 'tags', 'tag_ids', 'versions'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'deleted_at', 'created_by',
            'created_by_username', 'views', 'versions'
        ]

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        card = Card.objects.create(**validated_data)
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            card.tags.set(tags)
        
        # Create initial version
        self._create_version(card, validated_data.get('created_by'))
        
        return card

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Check if text fields changed to create new version
        text_fields_changed = any(
            getattr(instance, field) != validated_data.get(field, getattr(instance, field))
            for field in ['title', 'phrase', 'definition']
            if field in validated_data
        )
        
        # Update the card
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        # Create new version if text fields changed
        if text_fields_changed:
            self._create_version(instance, self.context['request'].user)
        
        return instance

    def _create_version(self, card, user):
        """Create a new version of the card"""
        last_version = card.versions.first()
        version_number = last_version.version_number + 1 if last_version else 1
        
        CardVersion.objects.create(
            card=card,
            title=card.title,
            phrase=card.phrase,
            definition=card.definition,
            created_by=user,
            version_number=version_number
        )


class CardListSerializer(serializers.ModelSerializer):
    """Simplified serializer for card list view"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Card
        fields = [
            'id', 'title', 'phrase', 'created_at', 'updated_at',
            'created_by_username', 'views', 'enabled', 'tags'
        ]
