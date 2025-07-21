"""Simple tagging system for conversation states."""

# Tag Definitions
TAGS = {
    'good-path': {
        'emoji': '✅', 
        'color': 'GREEN', 
        'desc': 'This branch worked well',
        'key': 'g'
    },
    'bad-path': {
        'emoji': '❌', 
        'color': 'RED', 
        'desc': 'This branch didn\'t work out',
        'key': 'b'
    },
    'branch-point': {
        'emoji': '⚡', 
        'color': 'YELLOW', 
        'desc': 'Good place to try alternatives',
        'key': 'x'
    }
}

def assign_tag(state, tag):
    """Assign a tag to a state."""
    if tag not in TAGS:
        return False
    
    if 'tags' not in state:
        state['tags'] = []
    
    if tag not in state['tags']:
        state['tags'].append(tag)
    
    return True

def remove_tag(state, tag):
    """Remove a tag from a state."""
    if 'tags' not in state or tag not in state['tags']:
        return False
    
    state['tags'].remove(tag)
    return True

def get_tag_display(tag):
    """Get display string for a tag (emoji)."""
    if tag in TAGS:
        return TAGS[tag]['emoji']
    return ''

def get_tag_color(tag):
    """Get color for a tag."""
    if tag in TAGS:
        return TAGS[tag]['color']
    return 'WHITE'

def filter_states_by_tags(states, tags):
    """Filter states that have any of the specified tags."""
    if not tags:
        return states
    
    filtered = []
    for state in states:
        state_tags = state.get('tags', [])
        if any(tag in state_tags for tag in tags):
            filtered.append(state)
    
    return filtered

def get_tagged_states(tree, tag):
    """Get all states with a specific tag."""
    tagged_states = []
    for state in tree.states.values():
        if tag in state.get('tags', []):
            tagged_states.append(state)
    
    return tagged_states

def parse_quick_tag(key):
    """Parse quick tag key to tag name."""
    for tag_name, tag_info in TAGS.items():
        if tag_info['key'] == key.lower():
            return tag_name
    return None

def get_all_tags():
    """Get all available tags."""
    return list(TAGS.keys())

def get_tag_help():
    """Get help text for tagging."""
    help_lines = []
    for tag_name, tag_info in TAGS.items():
        help_lines.append(f"  [{tag_info['key']}] {tag_info['emoji']} {tag_name} - {tag_info['desc']}")
    return '\n'.join(help_lines)