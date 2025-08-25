#!/usr/bin/env python3
"""
Enhanced WSGI API with PostgreSQL - Fixed multipart parsing and larger request handling
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from urllib.parse import parse_qs, unquote
import hashlib
import uuid
from datetime import datetime
import cgi
import io

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='startlinker_db',
        user='startlinker_user',
        password='startlinker123',
        cursor_factory=RealDictCursor
    )

def json_response(data, status=200):
    response_data = json.dumps(data, default=str).encode('utf-8')
    return response_data, status

def parse_request_body(body):
    try:
        return json.loads(body.decode('utf-8'))
    except:
        return {}

def parse_multipart_form_data(environ):
    """Parse multipart form data"""
    try:
        content_type = environ.get('CONTENT_TYPE', '')
        if not content_type.startswith('multipart/form-data'):
            return {}
        
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        if content_length == 0:
            return {}
            
        # Create a file-like object from the input
        input_stream = environ['wsgi.input']
        
        # Create FieldStorage object to parse the form
        form = cgi.FieldStorage(
            fp=input_stream,
            environ=environ,
            keep_blank_values=True
        )
        
        # Extract form fields
        form_data = {}
        for field in form.list:
            if field.name:
                if field.filename:  # File upload
                    form_data[field.name] = {
                        'filename': field.filename,
                        'content': field.file.read() if field.file else b'',
                        'content_type': field.type
                    }
                else:  # Regular field
                    form_data[field.name] = field.value
        
        return form_data
        
    except Exception as e:
        print(f"Error parsing multipart data: {e}")
        return {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    return str(uuid.uuid4())

def get_user_from_token(headers):
    """Get user from auth token"""
    auth_header = headers.get('HTTP_AUTHORIZATION', '')
    if not auth_header or not auth_header.startswith('Token '):
        return None
    
    token = auth_header.replace('Token ', '')
    
    # For demo, we'll return a user based on token
    # In production, you'd look up token in database
    if token:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # For now, return first user if token exists
                    cur.execute('SELECT * FROM auth_user ORDER BY id LIMIT 1')
                    return cur.fetchone()
        except:
            pass
    return None

# API Root
def api_root():
    return json_response({
        'message': 'StartLinker API v2.0 - PostgreSQL Connected with Enhanced Multipart Support',
        'endpoints': [
            'GET /api/',
            'GET /api/auth/check-username/',
            'POST /api/auth/register/',
            'POST /api/auth/login/',
            'GET /api/auth/user/',
            'GET /api/startups/',
            'POST /api/startups/',
            'GET /api/startups/<id>/',
            'GET /api/jobs/',
            'POST /api/jobs/',
            'GET /api/jobs/<id>/',
            'GET /api/posts/',
            'POST /api/posts/',
            'GET /api/stories/',
            'POST /api/stories/',
            'GET /social/stories/',
            'POST /social/stories/',
            'GET /social/stories/feed/',
            'GET /api/messaging/unread-count/',
            'GET /ws/achievements/'
        ]
    })

# Auth endpoints
def check_username(query_params):
    username = query_params.get('username', [''])[0]
    if not username:
        return json_response({'is_taken': False})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM auth_user WHERE username = %s', (username,))
                user = cur.fetchone()
                return json_response({'is_taken': bool(user)})
    except:
        return json_response({'is_taken': len(username) < 3})

def register_user(body):
    data = parse_request_body(body)
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    
    if not username or not email or not password:
        return json_response({'error': 'Username, email and password are required'}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if username exists
                cur.execute('SELECT id FROM auth_user WHERE username = %s OR email = %s', (username, email))
                if cur.fetchone():
                    return json_response({'error': 'Username or email already exists'}, 400)
                
                # Insert new user
                hashed_password = hash_password(password)
                cur.execute("""
                    INSERT INTO auth_user (username, email, password, first_name, last_name, date_joined, is_active, is_staff, is_superuser)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (username, email, hashed_password, first_name, last_name, datetime.now(), True, False, False))
                
                user_id = cur.fetchone()['id']
                conn.commit()
                
                # Generate token and return user data
                token = generate_token()
                return json_response({
                    'token': token,
                    'user': {
                        'id': user_id,
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'profile_picture': None
                    }
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

def login_user(body):
    data = parse_request_body(body)
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return json_response({'error': 'Username and password are required'}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                hashed_password = hash_password(password)
                cur.execute("""
                    SELECT id, username, email, first_name, last_name, profile_picture 
                    FROM auth_user 
                    WHERE (username = %s OR email = %s) AND password = %s
                """, (username, username, hashed_password))
                
                user = cur.fetchone()
                if not user:
                    return json_response({'error': 'Invalid credentials'}, 401)
                
                token = generate_token()
                return json_response({
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'profile_picture': user['profile_picture']
                    }
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

def get_current_user(headers):
    user = get_user_from_token(headers)
    if not user:
        return json_response(
            {'detail': 'Authentication credentials were not provided.'}, 
            status=401
        )
    
    return json_response({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'first_name': user['first_name'],
        'last_name': user['last_name'],
        'is_premium': False,
        'profile_picture': user.get('profile_picture')
    })

# Startup endpoints
def startups_list():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.*, u.username as founder_username 
                    FROM startups s
                    LEFT JOIN auth_user u ON s.user_id = u.id 
                    ORDER BY s.id
                """)
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
                'location': 'San Francisco, CA',
                'founder': startup.get('founder_username', 'Anonymous')
            })
        
        return json_response({'results': startups_data, 'count': len(startups_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def create_startup(body, headers):
    user = get_user_from_token(headers)
    if not user:
        return json_response({'error': 'Authentication required'}, 401)
    
    data = parse_request_body(body)
    name = data.get('name', '')
    description = data.get('description', '')
    industry = data.get('industry', '')
    website = data.get('website', '')
    location = data.get('location', '')
    
    if not name or not description:
        return json_response({'error': 'Name and description are required'}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO startups (user_id, name, description, industry, website, founded_date)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """, (user['id'], name, description, industry, website, datetime.now().date()))
                
                startup_id = cur.fetchone()['id']
                conn.commit()
                
                return json_response({
                    'id': startup_id,
                    'name': name,
                    'description': description,
                    'industry': industry,
                    'website': website,
                    'message': 'Startup created successfully'
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

def startup_detail(startup_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.*, u.username as founder_username 
                    FROM startups s
                    LEFT JOIN auth_user u ON s.user_id = u.id 
                    WHERE s.id = %s
                """, (startup_id,))
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
            'location': 'San Francisco, CA',
            'founder': startup.get('founder_username', 'Anonymous')
        }
        
        return json_response(startup_data)
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

# Job endpoints
def jobs_list():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT j.*, u.username as posted_by 
                    FROM jobs j
                    LEFT JOIN auth_user u ON j.user_id = u.id 
                    ORDER BY j.id
                """)
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
                'experience_level': 'Mid-Senior Level',
                'posted_by': job.get('posted_by', 'Anonymous')
            })
        
        return json_response({'results': jobs_data, 'count': len(jobs_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def create_job(body, headers):
    user = get_user_from_token(headers)
    if not user:
        return json_response({'error': 'Authentication required'}, 401)
    
    data = parse_request_body(body)
    title = data.get('title', '')
    company = data.get('company', '')
    description = data.get('description', '')
    location = data.get('location', '')
    job_type = data.get('job_type', 'Full-time')
    
    if not title or not company or not description:
        return json_response({'error': 'Title, company and description are required'}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jobs (user_id, title, company, description, location, job_type, created_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (user['id'], title, company, description, location, job_type, datetime.now().date()))
                
                job_id = cur.fetchone()['id']
                conn.commit()
                
                return json_response({
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'description': description,
                    'location': location,
                    'type': job_type,
                    'message': 'Job created successfully'
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

def job_detail(job_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT j.*, u.username as posted_by 
                    FROM jobs j
                    LEFT JOIN auth_user u ON j.user_id = u.id 
                    WHERE j.id = %s
                """, (job_id,))
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
            'experience_level': 'Mid-Senior Level',
            'posted_by': job.get('posted_by', 'Anonymous')
        }
        
        return json_response(job_data)
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

# Posts endpoints
def posts_list():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*, u.username, u.first_name, u.last_name 
                    FROM posts p
                    LEFT JOIN auth_user u ON p.user_id = u.id 
                    ORDER BY p.created_at DESC
                """)
                posts = cur.fetchall()
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post['id'],
                'title': post['title'],
                'content': post['content'],
                'image_url': post['image_url'],
                'created_at': post['created_at'],
                'author': {
                    'username': post.get('username', 'Anonymous'),
                    'name': f"{post.get('first_name', '')} {post.get('last_name', '')}".strip() or 'Anonymous'
                },
                'is_featured': post['is_featured']
            })
        
        return json_response({'results': posts_data, 'count': len(posts_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def create_post(body, headers):
    user = get_user_from_token(headers)
    if not user:
        return json_response({'error': 'Authentication required'}, 401)
    
    data = parse_request_body(body)
    title = data.get('title', '')
    content = data.get('content', '')
    image_url = data.get('image_url', '')
    
    if not title or not content:
        return json_response({'error': 'Title and content are required'}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO posts (user_id, title, content, image_url, created_at)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (user['id'], title, content, image_url, datetime.now()))
                
                post_id = cur.fetchone()['id']
                conn.commit()
                
                return json_response({
                    'id': post_id,
                    'title': title,
                    'content': content,
                    'image_url': image_url,
                    'message': 'Post created successfully'
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

# Stories endpoints  
def stories_list():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT s.*, u.username, u.first_name, u.last_name, u.profile_picture 
                    FROM stories s
                    LEFT JOIN auth_user u ON s.user_id = u.id 
                    ORDER BY s.created_at DESC
                """)
                stories = cur.fetchall()
        
        stories_data = []
        for story in stories:
            stories_data.append({
                'id': story['id'],
                'title': story['title'],
                'content': story['content'],
                'image_url': story['image_url'],
                'created_at': story['created_at'],
                'author': {
                    'id': story['user_id'],
                    'username': story.get('username', 'Anonymous'),
                    'name': f"{story.get('first_name', '')} {story.get('last_name', '')}".strip() or 'Anonymous',
                    'profile_picture': story.get('profile_picture')
                },
                'view_count': 0,
                'background_color': '#1F2937'
            })
        
        return json_response({'results': stories_data, 'count': len(stories_data)})
    except Exception as e:
        return json_response({'error': str(e)}, status=500)

def create_story(body, environ, headers):
    user = get_user_from_token(headers)
    if not user:
        return json_response({'error': 'Authentication required'}, 401)
    
    content_type = environ.get('CONTENT_TYPE', '')
    
    # Handle multipart form data
    if content_type.startswith('multipart/form-data'):
        form_data = parse_multipart_form_data(environ)
        title = form_data.get('title', '')
        content = form_data.get('content', '')
        story_type = form_data.get('storyType', 'text')
        background_color = form_data.get('backgroundColor', '#1F2937')
        text_color = form_data.get('textColor', '#FFFFFF')
        
        # Handle file uploads
        image_url = ''
        if 'media' in form_data and isinstance(form_data['media'], dict):
            # File upload handling would go here
            # For now, just store the filename
            filename = form_data['media'].get('filename', '')
            if filename:
                image_url = f'/uploads/{filename}'
    else:
        # Handle JSON data
        data = parse_request_body(body)
        title = data.get('title', '')
        content = data.get('content', '')
        story_type = data.get('storyType', 'text')
        background_color = data.get('backgroundColor', '#1F2937')
        image_url = data.get('image_url', '')
    
    if not title or not content:
        return json_response({'error': 'Title and content are required', 'debug': {'title': title, 'content': content}}, 400)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO stories (user_id, title, content, image_url, created_at)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (user['id'], title, content, image_url, datetime.now()))
                
                story_id = cur.fetchone()['id']
                conn.commit()
                
                return json_response({
                    'id': story_id,
                    'title': title,
                    'content': content,
                    'image_url': image_url,
                    'story_type': story_type,
                    'background_color': background_color,
                    'message': 'Story created successfully'
                })
    except Exception as e:
        return json_response({'error': str(e)}, 500)

def social_stories_feed():
    """Social stories feed endpoint"""
    return stories_list()

def view_story(story_id):
    """Mark story as viewed - placeholder endpoint"""
    return json_response({'message': 'Story viewed'})

# Other endpoints
def startups_filters():
    return json_response({
        'industries': ['Technology', 'Healthcare', 'Finance', 'E-commerce'],
        'funding_stages': ['Pre-Seed', 'Seed', 'Series A', 'Series B'],
        'locations': ['San Francisco, CA', 'New York, NY', 'Austin, TX']
    })

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

def achievements_websocket():
    """WebSocket endpoint placeholder - returns empty response"""
    return json_response({'message': 'WebSocket endpoint - achievements'})

def application(environ, start_response):
    """WSGI application"""
    method = environ['REQUEST_METHOD']
    path = environ['PATH_INFO']
    query_string = environ.get('QUERY_STRING', '')
    query_params = parse_qs(query_string)
    headers = environ
    
    # Get request body for POST requests (for JSON data)
    body = b''
    if method == 'POST':
        content_type = environ.get('CONTENT_TYPE', '')
        if not content_type.startswith('multipart/form-data'):
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                body = environ['wsgi.input'].read(content_length)
            except:
                body = b''
    
    # Handle CORS preflight
    if method == 'OPTIONS':
        response_data = b''
        status = 200
        response_headers = [
            ('Content-Type', 'application/json'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'),
            ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ]
        start_response('200 OK', response_headers)
        return [response_data]
    
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
        elif path == '/api/startups/' and method == 'POST':
            response_data, status = create_startup(body, headers)
        elif path == '/api/startups/filters/' and method == 'GET':
            response_data, status = startups_filters()
        elif re.match(r'/api/startups/(\d+)/', path) and method == 'GET':
            startup_id = int(re.match(r'/api/startups/(\d+)/', path).group(1))
            response_data, status = startup_detail(startup_id)
        
        # Job endpoints
        elif path == '/api/jobs/' and method == 'GET':
            response_data, status = jobs_list()
        elif path == '/api/jobs/' and method == 'POST':
            response_data, status = create_job(body, headers)
        elif path == '/api/jobs/filters/' and method == 'GET':
            response_data, status = jobs_filters()
        elif re.match(r'/api/jobs/(\d+)/', path) and method == 'GET':
            job_id = int(re.match(r'/api/jobs/(\d+)/', path).group(1))
            response_data, status = job_detail(job_id)
        
        # Posts endpoints
        elif path == '/api/posts/' and method == 'GET':
            response_data, status = posts_list()
        elif path == '/api/posts/' and method == 'POST':
            response_data, status = create_post(body, headers)
        
        # Stories endpoints - support all paths
        elif path == '/api/stories/' and method == 'GET':
            response_data, status = stories_list()
        elif path == '/api/stories/' and method == 'POST':
            response_data, status = create_story(body, environ, headers)
        elif path == '/social/stories/' and method == 'GET':
            response_data, status = stories_list()
        elif path == '/social/stories/' and method == 'POST':
            response_data, status = create_story(body, environ, headers)
        elif path == '/api/social/stories/' and method == 'GET':
            response_data, status = stories_list()
        elif path == '/api/social/stories/' and method == 'POST':
            response_data, status = create_story(body, environ, headers)
        elif path == '/social/stories/feed/' and method == 'GET':
            response_data, status = social_stories_feed()
        elif path == '/api/social/stories/feed/' and method == 'GET':
            response_data, status = social_stories_feed()
        elif re.match(r'/social/stories/(\d+)/view_story/', path) and method == 'POST':
            story_id = int(re.match(r'/social/stories/(\d+)/view_story/', path).group(1))
            response_data, status = view_story(story_id)
        elif re.match(r'/api/social/stories/(\d+)/view_story/', path) and method == 'POST':
            story_id = int(re.match(r'/api/social/stories/(\d+)/view_story/', path).group(1))
            response_data, status = view_story(story_id)
        
        # WebSocket endpoint (placeholder)
        elif path == '/ws/achievements/' and method == 'GET':
            response_data, status = achievements_websocket()
        
        # Other endpoints
        elif path == '/api/messaging/unread-count/' and method == 'GET':
            response_data, status = unread_count()
        
        else:
            response_data, status = json_response({'error': 'Not found', 'path': path, 'method': method}, 404)
    
    except Exception as e:
        response_data, status = json_response({'error': str(e), 'traceback': str(e)}, 500)
    
    # Set status and headers
    status_text = {
        200: '200 OK',
        400: '400 Bad Request',
        401: '401 Unauthorized', 
        404: '404 Not Found',
        413: '413 Request Entity Too Large',
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