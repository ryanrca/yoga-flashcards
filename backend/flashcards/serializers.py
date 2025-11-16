from rest_framework import serializers
from .models import Flashcard, Tag, DailyCard


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
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'title', 'phrase', 'definition', 'front_image', 'back_image',
            'tags', 'tag_names', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'is_active', 'version_group', 'version_number', 'is_live'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version_group', 'version_number', 'is_live']

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
            'id', 'title', 'phrase', 'definition', 'tags', 'created_by_username',
            'created_at', 'updated_at', 'version_number', 'is_live', 'is_active'
        ]


class DailyCardSerializer(serializers.ModelSerializer):
    """Serializer for DailyCard model."""
    
    card = FlashcardSerializer(read_only=True)
    
    class Meta:
        model = DailyCard
        fields = ['id', 'card', 'date', 'created_at']
