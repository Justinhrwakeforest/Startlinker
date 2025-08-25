# apps/users/profanity_filter.py
"""
Profanity filter for usernames, first names, and last names.
Prevents offensive and vulgar words from being used in user registration.
"""

import re
from typing import List, Tuple, Optional

# Comprehensive list of offensive words to block
# This includes various forms and common substitutions
OFFENSIVE_WORDS = {
    # Racial slurs and discriminatory terms
    'nigga', 'nigger', 'negro', 'coon', 'spook', 'chink', 'gook', 'wetback', 
    'beaner', 'spic', 'kike', 'hymie', 'raghead', 'towelhead', 'camel jockey',
    'injun', 'redskin', 'squaw', 'wop', 'dago', 'guinea', 'mick', 'paddy',
    'limey', 'frog', 'kraut', 'hun', 'jap', 'nip', 'slope', 'zipperhead',
    
    # Sexual and vulgar terms
    'fuck', 'fucking', 'fucker', 'fucked', 'motherfucker', 'fuckface', 'fuckhead',
    'shit', 'shitty', 'shithead', 'bullshit', 'horseshit', 'batshit',
    'damn', 'damned', 'goddamn', 'goddamned',
    'bitch', 'bitchy', 'bitches', 'son of a bitch', 'sonofabitch',
    'asshole', 'ass', 'arse', 'arsehole', 'butthole', 'butt',
    'piss', 'pissed', 'pissing', 'piss off',
    'cunt', 'pussy', 'twat', 'snatch', 'beaver', 'muff',
    'cock', 'dick', 'penis', 'prick', 'dong', 'schlong',
    'balls', 'nuts', 'testicles', 'ballsack', 'nutsack',
    'tits', 'boobs', 'breasts', 'nipples', 'hooters', 'jugs',
    'whore', 'slut', 'skank', 'ho', 'hoe', 'tramp', 'hooker',
    'bastard', 'bastards', 'bitch', 'bitches',
    
    # Homophobic slurs
    'fag', 'faggot', 'faggy', 'homo', 'queer', 'dyke', 'lesbo',
    
    # Hate speech and extremist terms
    'hitler', 'nazi', 'kkk', 'ku klux klan', 'white power',
    'jihad', 'terrorist', 'bin laden', 'isis', 'al qaeda',
    
    # Drug-related offensive terms
    'crackhead', 'druggie', 'junkie', 'pothead', 'stoner',
    
    # Other offensive terms
    'retard', 'retarded', 'mongoloid', 'spastic', 'cripple', 'gimp',
    'fatty', 'fatso', 'pig', 'whale', 'cow',
    'ugly', 'hideous', 'disgusting', 'gross', 'nasty',
    'stupid', 'idiot', 'moron', 'imbecile', 'dumbass', 'dumb',
    'loser', 'freak', 'weirdo', 'psycho', 'crazy',
    
    # Common substitutions and variations
    'f*ck', 'f**k', 'fck', 'fuk', 'phuck', 'fack', 'fick', 'fock',
    'sh*t', 'sh**', 'sht', 'shyt', 'shiit', 'chit',
    'b*tch', 'b**ch', 'btch', 'biatch', 'beatch', 'beyotch',
    'a**hole', 'a**', 'azz', 'asz', 'a55', 'a$$',
    'd*ck', 'd**k', 'dik', 'dck', 'dyck', 'dik',
    'n*gga', 'n**ga', 'n1gga', 'n1gg4', 'n!gga', 'n!gg@',
    'p*ssy', 'p**sy', 'pu$$y', 'pus5y', 'puzzy',
    'c*nt', 'c**t', 'cvnt', 'cnut', 'c0nt', 'c#nt',
    
    # Leet speak and number substitutions
    'fuc|<', 'fvck', 'phuk', '5hit', '$hit', 'b1tch', 'b!tch', 'b@tch',
    'a55h0le', '@sshole', 'a$$h0le', 'd1ck', 'd!ck', 'd@ck', 'd|ck',
    'n1663r', 'n!663r', 'n166@', 'n!66@', 'n1gg@', 'n!gg@',
    'pu55y', 'pv55y', 'p00sy', 'pv$$y', 'p@ssy',
    'cvn7', 'cv|\|7', 'c\/|\|7', 'c|_||\|7',
    
    # Additional variations and creative spellings
    'fuuuck', 'fuuck', 'fuccck', 'shiiiit', 'shiit', 'shiiit',
    'biiiitch', 'biitch', 'biiitch', 'assshole', 'asshoole',
    'dickkk', 'diick', 'diiiick', 'pussyyy', 'pusssy',
    'cunnnt', 'cunnt', 'cuuunt', 'niggga', 'nigggga',
    
    # Terms that might be used to bypass filters - only the more explicit ones
    # Removed mild terms like 'crap', 'darn', 'heck' to avoid false positives
}

