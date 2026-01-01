import json
import urllib.request
from collections import Counter

def fetch_json(url):
    print(f"Downloading {url}...")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())

def main():
    # URLs for the raw data
    verse_url = "https://raw.githubusercontent.com/gita/gita/main/data/verse.json"
    translation_url = "https://raw.githubusercontent.com/gita/gita/main/data/translation.json"

    try:
        verses_data = fetch_json(verse_url)
        translations_data = fetch_json(translation_url)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    print(f"Loaded {len(verses_data)} verses and {len(translations_data)} translations.")

    # Analyze authors to pick the best ones
    hindi_authors = Counter()
    english_authors = Counter()

    for t in translations_data:
        if t['lang'] == 'hindi':
            hindi_authors[t['authorName']] += 1
        elif t['lang'] == 'english':
            english_authors[t['authorName']] += 1

    print("\nAvailable Hindi Authors:", dict(hindi_authors))
    print("Available English Authors:", dict(english_authors))

    # Select authors (Preferring standard ones, or falling back to most frequent)
    preferred_hindi = "Swami Ramsukhdas"
    preferred_english = "Swami Sivananda"

    selected_hindi_author = preferred_hindi if preferred_hindi in hindi_authors else hindi_authors.most_common(1)[0][0]
    selected_english_author = preferred_english if preferred_english in english_authors else english_authors.most_common(1)[0][0]

    print(f"\nSelected Hindi Author: {selected_hindi_author}")
    print(f"Selected English Author: {selected_english_author}")

    # Create a lookup for translations
    # Map: verse_number (global id) -> lang -> translation text
    translation_map = {}

    for t in translations_data:
        v_num = t['verseNumber'] # This corresponds to the global 'id' in verse.json
        author = t['authorName']
        lang = t['lang']
        
        if v_num not in translation_map:
            translation_map[v_num] = {}
        
        if lang == 'hindi' and author == selected_hindi_author:
            translation_map[v_num]['hindi'] = t['description']
        elif lang == 'english' and author == selected_english_author:
            translation_map[v_num]['english'] = t['description']

    # Merge into final dataset
    final_dataset = []

    # Sort verses by id to ensure order
    sorted_verses = sorted(verses_data, key=lambda x: x['id'])

    for verse in sorted_verses:
        v_id = verse['id']
        
        # Get translations
        trans = translation_map.get(v_id, {})
        
        verse_obj = {
            "chapter": verse['chapter_number'],
            "verse": verse['verse_number'],
            "sanskrit": verse['text'],
            "hindi": trans.get('hindi', ""),
            "english": trans.get('english', "")
        }
        final_dataset.append(verse_obj)

    # Save to file
    output_file = "gita_dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully created {output_file} with {len(final_dataset)} verses.")

if __name__ == "__main__":
    main()
