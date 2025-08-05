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
            'created_at', 'updated_at', 'is_active', 'version', 'parent_version'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'version', 'parent_version']

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
        
        # Create new version instead of updating in place
        new_version = instance.create_new_version(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Handle tags for new version
        if tag_names is not None:
            new_version.tags.clear()
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name.strip())
                new_version.tags.add(tag)
        
        return new_version


class FlashcardVersionHistorySerializer(serializers.ModelSerializer):
    """Serializer for flashcard version history."""
    
    tags = TagSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Flashcard
        fields = [
            'id', 'title', 'phrase', 'definition', 'tags', 'created_by_username',
            'created_at', 'updated_at', 'version', 'is_active'
        ]


class DailyCardSerializer(serializers.ModelSerializer):
    """Serializer for DailyCard model."""
    
    card = FlashcardSerializer(read_only=True)
    
    class Meta:
        model = DailyCard
        fields = ['id', 'card', 'date', 'created_at']
