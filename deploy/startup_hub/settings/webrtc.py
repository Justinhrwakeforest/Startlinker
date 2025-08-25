# WebRTC Configuration
import os

# STUN/TURN server configuration
WEBRTC_CONFIG = {
    'iceServers': [
        # Google's public STUN servers
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        {'urls': 'stun:stun2.l.google.com:19302'},
        {'urls': 'stun:stun3.l.google.com:19302'},
        {'urls': 'stun:stun4.l.google.com:19302'},
        
        # Additional public STUN servers for redundancy
        {'urls': 'stun:stun.services.mozilla.com'},
        {'urls': 'stun:stun.stunprotocol.org:3478'},
        
        # TURN servers for NAT traversal (you can use free services or set up your own)
        # Example using a free TURN server (replace with your own in production)
        {
            'urls': 'turn:openrelay.metered.ca:80',
            'username': 'openrelayproject',
            'credential': 'openrelayproject',
        },
        {
            'urls': 'turn:openrelay.metered.ca:443',
            'username': 'openrelayproject',
            'credential': 'openrelayproject',
        },
        {
            'urls': 'turn:openrelay.metered.ca:443?transport=tcp',
            'username': 'openrelayproject',
            'credential': 'openrelayproject',
        },
    ],
    
    # ICE configuration
    'iceTransportPolicy': 'all',  # Use both STUN and TURN
    'iceCandidatePoolSize': 10,   # Pre-gather ICE candidates
    
    # Additional WebRTC constraints
    'bundlePolicy': 'max-bundle',
    'rtcpMuxPolicy': 'require',
}

# You can also use environment variables for production TURN servers
if os.environ.get('TURN_SERVER_URL'):
    WEBRTC_CONFIG['iceServers'].append({
        'urls': os.environ.get('TURN_SERVER_URL'),
        'username': os.environ.get('TURN_USERNAME'),
        'credential': os.environ.get('TURN_PASSWORD'),
    })

# Media constraints for better quality
WEBRTC_MEDIA_CONSTRAINTS = {
    'video': {
        'width': {'min': 640, 'ideal': 1280, 'max': 1920},
        'height': {'min': 480, 'ideal': 720, 'max': 1080},
        'frameRate': {'ideal': 30, 'max': 60},
        'facingMode': 'user',  # Use front camera by default
    },
    'audio': {
        'echoCancellation': True,
        'noiseSuppression': True,
        'autoGainControl': True,
        'sampleRate': 48000,
        'channelCount': 2,
    }
}