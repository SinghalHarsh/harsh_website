from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta
from bson.objectid import ObjectId

from app.extensions import db

notes_bp = Blueprint('notes', __name__)

# Notes older than this can no longer be deleted from the UI.
DELETE_WINDOW_DAYS = 7


def _deletable(created_at):
    if not isinstance(created_at, datetime):
        return True
    return datetime.now() - created_at <= timedelta(days=DELETE_WINDOW_DAYS)


@notes_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            db.notes.insert_one({
                'content': content,
                'created_at': datetime.now(),
            })
        return redirect(url_for('notes.notes'))

    all_notes = list(db.notes.find().sort('created_at', -1))
    for note in all_notes:
        note['deletable'] = _deletable(note.get('created_at'))

    return render_template(
        'pages/notes.html',
        notes=all_notes,
        delete_window_days=DELETE_WINDOW_DAYS,
    )


@notes_bp.route('/notes/edit', methods=['POST'])
def edit_note():
    note_id = request.form.get('note_id')
    content = request.form.get('content', '').strip()

    if not note_id or not content:
        return jsonify({'error': 'Note id and content are required'}), 400

    db.notes.update_one(
        {'_id': ObjectId(note_id)},
        {'$set': {'content': content, 'updated_at': datetime.now()}},
    )
    return jsonify({'status': 'success', 'content': content})


@notes_bp.route('/notes/delete/<note_id>', methods=['POST'])
def delete_note(note_id):
    note = db.notes.find_one({'_id': ObjectId(note_id)})
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    if not _deletable(note.get('created_at')):
        return jsonify({
            'error': f'Notes can only be deleted within {DELETE_WINDOW_DAYS} days'
        }), 403

    db.notes.delete_one({'_id': ObjectId(note_id)})

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    return redirect(url_for('notes.notes'))
