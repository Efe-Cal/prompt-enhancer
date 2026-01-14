from django.shortcuts import render
from django.conf import settings
import os


def serve_react(request):
    """
    Serve the React app's index.html for all frontend routes
    """
    index_path = os.path.join(settings.FRONTEND_BUILD_DIR, 'index.html')
    
    if os.path.exists(index_path):
        return render(request, 'index.html')
    else:
        return render(request, 'index.html', status=404)
