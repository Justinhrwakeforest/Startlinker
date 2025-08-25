# Collaboration Metadata Structure

This document defines the structure for the `metadata` field in the StartupCollection (Collaboration) model.

## Overview

The `metadata` field is a JSON field that stores extended information about collaborations. This flexible structure allows for different types of collaborations to store relevant data without modifying the database schema.

## Base Metadata Structure

```json
{
  "version": "1.0",
  "created_at": "2025-01-30T10:00:00Z",
  "last_updated": "2025-01-30T10:00:00Z",
  
  "collaboration_details": {
    "industry": ["technology", "healthcare", "fintech"],
    "stage": "ideation|development|launch|growth",
    "funding_status": "bootstrapped|seeking|funded",
    "location": {
      "city": "San Francisco",
      "state": "CA",
      "country": "USA",
      "remote_friendly": true
    }
  },
  
  "resources": {
    "tools": [
      {
        "name": "Slack",
        "type": "communication",
        "url": "https://team.slack.com",
        "access_level": "all_members"
      },
      {
        "name": "GitHub",
        "type": "development",
        "url": "https://github.com/team/repo",
        "access_level": "contributors"
      }
    ],
    "documents": [
      {
        "name": "Business Plan",
        "type": "planning",
        "url": "https://docs.google.com/...",
        "last_updated": "2025-01-30",
        "owner": "user_id"
      }
    ],
    "budget": {
      "total": 50000,
      "currency": "USD",
      "allocated": 15000,
      "spent": 5000
    }
  },
  
  "team_structure": {
    "roles": [
      {
        "title": "Project Lead",
        "user_id": "uuid",
        "responsibilities": ["Overall project management", "Stakeholder communication"],
        "time_commitment": "20 hours/week"
      },
      {
        "title": "Technical Lead",
        "user_id": "uuid",
        "responsibilities": ["Architecture decisions", "Code reviews"],
        "time_commitment": "15 hours/week"
      }
    ],
    "departments": [
      {
        "name": "Engineering",
        "lead": "user_id",
        "members": ["user_id1", "user_id2"]
      },
      {
        "name": "Marketing",
        "lead": "user_id",
        "members": ["user_id3", "user_id4"]
      }
    ]
  },
  
  "progress_tracking": {
    "kpis": [
      {
        "name": "User Signups",
        "target": 1000,
        "current": 250,
        "unit": "users",
        "deadline": "2025-03-01"
      },
      {
        "name": "Revenue",
        "target": 10000,
        "current": 2500,
        "unit": "USD",
        "deadline": "2025-06-01"
      }
    ],
    "sprints": [
      {
        "number": 1,
        "start_date": "2025-01-01",
        "end_date": "2025-01-14",
        "goals": ["Setup infrastructure", "Initial MVP"],
        "status": "completed",
        "velocity": 21
      }
    ],
    "roadmap": [
      {
        "phase": "MVP Development",
        "start_date": "2025-01-01",
        "end_date": "2025-02-15",
        "status": "in_progress",
        "completion_percentage": 60
      }
    ]
  },
  
  "communication": {
    "channels": [
      {
        "type": "slack",
        "name": "#general",
        "purpose": "General discussions"
      },
      {
        "type": "email",
        "list": "team@project.com",
        "purpose": "Weekly updates"
      }
    ],
    "meeting_notes": [
      {
        "date": "2025-01-30",
        "type": "weekly_standup",
        "attendees": ["user_id1", "user_id2"],
        "summary": "Discussed Q1 goals",
        "recording_url": "https://..."
      }
    ]
  },
  
  "analytics": {
    "engagement": {
      "active_members_last_7_days": 8,
      "total_tasks_completed": 45,
      "average_task_completion_time": "3.5 days"
    },
    "activity_heatmap": {
      "monday": 15,
      "tuesday": 22,
      "wednesday": 18,
      "thursday": 25,
      "friday": 20,
      "saturday": 5,
      "sunday": 3
    }
  },
  
  "integrations": {
    "github": {
      "enabled": true,
      "repo_url": "https://github.com/team/repo",
      "webhook_configured": true,
      "last_sync": "2025-01-30T09:00:00Z"
    },
    "trello": {
      "enabled": false,
      "board_id": null
    },
    "calendar": {
      "enabled": true,
      "calendar_id": "team@calendar.com",
      "sync_frequency": "hourly"
    }
  },
  
  "custom_fields": {
    "target_market": "B2B SaaS",
    "competitive_advantage": "AI-powered automation",
    "exit_strategy": "Acquisition",
    "advisor_network": ["advisor1", "advisor2"]
  }
}
```

