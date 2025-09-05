from django.http import HttpResponse
from django.views import View

class RobotsView(View):
    def get(self, request):
        robots_txt = """User-agent: *
Allow: /

Sitemap: https://startlinker.com/sitemap.xml
"""
        return HttpResponse(robots_txt, content_type='text/plain')