# StartLinker

A comprehensive startup platform connecting entrepreneurs, investors, and job seekers.

## Features

- **Startup Directory**: Browse and discover innovative startups
- **Job Board**: Find opportunities at growing companies
- **Social Feed**: Connect with the startup community
- **Professional Networking**: Build meaningful connections
- **Messaging System**: Direct communication between users
- **User Profiles**: Showcase your startup or professional background

## Tech Stack

### Backend
- Django 4.2+ with Django REST Framework
- PostgreSQL database
- Token-based authentication
- Real-time messaging with WebSockets

### Frontend
- React 18+ with modern hooks
- Tailwind CSS for styling
- Axios for API communication
- Real-time updates

## Deployment

This project is configured for deployment on Render.com with:
- Automatic PostgreSQL database setup
- Production-ready Django configuration
- Static file serving with WhiteNoise
- CORS properly configured

### Quick Deploy

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically deploy using the `render.yaml` configuration

### Manual Setup

See `RENDER_DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, uses SQLite by default)

### Backend Setup
```bash
cd startup_hub
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Endpoints

- `/api/auth/` - Authentication
- `/api/startups/` - Startup directory
- `/api/jobs/` - Job listings
- `/api/posts/` - Social feed
- `/api/users/` - User profiles
- `/api/messages/` - Direct messaging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For deployment help, see the included deployment guides or contact support.

---

**Live Demo**: Will be available after deployment to Render.com