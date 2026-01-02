from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from database import db
from bson.objectid import ObjectId

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if content or title:
            db.notes.insert_one({
                'title': title,
                'content': content,
                'created_at': datetime.now()
            })
        return redirect(url_for('notes.notes'))

    all_notes = list(db.notes.find().sort('created_at', -1))
    return render_template('notes.html', notes=all_notes)

@notes_bp.route('/notes/delete/<note_id>', methods=['POST'])
def delete_note(note_id):
    db.notes.delete_one({'_id': ObjectId(note_id)})
    return redirect(url_for('notes.notes'))