# Convert to lowercase and add common variations
OFFENSIVE_WORDS_LOWER = set()
for word in OFFENSIVE_WORDS:
    # Add original word
    OFFENSIVE_WORDS_LOWER.add(word.lower())
    
    # Add variations with different cases
    OFFENSIVE_WORDS_LOWER.add(word.upper())
    OFFENSIVE_WORDS_LOWER.add(word.capitalize())
    
    # Add variations with spaces removed
    no_space = word.replace(' ', '')
    if no_space != word:
        OFFENSIVE_WORDS_LOWER.add(no_space.lower())
        OFFENSIVE_WORDS_LOWER.add(no_space.upper())
        OFFENSIVE_WORDS_LOWER.add(no_space.capitalize())

# Patterns for detecting offensive content with character substitutions
SUBSTITUTION_PATTERNS = [
    # Common character substitutions
    (r'[0o]', 'o'),
    (r'[1l!|]', 'i'),
    (r'[3e]', 'e'),
    (r'[4@]', 'a'),
    (r'[5s$]', 's'),
    (r'[7t]', 't'),
    (r'[8b]', 'b'),
    (r'[9g]', 'g'),
    (r'[\+\-_\.\*\#\&\%\^\(\)]', ''),  # Remove special characters
    (r'\s+', ''),  # Remove spaces
]

def normalize_text(text: str) -> str:
    """
    Normalize text by applying common substitution patterns
    to detect creative spellings of offensive words.
    """
    if not text:
        return ""
    
    normalized = text.lower()
    
    # Apply substitution patterns
    for pattern, replacement in SUBSTITUTION_PATTERNS:
        normalized = re.sub(pattern, replacement, normalized)
    
    return normalized

