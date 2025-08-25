# StartupHub Component Metadata

## Component Architecture Overview

This document provides detailed metadata for each component in the StartupHub platform, explaining their purpose, relationships, and key functionalities.

## 🏗️ Core Components

### 1. **Users App** (`apps/users/`)
**Purpose**: Manages user accounts, authentication, and social features

#### Key Models
- **User**: Extended Django user model with startup-specific fields
- **UserProfile**: Additional profile information and preferences
- **UserSettings**: User-specific configuration options
- **Resume**: User resume management for job applications
- **UserFollow**: Following relationships between users
- **UserPoints**: Gamification points tracking
- **Achievement/UserAchievement**: Achievement system implementation

#### Key Features
- Custom authentication backend
- Social login integration
- Profile completion tracking
- Achievement unlocking system
- Points and rewards system
- Activity tracking
- Profanity filtering for user-generated content

#### API Endpoints
- `/api/users/register/`: New user registration
- `/api/users/login/`: User authentication
- `/api/users/profile/`: Profile management
- `/api/users/follow/`: Follow/unfollow users
- `/api/users/achievements/`: Achievement tracking
- `/api/users/activity/`: User activity feed

### 2. **Startups App** (`apps/startups/`)
**Purpose**: Manages startup profiles and related information

#### Key Models
- **Startup**: Company profile with comprehensive details
- **Industry**: Industry categorization
- **StartupMember**: Team members and their roles
- **StartupMetrics**: Performance and growth metrics

#### Key Features
- Startup profile creation and editing
- Industry-based categorization
- Team management
- Funding information tracking
- Search and filtering capabilities
- Startup verification system

#### API Endpoints
- `/api/startups/`: List and create startups
- `/api/startups/<id>/`: Retrieve, update, delete startup
- `/api/startups/search/`: Advanced search functionality
- `/api/startups/industries/`: Industry listings
- `/api/startups/<id>/team/`: Team management

### 3. **Posts App** (`apps/posts/`)
**Purpose**: Content creation and management system

#### Key Models
- **Post**: Main content model with various types
- **ScheduledPost**: Posts scheduled for future publication
- **PostAttachment**: Images and files attached to posts
- **PostLink**: External links with metadata
- **Comment**: User comments on posts
- **PostReaction**: Likes and other reactions
- **PostRanking**: Algorithm-based content ranking

#### Key Features
- Multiple post types (Discussion, Question, Event, etc.)
- Rich text editing
- Media attachments
- Link preview generation
- Comment threading
- Reaction system
- Content scheduling
- Ranking algorithm for feed curation

#### API Endpoints
- `/api/posts/`: Create and list posts
- `/api/posts/<id>/`: Post details and management
- `/api/posts/<id>/comments/`: Comment management
- `/api/posts/<id>/react/`: Add reactions
- `/api/posts/scheduled/`: Manage scheduled posts
- `/api/posts/feed/`: Personalized feed

### 4. **Jobs App** (`apps/jobs/`)
**Purpose**: Job board functionality for startup opportunities

#### Key Models
- **Job**: Job listing with detailed requirements
- **JobApplication**: Applications submitted by users
- **ApplicationStatus**: Application tracking states
- **JobCategory**: Job type categorization

#### Key Features
- Job posting by startups
- Advanced job search
- Application management
- Resume attachment
- Application status tracking
- Expired job handling
- Email notifications

#### API Endpoints
- `/api/jobs/`: List and create jobs
- `/api/jobs/<id>/`: Job details
- `/api/jobs/<id>/apply/`: Submit application
- `/api/jobs/applications/`: View applications
- `/api/jobs/categories/`: Job categories

### 5. **Messaging App** (`apps/messaging/`)
**Purpose**: Real-time communication between users

#### Key Models
- **Conversation**: Chat sessions between users
- **Message**: Individual messages
- **MessageReaction**: Message reactions
- **BusinessCard**: Professional info sharing
- **VideoCall**: Video call sessions

#### Key Features
- Real-time WebSocket messaging
- Group conversations
- Message types (text, voice, image, video)
- Read receipts
- Typing indicators
- Business card sharing
- Video calling integration
- Message search

#### WebSocket Endpoints
- `ws/messaging/`: Main messaging websocket
- `ws/notifications/`: Real-time notifications

#### API Endpoints
- `/api/messages/conversations/`: List conversations
- `/api/messages/send/`: Send message
- `/api/messages/history/`: Message history
- `/api/messages/video-call/`: Initiate video call

### 6. **Collections App** (within `apps/users/`)
**Purpose**: Curated lists of startups (Pinterest-style boards)

#### Key Models
- **StartupCollection**: Collection container
- **CollectionItem**: Startups in collections
- **CollectionCollaborator**: Multi-user collaboration
- **CollectionFollow**: Following collections

#### Key Features
- Public/private/collaborative collections
- Visual customization
- Collaborative editing with permissions
- Collection following
- Featured collections
- Tags and categorization

#### API Endpoints
- `/api/collections/`: List and create collections
- `/api/collections/<id>/items/`: Manage collection items
- `/api/collections/<id>/collaborators/`: Manage collaborators
- `/api/collections/featured/`: Featured collections

### 7. **Notifications App** (`apps/notifications/`)
**Purpose**: System-wide notification management

#### Key Models
- **Notification**: Base notification model
- **NotificationPreference**: User notification settings
- **NotificationQueue**: Pending notifications

#### Key Features
- Multiple notification types
- Real-time delivery
- Email notification integration
- Notification preferences
- Mark as read/unread
- Bulk notification management

#### API Endpoints
- `/api/notifications/`: List notifications
- `/api/notifications/mark-read/`: Mark as read
- `/api/notifications/preferences/`: Manage preferences

