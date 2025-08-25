-- Sample Social Features Data for StartupHub
-- This script inserts sample data for Collections, Achievements, and Scheduled Posts

-- Note: This assumes you have existing users and startups in your database
-- Adjust user_id and startup_id values based on your actual data

-- ========================================
-- ACHIEVEMENTS
-- ========================================

-- Profile Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('First Steps', 'first-steps', 'Complete your basic profile information', 'profile', 'common', '👤', '#6B7280', '{"profile_fields": ["first_name", "last_name", "bio"]}', 10, 'Newcomer', true, false, false, 0, NOW(), NOW()),
('Profile Pro', 'profile-pro', 'Complete all profile sections including avatar and background', 'profile', 'uncommon', '⭐', '#10B981', '{"profile_completion": 100}', 25, '', true, false, false, 0, NOW(), NOW());

-- Social Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('Social Butterfly', 'social-butterfly', 'Follow 50 users and build your network', 'social', 'uncommon', '🦋', '#10B981', '{"following_count": 50}', 30, '', true, false, false, 0, NOW(), NOW()),
('Influencer', 'influencer', 'Gain 100 followers', 'social', 'rare', '📢', '#3B82F6', '{"followers_count": 100}', 50, '', true, false, false, 0, NOW(), NOW());

-- Content Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('First Post', 'first-post', 'Create your first post', 'content', 'common', '📝', '#6B7280', '{"posts_count": 1}', 10, '', true, false, false, 0, NOW(), NOW()),
('Content Creator', 'content-creator', 'Create 50 posts and share your knowledge', 'content', 'rare', '✍️', '#3B82F6', '{"posts_count": 50}', 75, '', true, false, false, 0, NOW(), NOW()),
('Curator', 'curator', 'Create 5 collections with at least 10 startups each', 'content', 'rare', '🗂️', '#3B82F6', '{"collections_count": 5, "min_items_per_collection": 10}', 60, '', true, false, false, 0, NOW(), NOW()),
('Scheduler Master', 'scheduler-master', 'Successfully schedule and publish 20 posts', 'content', 'uncommon', '📅', '#10B981', '{"scheduled_posts_published": 20}', 45, '', true, false, false, 0, NOW(), NOW());

-- Networking Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('Connector', 'connector', 'Send 100 messages and build relationships', 'networking', 'uncommon', '🤝', '#10B981', '{"messages_sent": 100}', 40, '', true, false, false, 0, NOW(), NOW()),
('Community Builder', 'community-builder', 'Create a collection with 50+ followers', 'networking', 'epic', '🏛️', '#8B5CF6', '{"collection_followers": 50}', 100, '', true, false, false, 0, NOW(), NOW());

-- Startup Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('Startup Founder', 'startup-founder', 'List your first startup', 'startup', 'common', '🚀', '#6B7280', '{"startups_created": 1}', 20, '', true, false, false, 0, NOW(), NOW()),
('Serial Entrepreneur', 'serial-entrepreneur', 'List 5 startups', 'startup', 'epic', '💼', '#8B5CF6', '{"startups_created": 5}', 150, '', true, false, false, 0, NOW(), NOW());

-- Jobs Achievements
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('Job Creator', 'job-creator', 'Post your first job listing', 'jobs', 'common', '💼', '#6B7280', '{"jobs_posted": 1}', 15, '', true, false, false, 0, NOW(), NOW()),
('Hiring Manager', 'hiring-manager', 'Post 25 job listings', 'jobs', 'rare', '👔', '#3B82F6', '{"jobs_posted": 25}', 80, '', true, false, false, 0, NOW(), NOW());

-- Special Achievements (Secret)
INSERT INTO users_achievement (name, slug, description, category, rarity, icon, color, requirements, points, badge_text, is_active, is_secret, is_repeatable, earned_count, created_at, updated_at)
VALUES 
('Early Adopter', 'early-adopter', 'Among the first 1000 users to join', 'special', 'legendary', '🌟', '#F59E0B', '{"user_id_max": 1000}', 500, 'Pioneer', true, true, false, 0, NOW(), NOW()),
('Night Owl', 'night-owl', 'Post 10 times between midnight and 5 AM', 'special', 'uncommon', '🦉', '#10B981', '{"night_posts": 10}', 35, '', true, true, false, 0, NOW(), NOW());