def contains_offensive_word(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if text contains any offensive words.
    
    Args:
        text: The text to check
        
    Returns:
        Tuple of (is_offensive, matched_word)
    """
    if not text:
        return False, None
    
    # Check direct matches first (case-insensitive)
    text_lower = text.lower().strip()
    
    # Check for exact matches (the text is exactly an offensive word)
    if text_lower in OFFENSIVE_WORDS_LOWER:
        return True, text_lower
    
    # For usernames and longer texts, check if they contain offensive words as complete words
    # Split on common separators and check each part
    import re
    words = re.split(r'[\s\-_\.]+', text_lower)
    for word_part in words:
        if word_part in OFFENSIVE_WORDS_LOWER:
            return True, word_part
    
    # Check if text starts with an offensive word followed by numbers/letters
    # This catches cases like "fuck123", "shit456", etc.
    for offensive_word in OFFENSIVE_WORDS_LOWER:
        if len(offensive_word) >= 4:  # Only check longer words
            if text_lower.startswith(offensive_word.lower()):
                # Check if the rest is just numbers or simple suffixes
                remainder = text_lower[len(offensive_word):]
                if re.match(r'^[\d_\-\.]*$', remainder):
                    return True, offensive_word
    
    # Check for offensive words that appear as complete substrings with word boundaries
    # But be more selective to avoid false positives
    for offensive_word in OFFENSIVE_WORDS_LOWER:
        # Only check words that are at least 4 characters to avoid false positives
        if len(offensive_word) >= 4:
            # Use word boundary regex to match complete words
            pattern = r'\b' + re.escape(offensive_word) + r'\b'
            if re.search(pattern, text_lower):
                # Additional check: make sure it's not a common false positive
                # Skip if the offensive word is a substring of a common legitimate word
                if not _is_false_positive(text_lower, offensive_word):
                    return True, offensive_word
    
    # Check normalized version for creative spellings (only for longer offensive words)
    normalized = normalize_text(text)
    if normalized and len(normalized) >= 4:
        for word in OFFENSIVE_WORDS_LOWER:
            if len(word) >= 4:  # Only check longer offensive words
                normalized_word = normalize_text(word)
                if normalized_word and len(normalized_word) >= 4:
                    # Check if the normalized offensive word appears as a significant portion
                    if normalized_word in normalized and len(normalized_word) / len(normalized) > 0.7:
                        return True, word
    
    return False, None

def _is_false_positive(text: str, offensive_word: str) -> bool:
    """
    Check if the detected offensive word is likely a false positive.
    """
    # Common false positives to avoid
    false_positive_patterns = {
        'ass': ['class', 'pass', 'mass', 'grass', 'glass', 'assess', 'massachusetts', 'assume', 'classic'],
        'hell': ['hello', 'shell', 'spell', 'bell', 'well', 'tell', 'cell'],
        'damn': ['damn'],  # Keep this one as-is since it's actually offensive
    }
    
    if offensive_word in false_positive_patterns:
        for pattern in false_positive_patterns[offensive_word]:
            if pattern in text:
                return True
    
    return False

def is_valid_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a name (first name, last name, or username) is appropriate.
    
    Args:
        name: The name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return True, None
    
    # Check for offensive content
    is_offensive, matched_word = contains_offensive_word(name)
    if is_offensive:
        return False, f"The name '{name}' contains inappropriate content and cannot be used."
    
    # Additional checks for usernames
    # Check if it's trying to impersonate system accounts
    suspicious_patterns = [
        r'^admin\d*$',
        r'^mod\d*$', 
        r'^support\d*$',
        r'^staff\d*$',
        r'^system\d*$',
        r'^bot\d*$',
        r'^service\d*$',
    ]
    
    name_lower = name.lower()
    for pattern in suspicious_patterns:
        if re.match(pattern, name_lower):
            return False, f"The name '{name}' is not allowed as it may be confusing to other users."
    
    return True, None

def validate_user_input(username: str = None, first_name: str = None, last_name: str = None) -> List[str]:
    """
    Validate all user input fields for offensive content.
    
    Args:
        username: Username to validate
        first_name: First name to validate  
        last_name: Last name to validate
        
    Returns:
        List of error messages (empty if all valid)
    """
    errors = []
    
    if username:
        is_valid, error = is_valid_name(username)
        if not is_valid:
            errors.append(f"Username: {error}")
    
    if first_name:
        is_valid, error = is_valid_name(first_name)
        if not is_valid:
            errors.append(f"First name: {error}")
    
    if last_name:
        is_valid, error = is_valid_name(last_name)
        if not is_valid:
            errors.append(f"Last name: {error}")
    
    return errors

def get_clean_suggestion(original_name: str, field_type: str = "name") -> str:
    """
    Generate a clean alternative suggestion for an offensive name.
    
    Args:
        original_name: The original offensive name
        field_type: Type of field ('username', 'first_name', 'last_name')
        
    Returns:
        A clean alternative suggestion
    """
    if field_type == "username":
        suggestions = ["user", "member", "person", "individual"]
        import random
        import string
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"{random.choice(suggestions)}{random_suffix}"
    else:
        # For names, suggest they use their real name or a nickname
        return "Please use your real name or an appropriate nickname"