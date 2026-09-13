from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cards', views.FlashcardViewSet, basename='flashcard')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'card-images', views.CardImageViewSet, basename='card-image')

urlpatterns = [
    path('image-settings/', views.ImageGenerationSettingsView.as_view(), name='image-settings'),
    path('', include(router.urls)),
]
