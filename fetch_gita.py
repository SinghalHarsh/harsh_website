import requests
import json
import os

def fetch_gita_data():
    print("Fetching verses...")
    # Fetch Verses (Sanskrit)
    verses_url = "https://raw.githubusercontent.com/gita/gita/main/data/verse.json"
    verses_resp = requests.get(verses_url)
    verses_data = verses_resp.json()
    
    print("Fetching translations...")
    # Fetch Translations
    trans_url = "https://raw.githubusercontent.com/gita/gita/main/data/translation.json"
    trans_resp = requests.get(trans_url)
    trans_data = trans_resp.json()
    
    # Process Data
    # Create a lookup for translations
    # We need Hindi (let's pick a common author) and English
    # Looking at the repo, usually:
    # English: Swami Sivananda (author_id might vary, we'll check)
    # Hindi: Swami Ramsukhdas (author_id might vary)
    
    # Let's organize translations by verse_id
    translations_map = {}
    
    for t in trans_data:
        v_id = t.get('verse_id') or t.get('verseNumber') # Check key structure
        if not v_id: continue
        
        if v_id not in translations_map:
            translations_map[v_id] = {'hindi': '', 'english': ''}
            
        lang = t.get('lang')
        # Simple heuristic: take the first english and first hindi found
        # Ideally we filter by author, but let's see what we get
        if lang == 'english' and not translations_map[v_id]['english']:
            translations_map[v_id]['english'] = t.get('description')
        elif lang == 'hindi' and not translations_map[v_id]['hindi']:
            translations_map[v_id]['hindi'] = t.get('description')

    final_verses = []
    
    for v in verses_data:
        # verse.json structure usually: { "chapter_id": 1, "verse_id": 1, "text": "..." }
        # or { "chapter_number": 1, "verse_number": 1, "text": "..." }
        
        # Let's handle potential key variations
        chapter = v.get('chapter_id') or v.get('chapter_number')
        verse_num = v.get('verse_id') or v.get('verse_number')
        text = v.get('text') or v.get('sanskrit')
        
        # Construct a unique ID to match translations if needed, 
        # but the translation.json usually uses a global verse_id (1 to 700) or composite.
        # Let's assume the 'id' field in verse.json matches 'verse_id' in translation.json
        global_id = v.get('id')
        
        trans = translations_map.get(global_id, {'hindi': '', 'english': ''})
        
        final_verses.append({
            "chapter": chapter,
            "verse": verse_num,
            "sanskrit": text,
            "hindi": trans['hindi'],
            "english": trans['english']
        })
        
    # Sort by chapter and verse
    final_verses.sort(key=lambda x: (x['chapter'], x['verse']))
    
    with open('gita_full.json', 'w', encoding='utf-8') as f:
        json.dump(final_verses, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(final_verses)} verses to gita_full.json")

if __name__ == "__main__":
    fetch_gita_data()
