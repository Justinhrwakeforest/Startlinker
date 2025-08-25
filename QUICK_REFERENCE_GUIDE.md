# StartupHub Quick Reference Guide

## 🚀 For Developers

### Quick Setup
```bash
# Backend Setup
cd startup_hub
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend Setup
cd ../frontend
npm install
npm start
```

### Common Commands
```bash
# Database
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Static Files
python manage.py collectstatic

# Create test data
python manage.py loaddata sample_data.json

# Run tests
python manage.py test

# Management commands
python manage.py create_achievements
python manage.py sync_follower_counts
python manage.py delete_expired_jobs
```

### API Testing
```bash
# Get auth token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/users/profile/
```

### WebSocket Testing
```javascript
// Connect to messaging
const ws = new WebSocket('ws://localhost:8000/ws/messaging/');
ws.onmessage = (event) => console.log(event.data);
```

## 👥 For Users

### Getting Started
1. **Sign Up**: Create account with email
2. **Complete Profile**: Add photo, bio, skills
3. **Follow Topics**: Select interests
4. **Connect**: Find and follow other users
5. **Explore**: Browse startups and jobs

### Key Features

#### Creating Content
- **Posts**: Share updates, questions, resources
- **Stories**: 24-hour temporary content
- **Collections**: Organize favorite startups
- **Schedule**: Plan posts in advance

#### Networking
- **Follow Users**: Get updates from people
- **Join Groups**: Topic-based communities
- **Message**: Direct chat with connections
- **Video Calls**: Face-to-face meetings

#### Job Hunting
- **Browse Jobs**: Filter by role, location, salary
- **Quick Apply**: One-click with saved resume
- **Track Applications**: Monitor status
- **Get Alerts**: Notifications for new matches

#### Achievements
- **Earn Badges**: Complete platform activities
- **Level Up**: Gain points and recognition
- **Showcase**: Display on your profile
- **Compete**: Leaderboards and challenges

### Power User Tips
1. **Keyboard Shortcuts**:
   - `Ctrl/Cmd + K`: Quick search
   - `N`: New post
   - `M`: Messages
   - `?`: Show all shortcuts

2. **Advanced Search**:
   - Use quotes for exact matches
   - `tag:remote` for tagged content
   - `from:username` for user content
   - `has:image` for posts with images

3. **Collection Organization**:
   - Use emoji in titles for visual organization
   - Create themed collections
   - Collaborate with others
   - Make collections public for followers

4. **Scheduling Strategy**:
   - Post during peak hours (9-10 AM, 2-3 PM)
   - Schedule weekly content batches
   - Use analytics to find best times

## 🛠️ Troubleshooting

### Common Issues

#### Backend
| Issue | Solution |
|-------|----------|
| Migration errors | `python manage.py migrate --run-syncdb` |
| Redis connection | Check Redis is running: `redis-cli ping` |
| Static files 404 | Run `python manage.py collectstatic` |
| CORS errors | Check `CORS_ALLOWED_ORIGINS` in settings |

#### Frontend
| Issue | Solution |
|-------|----------|
| Build fails | Clear cache: `npm cache clean --force` |
| API not connecting | Check `.env` file for correct API URL |
| WebSocket errors | Ensure channels is running |
| Blank page | Check browser console for errors |

### Performance Tips
- Enable Redis caching
- Use pagination for large lists
- Optimize images before upload
- Enable gzip compression
- Use CDN for static files

## 📋 Feature Checklist

### Essential Features
- [x] User registration and login
- [x] Profile management
- [x] Startup listings
- [x] Job board
- [x] Messaging system
- [x] Post creation
- [x] Search functionality
- [x] Mobile responsive

### Advanced Features
- [x] Real-time notifications
- [x] Achievement system
- [x] Content scheduling
- [x] Collections
- [x] Video calls
- [x] Analytics dashboard
- [x] Subscription system
- [x] Content moderation

### Upcoming Features
- [ ] AI-powered recommendations
- [ ] Native mobile apps
- [ ] Advanced analytics
- [ ] API marketplace
- [ ] Virtual events
- [ ] Mentorship matching

## 🔗 Important Links

### Documentation
- API Docs: `/api/docs/`
- Admin Panel: `/admin/`
- Health Check: `/api/health/`
- WebSocket Test: `/ws/test/`

### External Resources
- Django Docs: https://docs.djangoproject.com/
- React Docs: https://react.dev/
- DRF Docs: https://www.django-rest-framework.org/
- Channels Docs: https://channels.readthedocs.io/

## 🚨 Emergency Contacts

### System Issues
- Check logs: `tail -f logs/django.log`
- Monitor Redis: `redis-cli monitor`
- Database status: `python manage.py dbshell`
- Service health: `/api/health/`

### Quick Fixes
```bash
# Restart services
sudo systemctl restart nginx
sudo systemctl restart gunicorn
sudo systemctl restart redis
sudo systemctl restart postgresql

# Clear cache
python manage.py clear_cache

# Rebuild search index
python manage.py rebuild_index

# Fix permissions
chmod -R 755 media/
chmod -R 755 static/
```

## 💡 Best Practices

### Code Style
- Follow PEP 8 for Python
- Use ESLint for JavaScript
- Write meaningful commit messages
- Document all API endpoints
- Add tests for new features

### Security
- Never commit sensitive data
- Use environment variables
- Validate all user input
- Keep dependencies updated
- Regular security audits

### Performance
- Profile before optimizing
- Use database indexes
- Implement caching strategically
- Lazy load images
- Minimize API calls

---

**Remember**: When in doubt, check the documentation or ask in the developer chat!