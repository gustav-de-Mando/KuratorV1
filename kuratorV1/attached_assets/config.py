import os

# Bot configuration
PREFIX = os.getenv('BOT_PREFIX', '!')

# Command cooldowns (in seconds)
COOLDOWNS = {
    'ping': 5,
    'clear': 10,
    'serverinfo': 30,
    'userinfo': 30
}

# Permission levels
PERMISSION_LEVELS = {
    'ADMIN': 4,
    'MODERATOR': 3,
    'MEMBER': 1,
    'GUEST': 0
}
