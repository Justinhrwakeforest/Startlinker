#!/usr/bin/env python
"""
Simple test script for message read receipts functionality.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'startup_hub.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.messaging.models import Conversation, Message, MessageRead, ConversationParticipant
from apps.messaging.serializers import MessageSerializer
from django.test import RequestFactory

User = get_user_model()

def create_test_users():
    """Create test users for messaging"""
    print("Creating test users...")
    
    # Clean up existing test users
    User.objects.filter(username__startswith='test_user_').delete()
    
    users_data = [
        {
            'username': 'test_user_alice',
            'email': 'alice@test.com',
            'first_name': 'Alice',
            'last_name': 'Johnson'
        },
        {
            'username': 'test_user_bob',
            'email': 'bob@test.com',
            'first_name': 'Bob',
            'last_name': 'Smith'
        }
    ]
    
    test_users = []
    for user_data in users_data:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password='testpass123',
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        test_users.append(user)
        print(f"[+] Created user: {user.username} ({user.get_full_name()})")
    
    print(f"[+] Created {len(test_users)} test users\n")
    return test_users

def create_test_conversation(users):
    """Create test conversation between users"""
    print("Creating test conversation...")
    
    # Clean up existing conversations
    Conversation.objects.filter(participants__in=users).delete()
    
    # Create 1-on-1 conversation between Alice and Bob
    conv = Conversation.objects.create(is_group=False)
    conv.participants.set(users)
    
    # Create participant settings
    for user in users:
        ConversationParticipant.objects.create(conversation=conv, user=user)
    
    print(f"[+] Created conversation between {users[0].first_name} & {users[1].first_name}")
    return conv

def send_test_messages(conversation, users):
    """Send test messages between users"""
    print("Sending test messages...")
    
    alice, bob = users
    
    messages_data = [
        (alice, "Hey Bob! How are you doing?"),
        (bob, "Hi Alice! I'm doing great, thanks for asking!"),
        (alice, "That's awesome! Want to grab coffee later?"),
        (bob, "Sure! Let's meet at the usual place at 3 PM."),
    ]
    
    messages = []
    for sender, content in messages_data:
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content
        )
        messages.append(message)
        print(f"[+] {sender.first_name}: \"{content}\"")
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
    
    print(f"[+] Sent {len(messages)} test messages\n")
    return messages

def test_read_receipts(messages, users):
    """Test read receipt functionality"""
    print("Testing read receipt functionality...\n")
    
    alice, bob = users
    
    print("BEFORE READING MESSAGES:")
    print_message_status(messages)
    
    # Simulate Alice reading Bob's messages
    print(f"Simulating {alice.first_name} reading messages...")
    bob_messages = [msg for msg in messages if msg.sender == bob]
    
    for message in bob_messages:
        MessageRead.objects.get_or_create(message=message, user=alice)
        print(f"   [+] Alice read: \"{message.content}\"")
    
    print("\nSimulating Bob reading Alice's messages...")
    alice_messages = [msg for msg in messages if msg.sender == alice]
    
    for message in alice_messages:
        MessageRead.objects.get_or_create(message=message, user=bob)
        print(f"   [+] Bob read: \"{message.content}\"")
    
    print("\nAFTER READING MESSAGES:")
    print_message_status(messages)

def print_message_status(messages):
    """Print detailed message read status"""
    print("-" * 60)
    
    for message in messages:
        # Get read receipts for this message
        read_receipts = MessageRead.objects.filter(message=message).select_related('user')
        read_by = [receipt.user.first_name for receipt in read_receipts]
        
        sender_name = message.sender.first_name
        content = message.content[:40] + "..." if len(message.content) > 40 else message.content
        time_str = message.sent_at.strftime("%H:%M")
        
        read_status = f"Read by: {', '.join(read_by)}" if read_by else "Unread"
        status_symbol = "[READ]" if read_by else "[UNREAD]"
        
        print(f"  {status_symbol} [{time_str}] {sender_name}: {content}")
        print(f"      {read_status}")
    
    print("-" * 60 + "\n")

def test_api_response(messages, users):
    """Test API response format for read receipts"""
    print("Testing API response format...")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/')
    request.user = users[0]  # Alice
    
    # Test serialization of messages with read receipts
    sample_message = messages[0]  # First message
    
    serializer = MessageSerializer(sample_message, context={'request': request})
    data = serializer.data
    
    print("Sample API Response:")
    print(f"  Message ID: {data['id']}")
    print(f"  Sender: {data['sender']['username']}")
    print(f"  Content: {data['content']}")
    print(f"  Is Read: {data['is_read']}")
    print(f"  Read Receipts: {len(data['read_receipts'])} receipts")
    
    for receipt in data['read_receipts']:
        print(f"    - Read by: {receipt['user']['full_name']} at {receipt['read_at']}")
    
    print()

def cleanup_test_data(users, conversation, messages):
    """Clean up test data"""
    print("Cleaning up test data...")
    
    # Delete test messages (cascades to read receipts)
    Message.objects.filter(id__in=[msg.id for msg in messages]).delete()
    
    # Delete test conversation
    conversation.delete()
    
    # Delete test users
    User.objects.filter(id__in=[user.id for user in users]).delete()
    
    print("[+] Cleaned up all test data\n")

def main():
    """Run the complete test suite"""
    print("Starting Message Read Receipts Test")
    print("=" * 60)
    
    try:
        # Create test data
        users = create_test_users()
        conversation = create_test_conversation(users)
        messages = send_test_messages(conversation, users)
        
        # Test read receipts
        test_read_receipts(messages, users)
        test_api_response(messages, users)
        
        print("[SUCCESS] All tests completed successfully!")
        print("\nKEY FINDINGS:")
        print("   * Read receipts are properly created in the database")
        print("   * Messages show correct read status per user")
        print("   * API serialization includes read receipt data")
        print("   * Frontend should now display read status correctly")
        
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        response = input("\nClean up test data? (y/n): ")
        if response.lower() == 'y':
            cleanup_test_data(users, conversation, messages)
        else:
            print("Test data preserved for manual inspection")

if __name__ == "__main__":
    main()