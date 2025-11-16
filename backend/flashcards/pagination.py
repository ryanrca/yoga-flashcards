from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CardPagination(PageNumberPagination):
    """Custom pagination that returns empty results instead of 404 for invalid pages."""
    
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a page object,
        or `None` if pagination is not configured for this view.
        Returns empty list instead of raising 404 for invalid pages.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            page_number = 1
        
        # If page number is beyond available pages, return empty page
        if page_number > paginator.num_pages and paginator.num_pages > 0:
            # Create an empty page
            self.page = paginator.page(paginator.num_pages)
            self.page.object_list = []
            self.request = request
            return []
        
        try:
            self.page = paginator.page(page_number)
        except Exception:
            # Return empty page for any pagination errors
            self.page = paginator.page(1)
            self.page.object_list = []
            self.request = request
            return []
        
        self.request = request
        return list(self.page)
