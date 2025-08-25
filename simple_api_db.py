#!/usr/bin/env python3
"""
Simple WSGI API with PostgreSQL - No Django Dependencies
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from urllib.parse import parse_qs

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='startlinker_db',
        user='startlinker_user',
        password='startlinker123',
        cursor_factory=RealDictCursor
    )

def json_response(data, status=200):
    response_data = json.dumps(data).encode('utf-8')
    return response_data, status

def parse_request_body(body):
    try:
        return json.loads(body.decode('utf-8'))
    except:
        return {}

def api_root():
    return json_response({
        'message': 'StartLinker API v1.0 - PostgreSQL Connected',
        'endpoints': [
            '/api/',
            '/api/auth/check-username/',
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/auth/user/',
            '/api/startups/',
            '/api/startups/<id>/',
            '/api/jobs/',
            '/api/jobs/<id>/',
            '/api/messaging/unread-count/'
        ]
    })

def check_username(query_params):
    username = query_params.get('username', [''])[0]
    return json_response({'is_taken': len(username) < 3})

def register_user(body):
    data = parse_request_body(body)
    return json_response({
        'message': 'User registered successfully',
        'user': {
            'id': 1,
            'username': data.get('username', ''),
            'email': data.get('email', '')
        }
    })

def login_user(body):
    data = parse_request_body(body)
    return json_response({
        'token': 'sample-auth-token-123',
        'user': {
            'id': 1,
            'username': data.get('username', ''),
            'email': 'user@startlinker.com',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    })

def get_current_user(headers):
    auth_header = headers.get('HTTP_AUTHORIZATION', '')
    if not auth_header or not auth_header.startswith('Token '):
        return json_response(
            {'detail': 'Authentication credentials were not provided.'}, 
            status=401
        )
    
    return json_response({
        'id': 1,
        'username': 'demo_user',
        'email': 'demo@startlinker.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'is_premium': False,
        'profile_picture': None
    })

def startups_list():
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
        
        return json_response({'results': startups_data, 'count': len(startups_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def startup_detail(startup_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM startups WHERE id = %s', (startup_id,))
                startup = cur.fetchone()
        
        if not startup:
            return json_response({'error': 'Startup not found'}, status=404)
        
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
        
        return json_response(startup_data)
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def startups_filters():
    return json_response({
        'industries': ['Technology', 'Healthcare', 'Finance', 'E-commerce'],
        'funding_stages': ['Pre-Seed', 'Seed', 'Series A', 'Series B'],
        'locations': ['San Francisco, CA', 'New York, NY', 'Austin, TX']
    })

def jobs_list():
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
        
        return json_response({'results': jobs_data, 'count': len(jobs_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def job_detail(job_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM jobs WHERE id = %s', (job_id,))
                job = cur.fetchone()
        
        if not job:
            return json_response({'error': 'Job not found'}, status=404)
        
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
        
        return json_response(job_data)
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def jobs_filters():
    return json_response({
        'job_types': ['Full-time', 'Part-time', 'Contract', 'Remote'],
        'experience_levels': ['Entry Level', 'Mid Level', 'Senior Level'],
        'locations': ['San Francisco, CA', 'New York, NY', 'Remote']
    })

def unread_count():
    return json_response({'unread_count': 0})

def user_stats():
    return json_response({
        'total_users': 1250,
        'active_users': 890,
        'new_users_today': 15
    })

def application(environ, start_response):
    """WSGI application"""
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    query_string = environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    headers = environ
    
    # Get request body for POST requests
    try:
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        body = environ['wsgi.input'].read(content_length)
    except:
        body = b''
    
    # Route handling
    try:
        # API root
        if path == '/api/' and method == 'GET':
            response_data, status = api_root()
        
        # Auth endpoints
        elif path == '/api/auth/check-username/' and method == 'GET':
            response_data, status = check_username(query_params)
        elif path == '/api/auth/register/' and method == 'POST':
            response_data, status = register_user(body)
        elif path == '/api/auth/login/' and method == 'POST':
            response_data, status = login_user(body)
        elif path == '/api/auth/user/' and method == 'GET':
            response_data, status = get_current_user(headers)
        elif path == '/api/auth/stats/' and method == 'GET':
            response_data, status = user_stats()
        
        # Startup endpoints
        elif path == '/api/startups/' and method == 'GET':
            response_data, status = startups_list()
        elif path == '/api/startups/filters/' and method == 'GET':
            response_data, status = startups_filters()
        elif re.match(r'/api/startups/(\d+)/', path) and method == 'GET':
            startup_id = int(re.match(r'/api/startups/(\d+)/', path).group(1))
            response_data, status = startup_detail(startup_id)
        
        # Job endpoints
        elif path == '/api/jobs/' and method == 'GET':
            response_data, status = jobs_list()
        elif path == '/api/jobs/filters/' and method == 'GET':
            response_data, status = jobs_filters()
        elif re.match(r'/api/jobs/(\d+)/', path) and method == 'GET':
            job_id = int(re.match(r'/api/jobs/(\d+)/', path).group(1))
            response_data, status = job_detail(job_id)
        
        # Other endpoints
        elif path == '/api/messaging/unread-count/' and method == 'GET':
            response_data, status = unread_count()
        
        else:
            response_data, status = json_response({'error': 'Not found'}, 404)
    
    except Exception as e:
        response_data, status = json_response({'error': str(e)}, 500)
    
    # Set status and headers
    status_text = {
        200: '200 OK',
        401: '401 Unauthorized', 
        404: '404 Not Found',
        500: '500 Internal Server Error'
    }.get(status, '200 OK')
    
    response_headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
    ]
    
    start_response(status_text, response_headers)
    return [response_data]