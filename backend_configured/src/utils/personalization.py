"""
Personalization utilities for story generation
Handles vocabulary levels, cultural context, and language integration
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

def get_vocabulary_guidelines(reading_level: str) -> Dict[str, str]:
    """
    Get vocabulary guidelines based on reading level
    """
    guidelines = {
        'simple': {
            'description': 'Use basic words, short sentences (5-10 words), common vocabulary',
            'sentence_length': 'Keep sentences short and simple',
            'vocabulary': 'Use everyday words that children know',
            'complexity': 'Avoid complex grammar structures'
        },
        'medium': {
            'description': 'Use moderate vocabulary, varied sentence structure (8-15 words)',
            'sentence_length': 'Mix short and medium sentences',
            'vocabulary': 'Include some new words with context clues',
            'complexity': 'Use moderate complexity with clear connections'
        },
        'advanced': {
            'description': 'Use rich vocabulary, complex sentences (10-20 words), descriptive language',
            'sentence_length': 'Use varied sentence lengths for rhythm',
            'vocabulary': 'Include challenging vocabulary with definitions',
            'complexity': 'Use complex grammar and literary devices'
        }
    }
    
    return guidelines.get(reading_level.lower(), guidelines['medium'])

def get_cultural_context(region: str, location: str) -> Dict[str, Any]:
    """
    Get cultural elements for a specific region and location
    """
    # Basic cultural mapping - can be expanded
    cultural_contexts = {
        'maharashtra': {
            'festivals': ['Ganesh Chaturthi', 'Gudi Padwa', 'Navratri'],
            'foods': ['Vada Pav', 'Puran Poli', 'Modak'],
            'landmarks': ['Gateway of India', 'Shivaji Park', 'Elephanta Caves'],
            'traditions': ['Govinda celebration', 'Dhol Tasha', 'Warli art'],
            'greetings': ['Namaskar', 'Kay challay'],
            'values': ['respect for elders', 'community spirit', 'education']
        },
        'rajasthan': {
            'festivals': ['Teej', 'Desert Festival', 'Kite Festival'],
            'foods': ['Dal Baati Churma', 'Ghevar', 'Laal Maas'],
            'landmarks': ['Hawa Mahal', 'City Palace', 'Thar Desert'],
            'traditions': ['Folk music', 'Puppet shows', 'Camel rides'],
            'greetings': ['Ram Ram', 'Khamma Ghani'],
            'values': ['hospitality', 'bravery', 'tradition']
        },
        'punjab': {
            'festivals': ['Baisakhi', 'Lohri', 'Karva Chauth'],
            'foods': ['Makki ki Roti', 'Sarson ka Saag', 'Lassi'],
            'landmarks': ['Golden Temple', 'Wagah Border', 'Anandpur Sahib'],
            'traditions': ['Bhangra', 'Giddha', 'Langar'],
            'greetings': ['Sat Sri Akal', 'Waheguru'],
            'values': ['sharing', 'strength', 'devotion']
        }
    }
    
    # Default context if region not found
    default_context = {
        'festivals': ['local celebrations'],
        'foods': ['traditional dishes'],
        'landmarks': ['local monuments'],
        'traditions': ['cultural practices'],
        'greetings': ['local greetings'],
        'values': ['community values']
    }
    
    region_key = region.lower() if region else 'default'
    context = cultural_contexts.get(region_key, default_context)
    
    # Add location-specific elements if provided
    if location:
        context['setting_details'] = [f"Set in {location}, showcasing local atmosphere and community"]
    
    return context

def get_mother_tongue_words(mother_tongue: str, category: str = 'general') -> List[Dict[str, str]]:
    """
    Get appropriate mother tongue words to integrate into stories
    Returns list of {word, meaning, context} dictionaries
    """
    word_collections = {
        'hindi': {
            'general': [
                {'word': 'दोस्त', 'meaning': 'friend', 'context': 'when talking about friendship'},
                {'word': 'माँ', 'meaning': 'mother', 'context': 'when referring to mother'},
                {'word': 'खुशी', 'meaning': 'happiness', 'context': 'when expressing joy'},
                {'word': 'सुंदर', 'meaning': 'beautiful', 'context': 'when describing something beautiful'},
                {'word': 'साहस', 'meaning': 'courage', 'context': 'when showing bravery'},
                {'word': 'प्यार', 'meaning': 'love', 'context': 'when expressing affection'},
                {'word': 'मदद', 'meaning': 'help', 'context': 'when asking for or giving help'},
                {'word': 'सपना', 'meaning': 'dream', 'context': 'when talking about dreams or aspirations'}
            ],
            'adventure': [
                {'word': 'रोमांच', 'meaning': 'adventure', 'context': 'during exciting moments'},
                {'word': 'जंगल', 'meaning': 'forest', 'context': 'when in forest settings'},
                {'word': 'खजाना', 'meaning': 'treasure', 'context': 'when discovering something valuable'},
                {'word': 'राह', 'meaning': 'path/way', 'context': 'when choosing directions'}
            ],
            'family': [
                {'word': 'दादी', 'meaning': 'grandmother', 'context': 'when talking about grandmother'},
                {'word': 'भाई', 'meaning': 'brother', 'context': 'when referring to brother'},
                {'word': 'बहन', 'meaning': 'sister', 'context': 'when referring to sister'},
                {'word': 'घर', 'meaning': 'home', 'context': 'when talking about home'}
            ]
        },
        'marathi': {
            'general': [
                {'word': 'मित्र', 'meaning': 'friend', 'context': 'when talking about friendship'},
                {'word': 'आई', 'meaning': 'mother', 'context': 'when referring to mother'},
                {'word': 'आनंद', 'meaning': 'joy', 'context': 'when expressing happiness'},
                {'word': 'सुंदर', 'meaning': 'beautiful', 'context': 'when describing beauty'}
            ]
        },
        'punjabi': {
            'general': [
                {'word': 'यार', 'meaning': 'friend', 'context': 'when talking about friendship'},
                {'word': 'माँ', 'meaning': 'mother', 'context': 'when referring to mother'},
                {'word': 'खुशी', 'meaning': 'happiness', 'context': 'when expressing joy'},
                {'word': 'वाह', 'meaning': 'wow/great', 'context': 'when expressing amazement'}
            ]
        }
    }
    
    language_key = mother_tongue.lower() if mother_tongue else 'hindi'
    category_key = category.lower()
    
    # Get words from specified category, fallback to general
    words = word_collections.get(language_key, {}).get(category_key, 
             word_collections.get(language_key, {}).get('general', 
             word_collections['hindi']['general']))
    
    return words[:8]  # Return up to 8 words for natural integration

def format_companions_for_story(companions: List[Dict[str, Any]]) -> str:
    """
    Format companion list for story integration
    """
    if not companions:
        return "no specific companions mentioned"
    
    companion_descriptions = []
    for comp in companions:
        name = comp.get('name', 'Friend')
        comp_type = comp.get('type', 'friend')
        description = comp.get('description', f'a wonderful {comp_type}')
        
        companion_descriptions.append(f"{name} ({description})")
    
    if len(companion_descriptions) == 1:
        return companion_descriptions[0]
    elif len(companion_descriptions) == 2:
        return f"{companion_descriptions[0]} and {companion_descriptions[1]}"
    else:
        return f"{', '.join(companion_descriptions[:-1])}, and {companion_descriptions[-1]}"

def get_age_appropriate_themes(age: int) -> List[str]:
    """
    Get age-appropriate themes and story elements
    """
    if age <= 5:
        return ['friendship', 'sharing', 'kindness', 'family', 'animals', 'colors', 'shapes']
    elif age <= 8:
        return ['adventure', 'courage', 'helping others', 'learning', 'discovery', 'magic', 'problem-solving']
    elif age <= 12:
        return ['responsibility', 'teamwork', 'perseverance', 'identity', 'challenges', 'growth', 'leadership']
    else:
        return ['self-discovery', 'relationships', 'choices', 'future', 'values', 'independence', 'purpose']

def get_reading_time_estimate(word_count: int, reading_level: str, age: int) -> int:
    """
    Estimate reading time based on word count, reading level, and age
    """
    # Words per minute by age and reading level
    wpm_rates = {
        'simple': {5: 20, 6: 30, 7: 40, 8: 50, 9: 60, 10: 70},
        'medium': {6: 25, 7: 35, 8: 45, 9: 55, 10: 65, 11: 75, 12: 85},
        'advanced': {8: 40, 9: 50, 10: 60, 11: 70, 12: 80, 13: 90, 14: 100}
    }
    
    # Get appropriate WPM rate
    level_rates = wpm_rates.get(reading_level, wpm_rates['medium'])
    wpm = level_rates.get(age, 60)  # Default to 60 WPM
    
    # Calculate reading time in minutes
    reading_time = max(1, round(word_count / wpm))
    return reading_time

def validate_personalization_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean personalization parameters
    """
    cleaned_params = {}
    
    # Required fields with defaults
    cleaned_params['child_name'] = params.get('child_name') or 'Hero'
    cleaned_params['child_age'] = max(3, min(18, params.get('child_age', 8)))
    cleaned_params['child_gender'] = params.get('child_gender', 'neutral').lower()
    
    # Ensure valid gender options
    if cleaned_params['child_gender'] not in ['he', 'she', 'they', 'neutral']:
        cleaned_params['child_gender'] = 'neutral'
    
    # Clean interests list
    interests = params.get('interests', [])
    cleaned_params['interests'] = [interest.strip() for interest in interests if interest.strip()]
    
    # Validate reading level
    reading_level = params.get('reading_level', 'medium').lower()
    cleaned_params['reading_level'] = reading_level if reading_level in ['simple', 'medium', 'advanced'] else 'medium'
    
    # Validate language
    language = params.get('language_of_story', 'english').lower()
    cleaned_params['language_of_story'] = language if language in ['english', 'hindi'] else 'english'
    
    # Clean optional fields
    cleaned_params['location'] = params.get('location', '').strip()
    cleaned_params['region'] = params.get('region', '').strip()
    cleaned_params['mother_tongue'] = params.get('mother_tongue', '').strip()
    cleaned_params['companions'] = params.get('companions', [])
    
    return cleaned_params

def create_personalization_prompt_context(params: Dict[str, Any]) -> str:
    """
    Create a rich context string for prompts based on personalization parameters
    """
    context_parts = []
    
    # Child details
    if params.get('child_name'):
        context_parts.append(f"The story features {params['child_name']} as the main character")
    
    # Interests
    if params.get('interests'):
        interests_str = ', '.join(params['interests'])
        context_parts.append(f"Story environment should reflect these interests: {interests_str}")
    
    # Cultural context
    if params.get('location') and params.get('region'):
        context_parts.append(f"Set in {params['location']}, {params['region']} with authentic cultural elements")
    
    # Language considerations
    if params.get('mother_tongue'):
        context_parts.append(f"Include appropriate {params['mother_tongue']} words naturally")
    
    # Companions
    if params.get('companions'):
        companion_str = format_companions_for_story(params['companions'])
        context_parts.append(f"Include these companions: {companion_str}")
    
    return '. '.join(context_parts) + '.' if context_parts else 'Standard story personalization.'