### 8. **Analysis App** (`apps/analysis/`)
**Purpose**: Analytics and insights generation

#### Key Models
- **UserAnalytics**: User behavior tracking
- **StartupAnalytics**: Startup performance metrics
- **ContentAnalytics**: Content engagement tracking
- **PlatformMetrics**: Overall platform statistics

#### Key Features
- User engagement tracking
- Content performance analysis
- Startup growth metrics
- Platform-wide statistics
- Custom report generation
- Data visualization

#### API Endpoints
- `/api/analysis/user/`: User analytics
- `/api/analysis/startup/`: Startup metrics
- `/api/analysis/content/`: Content performance
- `/api/analysis/platform/`: Platform statistics

### 9. **Reports App** (`apps/reports/`)
**Purpose**: Content moderation and user safety

#### Key Models
- **Report**: Base report model
- **PostReport**: Reported posts
- **UserReport**: Reported users
- **UserWarning**: Moderation warnings
- **UserBan**: Ban management

#### Key Features
- Content reporting system
- User reporting
- Moderation queue
- Automated content filtering
- Warning system
- Temporary and permanent bans
- Appeal process

#### API Endpoints
- `/api/reports/create/`: Submit report
- `/api/reports/moderate/`: Moderation actions
- `/api/reports/appeals/`: Appeal management

### 10. **Subscriptions App** (`apps/subscriptions/`)
**Purpose**: Premium features and monetization

#### Key Models
- **SubscriptionPlan**: Available plans
- **UserSubscription**: Active subscriptions
- **PaymentHistory**: Payment records
- **Feature**: Premium features

#### Key Features
- Multiple subscription tiers
- Stripe payment integration
- Recurring billing
- Feature gating
- Usage tracking
- Billing history
- Subscription management

#### API Endpoints
- `/api/subscriptions/plans/`: Available plans
- `/api/subscriptions/subscribe/`: Create subscription
- `/api/subscriptions/cancel/`: Cancel subscription
- `/api/subscriptions/billing/`: Billing history

### 11. **Connect App** (`apps/connect/`)
**Purpose**: Networking and connection features

#### Key Models
- **Connection**: User connections
- **ConnectionRequest**: Pending requests
- **NetworkGroup**: User groups
- **Event**: Networking events

#### Key Features
- Connection requests
- Mutual connections
- Network groups
- Event organization
- Connection recommendations
- Network analytics

#### API Endpoints
- `/api/connect/request/`: Send connection request
- `/api/connect/accept/`: Accept request
- `/api/connect/groups/`: Manage groups
- `/api/connect/events/`: Event management

### 12. **Core App** (`apps/core/`)
**Purpose**: Shared utilities and base functionality

#### Key Features
- Base model classes
- Common mixins
- Utility functions
- Middleware
- Custom permissions
- Health checks
- Management commands

#### Utilities
- Email helpers
- File upload handlers
- Image processing
- URL shortening
- Data validators
- Cache management

## 🔄 Component Interactions

### User Flow Examples

#### 1. **New User Onboarding**
```
Users App → Create Account
    ↓
Users App → Complete Profile
    ↓
Achievements App → Unlock "First Steps"
    ↓
Notifications App → Welcome Notification
    ↓
Posts App → View Feed
```

#### 2. **Job Application Process**
```
Jobs App → Browse Jobs
    ↓
Users App → Upload Resume
    ↓
Jobs App → Submit Application
    ↓
Notifications App → Application Confirmation
    ↓
Messaging App → Recruiter Contact
```

#### 3. **Content Creation Flow**
```
Posts App → Create Post
    ↓
Analysis App → Track Creation
    ↓
Posts App → Schedule/Publish
    ↓
Notifications App → Notify Followers
    ↓
Achievements App → Check Milestones
```

## 🔌 Integration Points

### Internal Integrations
1. **Users ↔ All Apps**: Authentication and authorization
2. **Notifications ↔ All Apps**: Event-driven notifications
3. **Analysis ↔ All Apps**: Data collection and metrics
4. **Core ↔ All Apps**: Shared utilities and base classes

### External Integrations
1. **Storage**: AWS S3 for media files
2. **Email**: SMTP/Anymail for emails
3. **Payments**: Stripe for subscriptions
4. **Cache**: Redis for performance
5. **Search**: PostgreSQL full-text search

## 📊 Data Flow

### Real-time Data
- WebSocket connections for messaging
- Server-sent events for notifications
- Polling for activity feeds
- WebRTC for video calls

### Batch Processing
- Celery tasks for heavy operations
- Scheduled jobs for maintenance
- Background email sending
- Analytics aggregation

## 🛡️ Security Layers

### Component-Level Security
1. **Authentication**: JWT tokens, session management
2. **Authorization**: Permission classes per view
3. **Validation**: Serializer-level validation
4. **Sanitization**: Input cleaning and XSS prevention
5. **Rate Limiting**: API throttling per endpoint

## 🎯 Performance Optimization

### Caching Strategy
- Redis for session data
- Database query caching
- Static file caching
- API response caching

### Database Optimization
- Indexed fields for search
- Query optimization
- Connection pooling
- Read replicas (production)

## 📱 Frontend Integration

### API Design Principles
- RESTful endpoints
- Consistent response formats
- Pagination support
- Filter and search parameters
- Error handling standards

### WebSocket Protocol
- Authentication via tokens
- Heartbeat mechanism
- Reconnection handling
- Message queuing

---

**Note**: This component metadata should be updated as new features are added or existing components are modified. Each component should maintain its own detailed documentation for specific implementation details.