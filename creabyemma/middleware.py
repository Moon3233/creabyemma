"""
Middleware de rate limiting pour les vues sensibles.
"""
from django.http import JsonResponse, HttpResponse
from .rate_limit import is_rate_limited, get_client_ip


class RateLimitMiddleware:
    """
    Applique un rate limit basique sur login, upload.
    Les vues marquées avec request.rate_limit_key seront vérifiées.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.rstrip('/')
        key = None
        if path == '/login' and request.method == 'POST':
            key = 'login'
        elif path == '/upload' and request.method == 'POST':
            key = 'upload'

        if key:
            ip = get_client_ip(request)
            if is_rate_limited(ip, key):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accepts('application/json'):
                    return JsonResponse({'error': 'Trop de requêtes. Réessayez plus tard.'}, status=429)
                return HttpResponse('Trop de requêtes. Réessayez plus tard.', status=429)

        return self.get_response(request)
