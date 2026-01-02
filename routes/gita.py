from flask import Blueprint, render_template, request, jsonify
import random
from gita_data import gita_data
from database import db

gita_bp = Blueprint('gita', __name__)

@gita_bp.route('/gita')
def gita_jar():
    total_verses = sum(len(data['verses']) for data in gita_data.values())
    return render_template('gita.html', emotions=gita_data, total_verses=total_verses)

@gita_bp.route('/gita/verse/<emotion>')
def get_gita_verse(emotion):
    if emotion in gita_data:
        verses = gita_data[emotion]['verses']
        verse = random.choice(verses)
        return jsonify({'status': 'success', 'verse': verse, 'emotion': gita_data[emotion]['label']})
    return jsonify({'status': 'error', 'message': 'Emotion not found'}), 404

@gita_bp.route('/api/gita/random')
def gita_random():
    # Get a random verse from the DB
    pipeline = [{"$sample": {"size": 1}}]
    random_verse = list(db.gita_verses.aggregate(pipeline))
    if random_verse:
        verse = random_verse[0]
        verse['_id'] = str(verse['_id'])
        return jsonify(verse)
    return jsonify({"error": "No verses found"}), 404

@gita_bp.route('/api/gita/search')
def gita_search():
    chapter = request.args.get('chapter', type=int)
    verse_num = request.args.get('verse', type=int)
    
    if not chapter or not verse_num:
        return jsonify({"error": "Chapter and Verse number required"}), 400
        
    verse = db.gita_verses.find_one({"chapter": chapter, "verse": verse_num})
    if verse:
        verse['_id'] = str(verse['_id'])
        return jsonify(verse)
    return jsonify({"error": "Verse not found"}), 404

@gita_bp.route('/api/gita/chapters')
def gita_chapters():
    # Return structure: { 1: 47, 2: 72, ... } (chapter: max_verses)
    pipeline = [
        {"$group": {"_id": "$chapter", "count": {"$max": "$verse"}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(db.gita_verses.aggregate(pipeline))
    chapters = {r['_id']: r['count'] for r in results}
    return jsonify(chapters)