-- ========================================
-- STARTUP COLLECTIONS (Assuming user IDs 1-5 exist)
-- ========================================

-- AI & Machine Learning Collection
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 1, 'AI & Machine Learning Innovators', 'Cutting-edge startups using AI to solve real-world problems', 'public', '', '#8B5CF6', true, true, 245, 67, NOW(), NOW());

-- Green Tech Collection
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 2, 'Green Tech & Sustainability', 'Startups fighting climate change and promoting sustainability', 'public', '', '#10B981', true, true, 312, 89, NOW(), NOW());

-- EdTech Collection (Collaborative)
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 3, 'EdTech Revolution', 'Transforming education through technology', 'collaborative', '', '#3B82F6', false, true, 156, 42, NOW(), NOW());

-- Private Investment Collection
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 1, 'My Investment Watchlist', 'Private collection of potential investment opportunities', 'private', '', '#F59E0B', false, false, 0, 0, NOW(), NOW());

-- HealthTech Collection
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 4, 'HealthTech Pioneers', 'Digital health and biotech startups', 'public', '', '#EF4444', false, true, 198, 56, NOW(), NOW());

-- FinTech Collection
INSERT INTO users_startupcollection (id, owner_id, name, description, collection_type, cover_image, theme_color, is_featured, allow_comments, view_count, follower_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 5, 'FinTech Disruptors', 'Financial technology startups changing how we handle money', 'public', '', '#6366F1', false, true, 267, 78, NOW(), NOW());

-- ========================================
-- SCHEDULED POSTS (Assuming user IDs 1-5 exist)
-- ========================================

-- Scheduled Discussion Post
INSERT INTO users_scheduledpost (id, author_id, title, content, post_type, scheduled_for, status, images_data, links_data, topics_data, related_startup_id, related_job_id, is_anonymous, published_post_id, error_message, created_at, updated_at, published_at)
VALUES 
(gen_random_uuid(), 1, 'Weekly Startup Spotlight: AI in Healthcare', 
'This week, I want to highlight some amazing startups using AI to revolutionize healthcare:

1. **MedAI Diagnostics** - Using computer vision for early disease detection
2. **HealthBot Pro** - AI-powered patient triage and support
3. **GenomeAI** - Machine learning for personalized medicine

What are your thoughts on AI in healthcare? Share your favorite health tech startups below!

#HealthTech #AIStartups #Innovation', 
'discussion', NOW() + INTERVAL '1 day 9 hours', 'scheduled', '[]', '[]', '["healthtech", "ai", "startups"]', NULL, NULL, false, NULL, '', NOW(), NOW(), NULL);

-- Scheduled Announcement
INSERT INTO users_scheduledpost (id, author_id, title, content, post_type, scheduled_for, status, images_data, links_data, topics_data, related_startup_id, related_job_id, is_anonymous, published_post_id, error_message, created_at, updated_at, published_at)
VALUES 
(gen_random_uuid(), 2, 'Join us for Green Tech Summit 2025!', 
'Excited to announce that our startup will be presenting at the Green Tech Summit next month!

📅 Date: March 15-17, 2025
📍 Location: San Francisco Convention Center
🎟️ Use code STARTUP20 for 20% off tickets

We''ll be showcasing our latest solar panel efficiency breakthrough. Hope to see you there!

#GreenTech #Sustainability #StartupEvents', 
'announcement', NOW() + INTERVAL '7 days 10 hours', 'scheduled', '[]', '[]', '["greentech", "events", "sustainability"]', NULL, NULL, false, NULL, '', NOW(), NOW(), NULL);

