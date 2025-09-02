from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class with user-friendly query parameters and response format.

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Number of items per page (default: 10, max: 100)

    Example usage:
    - /api/products/?page=2&page_size=20
    """

    page_size = 10  # Default page size
    # Allow clients to set page size via ?page_size=X
    page_size_query_param = 'page_size'
    max_page_size = 100  # Maximum allowed page size
    page_query_param = 'page'  # Page number parameter (default is 'page')

    def get_paginated_response(self, data):
        """
        Return a paginated response with user-friendly structure.
        """
        # Get the base URL from the request
        request = self.request
        base_url = request.build_absolute_uri().split('?')[0]

        # Build next and previous URLs
        next_page_url = None
        previous_page_url = None

        if self.page.has_next():
            next_page_num = self.page.next_page_number()
            next_page_url = f"{base_url}?{self.page_query_param}={next_page_num}"
            if hasattr(self, 'get_page_size') and self.get_page_size(request) != self.page_size:
                next_page_url += f"&{self.page_size_query_param}={self.get_page_size(request)}"

        if self.page.has_previous():
            previous_page_num = self.page.previous_page_number()
            previous_page_url = f"{base_url}?{self.page_query_param}={previous_page_num}"
            if hasattr(self, 'get_page_size') and self.get_page_size(request) != self.page_size:
                previous_page_url += f"&{self.page_size_query_param}={self.get_page_size(request)}"

        return Response({
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'page_size': self.get_page_size(request) if hasattr(self, 'get_page_size') else self.page_size,
            'total_items': self.page.paginator.count,
            'next_page': next_page_url,
            'previous_page': previous_page_url,
            'results': data
        })
