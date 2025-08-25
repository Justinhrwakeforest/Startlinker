import json
import psycopg2
from psycopg2.extras import RealDictCursor
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import django
from django.core.wsgi import get_wsgi_application
import os

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
if not settings.configured:
    django.setup()

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='startlinker_db',
        user='startlinker_user',
        password='startlinker123',
        cursor_factory=RealDictCursor
    )

@csrf_exempt
def api_root(request):
    return JsonResponse({
        'message': 'StartLinker API v1.0 - PostgreSQL Connected',
        'endpoints': [
            '/api/auth/check-username/',
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/auth/user/',
            '/api/startups/',
            '/api/jobs/',
            '/api/messaging/unread-count/'
        ]
    })

@csrf_exempt
@require_http_methods(['GET'])
def check_username(request):
    username = request.GET.get('username', '')
    return JsonResponse({'is_taken': len(username) < 3})

@csrf_exempt
@require_http_methods(['POST'])
def register_user(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({
            'message': 'User registered successfully',
            'user': {
                'id': 1,
                'username': data.get('username', ''),
                'email': data.get('email', '')
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(['POST'])
def login_user(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({
            'token': 'sample-auth-token-123',
            'user': {
                'id': 1,
                'username': data.get('username', ''),
                'email': 'user@startlinker.com',
                'first_name': 'Demo',
                'last_name': 'User'
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(['GET'])
def get_current_user(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Token '):
        return JsonResponse(
            {'detail': 'Authentication credentials were not provided.'}, 
            status=401
        )
    
    return JsonResponse({
        'id': 1,
        'username': 'demo_user',
        'email': 'demo@startlinker.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'is_premium': False,
        'profile_picture': None
    })

@csrf_exempt
@require_http_methods(['GET'])
def user_stats(request):
    return JsonResponse({
        'total_users': 1250,
        'active_users': 890,
        'new_users_today': 15
    })

@csrf_exempt
@require_http_methods(['GET'])
def startups_list(request):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM startups ORDER BY id')
                startups = cur.fetchall()
        
        startups_data = []
        for startup in startups:
            startups_data.append({
                'id': startup['id'],
                'name': startup['name'],
                'description': startup['description'],
                'industry': startup['industry'],
                'website': startup['website'],
                'founded_date': startup['founded_date'].isoformat() if startup['founded_date'] else None,
                'team_size': '10-50 employees',
                'funding_stage': 'Series A',
                'location': 'San Francisco, CA'
            })
        
        return JsonResponse({'results': startups_data, 'count': len(startups_data)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(['GET'])
def startup_detail(request, startup_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM startups WHERE id = %s', (startup_id,))
                startup = cur.fetchone()
        
        if not startup:
            return JsonResponse({'error': 'Startup not found'}, status=404)
        
        startup_data = {
            'id': startup['id'],
            'name': startup['name'],
            'description': startup['description'],
            'industry': startup['industry'],
            'website': startup['website'],
            'founded_date': startup['founded_date'].isoformat() if startup['founded_date'] else None,
            'team_size': '10-50 employees',
            'funding_stage': 'Series A',
            'location': 'San Francisco, CA'
        }
        
        return JsonResponse(startup_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(['GET'])
def startups_filters(request):
    return JsonResponse({
        'industries': ['Technology', 'Healthcare', 'Finance', 'E-commerce'],
        'funding_stages': ['Pre-Seed', 'Seed', 'Series A', 'Series B'],
        'locations': ['San Francisco, CA', 'New York, NY', 'Austin, TX']
    })

@csrf_exempt
@require_http_methods(['GET'])
def jobs_list(request):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM jobs ORDER BY id')
                jobs = cur.fetchall()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job['id'],
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'type': job['job_type'],
                'description': job['description'],
                'salary_range': '0K - 50K',
                'experience_level': 'Mid-Senior Level'
            })
        
        return JsonResponse({'results': jobs_data, 'count': len(jobs_data)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(['GET'])
def job_detail(request, job_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM jobs WHERE id = %s', (job_id,))
                job = cur.fetchone()
        
        if not job:
            return JsonResponse({'error': 'Job not found'}, status=404)
        
        job_data = {
            'id': job['id'],
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'type': job['job_type'],
            'description': job['description'],
            'salary_range': '0K - 50K',
            'experience_level': 'Mid-Senior Level'
        }
        
        return JsonResponse(job_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(['GET'])
def jobs_filters(request):
    return JsonResponse({
        'job_types': ['Full-time', 'Part-time', 'Contract', 'Remote'],
        'experience_levels': ['Entry Level', 'Mid Level', 'Senior Level'],
        'locations': ['San Francisco, CA', 'New York, NY', 'Remote']
    })

@csrf_exempt
@require_http_methods(['GET'])
def unread_count(request):
    return JsonResponse({'unread_count': 0})

# URL patterns
urlpatterns = [
    path('api/', api_root),
    path('api/auth/check-username/', check_username),
    path('api/auth/register/', register_user),
    path('api/auth/login/', login_user),
    path('api/auth/user/', get_current_user),
    path('api/auth/stats/', user_stats),
    path('api/startups/', startups_list),
    path('api/startups/<int:startup_id>/', startup_detail),
    path('api/startups/filters/', startups_filters),
    path('api/jobs/', jobs_list),
    path('api/jobs/<int:job_id>/', job_detail),
    path('api/jobs/filters/', jobs_filters),
    path('api/messaging/unread-count/', unread_count),
]

# WSGI application
application = get_wsgi_application()