-- Scheduled Question
INSERT INTO users_scheduledpost (id, author_id, title, content, post_type, scheduled_for, status, images_data, links_data, topics_data, related_startup_id, related_job_id, is_anonymous, published_post_id, error_message, created_at, updated_at, published_at)
VALUES 
(gen_random_uuid(), 3, 'What features do you want in an EdTech platform?', 
'We''re building the next generation of online learning platforms and want YOUR input!

What features are missing from current EdTech solutions?
- Better collaboration tools?
- AI-powered tutoring?
- Gamification elements?
- VR/AR integration?

Drop your ideas in the comments! The best suggestions will be featured in our beta.

#EdTech #ProductDevelopment #CommunityFeedback', 
'question', NOW() + INTERVAL '2 days 14 hours', 'scheduled', '[]', '[]', '["edtech", "product-development", "feedback"]', NULL, NULL, false, NULL, '', NOW(), NOW(), NULL);

-- ========================================
-- USER FOLLOWS (Creating follow relationships)
-- ========================================

-- Sample follow relationships (adjust user IDs as needed)
INSERT INTO users_userfollow (follower_id, following_id, created_at, notify_on_posts, notify_on_stories, notify_on_achievements)
VALUES 
(1, 2, NOW(), true, true, false),
(1, 3, NOW(), true, false, true),
(2, 1, NOW(), true, true, true),
(2, 4, NOW(), true, false, false),
(3, 1, NOW(), true, true, false),
(3, 5, NOW(), true, true, true),
(4, 2, NOW(), true, false, false),
(5, 1, NOW(), true, true, true);

-- ========================================
-- STORIES (Time-limited content)
-- ========================================

-- Text Story
INSERT INTO users_story (id, author_id, story_type, text_content, image, video, link_url, link_title, link_description, related_startup_id, related_job_id, is_active, expires_at, background_color, text_color, view_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 1, 'text', 'Just closed our Series A! 🎉 Grateful for everyone who believed in our vision. Big things coming!', '', '', '', '', '', NULL, NULL, true, NOW() + INTERVAL '24 hours', '#8B5CF6', '#FFFFFF', 156, NOW(), NOW());

-- Achievement Story
INSERT INTO users_story (id, author_id, story_type, text_content, image, video, link_url, link_title, link_description, related_startup_id, related_job_id, is_active, expires_at, background_color, text_color, view_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 2, 'achievement', 'Finally hit 100 followers! Thanks for all the support 🙏', '', '', '', '', '', NULL, NULL, true, NOW() + INTERVAL '24 hours', '#10B981', '#FFFFFF', 89, NOW(), NOW());

-- Link Story
INSERT INTO users_story (id, author_id, story_type, text_content, image, video, link_url, link_title, link_description, related_startup_id, related_job_id, is_active, expires_at, background_color, text_color, view_count, created_at, updated_at)
VALUES 
(gen_random_uuid(), 3, 'link', 'Check out our latest blog post on the future of EdTech!', '', '', 'https://example.com/blog/future-of-edtech', 'The Future of Education Technology', 'How AI and VR are transforming the classroom', NULL, NULL, true, NOW() + INTERVAL '24 hours', '#3B82F6', '#FFFFFF', 234, NOW(), NOW());

-- ========================================
-- USER ACHIEVEMENTS (Assigning achievements to users)
-- ========================================

-- Note: You'll need to get the actual achievement IDs from the achievements table after inserting them
-- This is a template - replace achievement_id with actual IDs

-- User 1 achievements
INSERT INTO users_userachievement (user_id, achievement_id, earned_at, progress_data, is_pinned, is_public)
SELECT 1, id, NOW(), '{"progress": "completed"}', true, true 
FROM users_achievement WHERE slug = 'first-steps';

INSERT INTO users_userachievement (user_id, achievement_id, earned_at, progress_data, is_pinned, is_public)
SELECT 1, id, NOW(), '{"posts_count": 15}', false, true 
FROM users_achievement WHERE slug = 'first-post';

-- User 2 achievements
INSERT INTO users_userachievement (user_id, achievement_id, earned_at, progress_data, is_pinned, is_public)
SELECT 2, id, NOW(), '{"following_count": 52}', true, true 
FROM users_achievement WHERE slug = 'social-butterfly';

-- Update achievement earned counts
UPDATE users_achievement SET earned_count = earned_count + 1 
WHERE slug IN ('first-steps', 'first-post', 'social-butterfly');