## Metadata Field Guidelines

### 1. Version Control
- Always include a `version` field to track metadata structure changes
- Use semantic versioning (e.g., "1.0", "1.1", "2.0")

### 2. Timestamps
- Include `created_at` and `last_updated` for tracking
- Use ISO 8601 format for all timestamps

### 3. Flexibility
- The structure is flexible and can be extended
- Not all fields are required for every collaboration
- Add custom fields under `custom_fields` for specific needs

### 4. Data Types
- **Arrays**: Use for lists (tools, documents, team members)
- **Objects**: Use for structured data (location, budget)
- **Numbers**: Use for metrics and counts
- **Strings**: Use for text, URLs, and identifiers
- **Booleans**: Use for flags and settings

## Usage Examples

### 1. Startup Development Project
```python
metadata = {
    "version": "1.0",
    "collaboration_details": {
        "industry": ["fintech"],
        "stage": "development",
        "funding_status": "seeking"
    },
    "resources": {
        "budget": {
            "total": 100000,
            "currency": "USD"
        }
    }
}
```

### 2. Open Source Project
```python
metadata = {
    "version": "1.0",
    "collaboration_details": {
        "industry": ["technology"],
        "stage": "growth"
    },
    "integrations": {
        "github": {
            "enabled": true,
            "repo_url": "https://github.com/project/repo"
        }
    }
}
```

### 3. Research Collaboration
```python
metadata = {
    "version": "1.0",
    "collaboration_details": {
        "industry": ["healthcare", "AI"],
        "stage": "ideation"
    },
    "resources": {
        "documents": [
            {
                "name": "Research Paper Draft",
                "type": "research",
                "url": "https://..."
            }
        ]
    }
}
```

## API Usage

### Creating a Collaboration with Metadata
```python
POST /api/social/collaborations/
{
    "name": "AI Healthcare Startup",
    "description": "Building AI solutions for healthcare",
    "project_type": "startup",
    "metadata": {
        "version": "1.0",
        "collaboration_details": {
            "industry": ["healthcare", "AI"],
            "stage": "ideation"
        }
    }
}
```

### Updating Metadata
```python
PATCH /api/social/collaborations/{id}/
{
    "metadata": {
        "version": "1.0",
        "progress_tracking": {
            "kpis": [
                {
                    "name": "Beta Users",
                    "target": 100,
                    "current": 25
                }
            ]
        }
    }
}
```

## Frontend Display

The frontend should intelligently display metadata based on:
1. Collaboration type (project_type field)
2. Available metadata fields
3. User permissions

Example display priority:
- **All Types**: Show progress, team size, recent activity
- **Startup**: Show funding status, stage, KPIs
- **Research**: Show documents, publications, milestones
- **Hackathon**: Show deadline, team members, tech stack

## Best Practices

1. **Keep it Clean**: Only store relevant data
2. **Regular Updates**: Update timestamps when metadata changes
3. **Validation**: Validate metadata structure before saving
4. **Privacy**: Don't store sensitive information (passwords, keys)
5. **Performance**: Keep metadata size reasonable (<1MB)
6. **Backward Compatibility**: Handle missing fields gracefully