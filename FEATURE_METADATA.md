# StartupHub Feature Metadata Documentation

## Table of Contents
1. [Collections Feature](#collections-feature)
2. [Achievements Feature](#achievements-feature)
3. [Scheduler Feature](#scheduler-feature)

---

## Collections Feature

### Overview
Collections are Pinterest-style boards where users can organize and curate startups they're interested in. Think of them as personalized startup portfolios or watchlists.

### Purpose
- **Organize**: Users can categorize startups based on their interests (e.g., "AI Startups to Watch", "Green Tech Companies", "Investment Opportunities")
- **Collaborate**: Multiple users can contribute to collaborative collections
- **Discover**: Public collections help users discover curated startup lists from other users
- **Track**: Follow collections to get updates when new startups are added

### Key Components

#### 1. StartupCollection (Model)
- **What it is**: The main container for a collection of startups
- **Key Features**:
  - Name and description for the collection
  - Three types: public, private, or collaborative
  - Visual customization with cover images and theme colors
  - Metrics tracking (views, followers)
  - Featured collections for highlighting quality content

#### 2. CollectionItem (Model)
- **What it is**: Individual startups within a collection
- **Key Features**:
  - Links a startup to a collection
  - Custom notes and tags for each item
  - Position ordering for arrangement
  - Track who added the item and when

#### 3. CollectionCollaborator (Model)
- **What it is**: Manages multiple users working on the same collection
- **Permission Levels**:
  - View: Can only see the collection
  - Comment: Can add comments
  - Edit: Can add/remove startups
  - Admin: Full control including adding other collaborators

#### 4. CollectionFollow (Model)
- **What it is**: Allows users to follow collections for updates
- **Features**:
  - Get notifications when collections are updated
  - Build a personalized feed of collection updates

### Use Cases
1. **Investors**: Create collections of potential investment opportunities
2. **Job Seekers**: Organize startups they want to apply to
3. **Researchers**: Curate startups in specific industries
4. **Community Building**: Share curated lists with the community

### Example Workflow
```
1. User creates a collection called "EdTech Innovators"
2. Sets it as public and adds a cover image
3. Browses startups and adds relevant ones to the collection
4. Adds custom notes like "Great team, Series A funded"
5. Other users discover and follow the collection
6. Can invite collaborators to help maintain the collection
```

---

## Achievements Feature

### Overview
A gamification system that rewards users for various activities on the platform, encouraging engagement and recognizing contributions.

### Purpose
- **Engagement**: Motivate users to explore and use platform features
- **Recognition**: Acknowledge user contributions and milestones
- **Progress Tracking**: Show users their journey and growth
- **Community Building**: Create shared goals and challenges

### Key Components

#### 1. Achievement (Model)
- **What it is**: Definition of an achievement that can be earned
- **Categories**:
  - Profile: Complete profile sections
  - Social: Engagement activities (follows, likes, comments)
  - Content: Creating posts, stories, collections
  - Networking: Making connections, messaging
  - Startup: Listing startups, updates
  - Jobs: Posting jobs, applications
  - Special: Time-limited or event-based achievements

- **Rarity Levels** (with colors):
  - Common (Gray): Basic achievements most users will earn
  - Uncommon (Green): Requires moderate effort
  - Rare (Blue): Significant accomplishments
  - Epic (Purple): Major milestones
  - Legendary (Orange): Exceptional achievements

- **Features**:
  - Points system for leaderboards
  - Secret achievements (hidden until earned)
  - Repeatable achievements for ongoing activities
  - Visual elements (icons, colors, badges)

#### 2. UserAchievement (Model)
- **What it is**: Tracks which achievements a user has earned
- **Features**:
  - Timestamp of when earned
  - Progress data snapshot
  - Pin achievements to profile
  - Privacy control (public/private)

#### 3. UserAchievementProgress (Model)
- **What it is**: Real-time tracking of progress towards achievements
- **Features**:
  - JSON-based progress tracking for flexibility
  - Percentage completion
  - Auto-updates based on user activities

### Achievement Examples

1. **"First Steps"** (Common - Profile)
   - Requirement: Complete basic profile information
   - Points: 10
   - Icon: 👤

2. **"Social Butterfly"** (Uncommon - Social)
   - Requirement: Follow 50 users
   - Points: 25
   - Icon: 🦋

3. **"Startup Scout"** (Rare - Content)
   - Requirement: Create 5 collections with 10+ startups each
   - Points: 50
   - Icon: 🔍

4. **"Job Creator"** (Epic - Jobs)
   - Requirement: Post 100 job listings
   - Points: 100
   - Icon: 💼

5. **"Pioneer"** (Legendary - Special)
   - Requirement: Be among first 100 users
   - Points: 500
   - Icon: 🌟
   - Secret: Yes

### Achievement System Workflow
```
1. User performs action (e.g., creates first post)
2. System checks if action matches any achievement requirements
3. Updates UserAchievementProgress
4. If requirements met, creates UserAchievement
5. Sends notification to user
6. Updates user's total points
7. Achievement appears on profile if public
```

---

## Scheduler Feature

### Overview
Allows users to create posts in advance and schedule them for automatic publication at specified times.

### Purpose
- **Time Management**: Write content when convenient, publish when optimal
- **Consistency**: Maintain regular posting schedule
- **Strategic Timing**: Post when audience is most active
- **Content Planning**: Plan and organize content calendar

### Key Components

#### ScheduledPost (Model)
- **What it is**: A post waiting to be published at a future time
- **Features**:
  - All regular post features (title, content, type, attachments)
  - Scheduled publication time
  - Status tracking (scheduled, published, failed, cancelled)
  - Error handling and retry logic
  - Link to published post once live

### Status Workflow
1. **Scheduled**: Post is created and waiting
2. **Published**: Successfully posted at scheduled time
3. **Failed**: Publishing failed (with error message)
4. **Cancelled**: User cancelled before publication

### Scheduling Features

#### Content Types Supported
- Discussion posts
- Questions
- Announcements
- Resources
- Events

#### Attachment Handling
- Images stored as JSON data until publication
- Links metadata preserved
- Topics/tags maintained
- Related startups/jobs connections

#### Use Cases
1. **Content Creators**: Plan week's content in advance
2. **Startup Founders**: Schedule announcements for optimal times
3. **Event Organizers**: Schedule reminders leading up to events
4. **Job Posters**: Schedule job postings for Monday mornings

### Example Workflow
```
1. User writes a post about their startup's new feature
2. Instead of "Post Now", selects "Schedule"
3. Picks date/time (e.g., Tuesday 9 AM when audience is active)
4. Post saved as ScheduledPost with status "scheduled"
5. Background job runs every minute checking for ready posts
6. At scheduled time, system:
   - Creates actual Post from ScheduledPost data
   - Uploads any images
   - Processes links
   - Sets ScheduledPost status to "published"
   - Links to the published post
7. User receives notification of successful publication
```

### Technical Implementation Notes
- Requires background task runner (Celery)
- Checks for scheduled posts every minute
- Handles timezone conversions
- Provides editing/cancellation until publication
- Maintains audit trail of all scheduled posts

---

## Integration Between Features

### Collections + Achievements
- Earn achievements for creating popular collections
- "Curator" achievements for collection milestones
- Special badges for featured collections

### Scheduler + Achievements  
- "Consistent Poster" achievement for scheduled posts
- "Time Master" for using scheduler effectively

### Stories + Achievements
- Story-specific achievements appear as story content
- Share achievement unlocks in stories

### All Features + User Profile
- Achievements displayed on profile
- Featured collections showcase
- Scheduled post calendar view
- Story highlights section

---

## Benefits Summary

1. **User Engagement**: Multiple ways to interact with content
2. **Content Organization**: Collections provide structure
3. **Motivation**: Achievements encourage platform exploration
4. **Flexibility**: Scheduler accommodates different schedules
5. **Community**: Features promote interaction and discovery
6. **Retention**: Gamification and tools keep users returning