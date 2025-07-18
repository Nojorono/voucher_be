import logging

logger = logging.getLogger(__name__)

class ALBCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log untuk debug ALB
        origin = request.META.get('HTTP_ORIGIN', 'No origin')
        forwarded_host = request.META.get('HTTP_X_FORWARDED_HOST', 'No forwarded host')
        method = request.method
        path = request.path
        content_type = request.META.get('CONTENT_TYPE', 'No content type')
        
        logger.info(f"MIDDLEWARE: {method} {path} from Origin: {origin}")
        logger.info(f"MIDDLEWARE: Content-Type: {content_type}")
        print(f"MIDDLEWARE: {method} {path} from Origin: {origin}, Content-Type: {content_type}")
        
        # Handle preflight requests IMMEDIATELY
        if request.method == "OPTIONS":
            from django.http import HttpResponse
            logger.info("MIDDLEWARE: Handling OPTIONS request for file upload")
            print("MIDDLEWARE: Handling OPTIONS request for file upload")
            
            response = HttpResponse(status=200)
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            
            # IMPORTANT: Allow multipart/form-data untuk file upload
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, X-Forwarded-For, X-Forwarded-Host, X-Forwarded-Proto, Origin, Accept, Accept-Encoding, Accept-Language, Cache-Control"
            response["Access-Control-Max-Age"] = "86400"
            response["Access-Control-Allow-Credentials"] = "false"
            
            logger.info("MIDDLEWARE: OPTIONS response sent with file upload CORS headers")
            print("MIDDLEWARE: OPTIONS response sent with file upload CORS headers")
            return response

        # Process normal requests
        response = self.get_response(request)
        
        # Add CORS headers to all responses
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, X-Forwarded-For, X-Forwarded-Host, X-Forwarded-Proto, Origin, Accept, Accept-Encoding, Accept-Language, Cache-Control"
        response["Access-Control-Allow-Credentials"] = "false"
        
        logger.info(f"MIDDLEWARE: {method} {path} response sent with CORS headers")
        print(f"MIDDLEWARE: {method} {path} response sent with CORS headers")
        
        return response