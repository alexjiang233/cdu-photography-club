class PrivateResponsesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(('/api/', '/admin/')):
            response['Cache-Control'] = 'private, no-store'
            response['Vary'] = 'Cookie'
        return response
