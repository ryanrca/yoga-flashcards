from django.db import models
from .models import Card, CardVersion, Tag


class CardService:
    """Service class for card-related business logic"""
    
    @staticmethod
    def revert_to_version(card, version_id, user):
        """Revert a card to a specific version"""
        try:
            version = CardVersion.objects.get(id=version_id, card=card)
        except CardVersion.DoesNotExist:
            raise ValueError("Version not found")
        
        # Update card with version data
        card.title = version.title
        card.phrase = version.phrase
        card.definition = version.definition
        card.save()
        
        # Create new version entry for this revert
        last_version = card.versions.first()
        new_version_number = last_version.version_number + 1 if last_version else 1
        
        CardVersion.objects.create(
            card=card,
            title=card.title,
            phrase=card.phrase,
            definition=card.definition,
            created_by=user,
            version_number=new_version_number
        )
        
        return card
    
    @staticmethod
    def search_cards(queryset, search_query):
        """Search cards across title, phrase, and definition"""
        if search_query:
            return queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(phrase__icontains=search_query) |
                models.Q(definition__icontains=search_query)
            )
        return queryset


class TagService:
    """Service class for tag-related business logic"""
    
    @staticmethod
    def get_or_create_tags(tag_names):
        """Get or create tags by name"""
        tags = []
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name.strip())
            tags.append(tag)
        return tags
