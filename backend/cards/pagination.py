from rest_framework.pagination import PageNumberPagination


class CardPagination(PageNumberPagination):
    """Custom pagination for cards with configurable page size"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
