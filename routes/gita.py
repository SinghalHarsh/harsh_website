from flask import Blueprint, render_template, request, jsonify, current_app
import random
import json
import os
import re
from database import db

gita_bp = Blueprint('gita', __name__)

CHAPTER_TITLES = {
    1: "Arjuna Visada Yoga (The Yoga of Arjuna's Dejection)",
    2: "Sankhya Yoga (The Yoga of Knowledge)",
    3: "Karma Yoga (The Yoga of Action)",
    4: "Jnana Karma Sanyasa Yoga (The Yoga of Knowledge and Renunciation)",
    5: "Karma Sanyasa Yoga (The Yoga of Renunciation of Action)",
    6: "Dhyana Yoga (The Yoga of Meditation)",
    7: "Jnana Vijnana Yoga (The Yoga of Knowledge and Wisdom)",
    8: "Akshara Brahma Yoga (The Yoga of the Imperishable Brahman)",
    9: "Raja Vidya Raja Guhya Yoga (The Yoga of Sovereign Science and Secret)",
    10: "Vibhuti Yoga (The Yoga of Divine Glories)",
    11: "Visvarupa Darsana Yoga (The Yoga of the Vision of the Universal Form)",
    12: "Bhakti Yoga (The Yoga of Devotion)",
    13: "Kshetra Kshetragya Vibhaga Yoga (The Field and the Knower)",
    14: "Gunatraya Vibhaga Yoga (The Division of the Three Gunas)",
    15: "Purushottama Yoga (The Yoga of the Supreme Person)",
    16: "Daivasura Sampad Vibhaga Yoga (The Divine and Demoniacal Properties)",
    17: "Sraddhatraya Vibhaga Yoga (The Division of the Threefold Faith)",
    18: "Moksha Sanyasa Yoga (The Yoga of Liberation by Renunciation)"
}

def load_all_verses():
    try:
        file_path = os.path.join(current_app.root_path, 'gita_full.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading verses: {e}")
        return []

def clean_text(text, is_sanskrit=False):
    if not text:
        return ""
    # Remove non-breaking spaces
    text = text.replace('\u00a0', ' ')
    
    # Remove verse numbers like "18.4" or "।।18.4।।" or "||18.4||"
    text = re.sub(r'[।|]*\d+\.\d+[।|]*', '', text)
    
    # Replace newlines with spaces to merge padas
    text = text.replace('\n', ' ')
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    if is_sanskrit:
        # Add newline after 'uvacha' (speaker marker)
        text = re.sub(r'(उवाच)', r'\1\n', text)
        
        # Add newline after dandas
        text = re.sub(r'([।॥]+)', r'\1\n', text)
        
        # Ensure it ends with double danda if it doesn't have one
        text = text.strip()
        if text and not text.endswith('॥') and not text.endswith('||'):
            text += '॥'
    else:
        # For Hindi/English, just ensure basic cleanup
        # We might want to keep newlines if they are paragraph breaks, 
        # but usually translations are single paragraphs.
        # Let's keep the logic simple for now.
        pass
            
    return text.strip()

@gita_bp.route('/gita')
def gita_jar():
    verses = load_all_verses()
    total_verses = len(verses)
    return render_template('gita.html', total_verses=total_verses)

@gita_bp.route('/api/gita/random')
def gita_random():
    verses = load_all_verses()
    
    if verses:
        verse = random.choice(verses)
        # Add chapter title
        verse['chapter_title'] = CHAPTER_TITLES.get(verse['chapter'], f"Chapter {verse['chapter']}")
        
        # Clean text
        verse['sanskrit'] = clean_text(verse.get('sanskrit', ''), is_sanskrit=True)
        verse['hindi'] = clean_text(verse.get('hindi', ''))
        verse['english'] = clean_text(verse.get('english', ''))
        
        return jsonify(verse)
    return jsonify({"error": "No verses found"}), 404
