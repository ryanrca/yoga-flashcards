import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from cards.models import Card, Tag, CardVersion
from cards.factories import UserFactory, CardFactory, TagFactory


class CardModelTest(TestCase):
    
    def setUp(self):
        self.user = UserFactory()
        self.tag1 = TagFactory(name='Asana')
        self.tag2 = TagFactory(name='Pranayama')
    
    def test_card_creation(self):
        """Test basic card creation"""
        card = CardFactory(
            title='Test Card',
            phrase='Test Phrase',
            definition='Test Definition',
            created_by=self.user
        )
        
        self.assertEqual(card.title, 'Test Card')
        self.assertEqual(card.phrase, 'Test Phrase')
        self.assertEqual(card.definition, 'Test Definition')
        self.assertEqual(card.created_by, self.user)
        self.assertTrue(card.enabled)
        self.assertEqual(card.views, 0)
        self.assertIsNone(card.deleted_at)
    
    def test_card_soft_delete(self):
        """Test soft delete functionality"""
        card = CardFactory()
        self.assertFalse(card.is_deleted())
        
        card.soft_delete()
        self.assertTrue(card.is_deleted())
        self.assertIsNotNone(card.deleted_at)
    
    def test_card_increment_views(self):
        """Test view counter increment"""
        card = CardFactory()
        self.assertEqual(card.views, 0)
        
        card.increment_views()
        self.assertEqual(card.views, 1)
        
        card.increment_views()
        self.assertEqual(card.views, 2)
    
    def test_card_tags_relationship(self):
        """Test many-to-many relationship with tags"""
        card = CardFactory()
        card.tags.add(self.tag1, self.tag2)
        
        self.assertEqual(card.tags.count(), 2)
        self.assertIn(self.tag1, card.tags.all())
        self.assertIn(self.tag2, card.tags.all())


class TagModelTest(TestCase):
    
    def test_tag_creation(self):
        """Test basic tag creation"""
        tag = TagFactory(name='Test Tag')
        
        self.assertEqual(tag.name, 'Test Tag')
        self.assertEqual(str(tag), 'Test Tag')
    
    def test_tag_unique_constraint(self):
        """Test tag name uniqueness"""
        TagFactory(name='Unique Tag')
        
        with pytest.raises(Exception):
            TagFactory(name='Unique Tag')


class CardVersionModelTest(TestCase):
    
    def setUp(self):
        self.user = UserFactory()
        self.card = CardFactory(created_by=self.user)
    
    def test_version_creation(self):
        """Test card version creation"""
        version = CardVersion.objects.create(
            card=self.card,
            title=self.card.title,
            phrase=self.card.phrase,
            definition=self.card.definition,
            created_by=self.user,
            version_number=1
        )
        
        self.assertEqual(version.card, self.card)
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.created_by, self.user)
        self.assertEqual(str(version), f"{self.card.title} - v1")
    
    def test_version_unique_constraint(self):
        """Test unique constraint on card and version number"""
        CardVersion.objects.create(
            card=self.card,
            title=self.card.title,
            phrase=self.card.phrase,
            definition=self.card.definition,
            created_by=self.user,
            version_number=1
        )
        
        with pytest.raises(Exception):
            CardVersion.objects.create(
                card=self.card,
                title=self.card.title,
                phrase=self.card.phrase,
                definition=self.card.definition,
                created_by=self.user,
                version_number=1
            )
