from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import CardViewSet, TagViewSet, CardVersionViewSet

# Create main router
router = DefaultRouter()
router.register(r'cards', CardViewSet, basename='card')
router.register(r'tags', TagViewSet, basename='tag')

# Create nested router for card versions
cards_router = routers.NestedDefaultRouter(router, r'cards', lookup='card')
cards_router.register(r'versions', CardVersionViewSet, basename='card-versions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(cards_router.urls)),
]
