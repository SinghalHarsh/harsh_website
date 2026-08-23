from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from bson.objectid import ObjectId
from app.extensions import db

books_bp = Blueprint('books', __name__)

@books_bp.route('/books')
def books():
    all_books = list(db.books.find())

    currently_reading = [b for b in all_books if b.get('status') == 'reading']
    # Anything not explicitly reading or completed sits on the to-read shelf, so
    # legacy documents without a status stay visible instead of vanishing.
    to_read = [b for b in all_books if b.get('status') not in ('reading', 'completed')]

    current_year = datetime.now().year
    completed_books = []
    for b in all_books:
        if b.get('status') != 'completed':
            continue
        # Fall back to created_at so a completion without a recorded date is
        # still shown rather than silently dropped from every shelf.
        stamp = b.get('completed_date') or b.get('created_at')
        if isinstance(stamp, datetime):
            stamp = stamp.strftime('%Y-%m-%d')
        if stamp and str(stamp).startswith(str(current_year)):
            completed_books.append(b)

    completed_books.sort(key=lambda b: str(b.get('completed_date') or ''), reverse=True)

    return render_template('pages/books.html',
                           now=datetime.now(),
                           currently_reading=currently_reading,
                           to_read=to_read,
                           completed_books=completed_books)

@books_bp.route('/books/add', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    status = request.form.get('status', 'to_read') # Default to 'to_read'
    
    total_pages_str = request.form.get('total_pages')
    total_pages = int(total_pages_str) if total_pages_str and total_pages_str.strip() else 0

    if title:
        db.books.insert_one({
            'title': title,
            'author': author,
            'status': status,
            'created_at': datetime.now(),
            'current_page': 0,
            'total_pages': total_pages
        })
    return redirect(url_for('books.books'))

@books_bp.route('/books/update_status', methods=['POST'])
def update_book_status():
    book_id = request.form.get('book_id')
    new_status = request.form.get('status')
    total_pages_str = request.form.get('total_pages')
    
    update_data = {'status': new_status}
    if new_status == 'completed':
        update_data['completed_date'] = datetime.now().strftime('%Y-%m-%d')
    
    if total_pages_str and total_pages_str.strip():
        try:
            update_data['total_pages'] = int(total_pages_str)
        except ValueError:
            pass
        
    db.books.update_one({'_id': ObjectId(book_id)}, {'$set': update_data})
    return redirect(url_for('books.books'))

@books_bp.route('/books/update_progress', methods=['POST'])
def update_book_progress():
    book_id = request.form.get('book_id')
    current_page = int(request.form.get('current_page', 0))
    total_pages_str = request.form.get('total_pages')
    
    update_data = {'current_page': current_page}
    
    if total_pages_str and total_pages_str.strip():
        try:
            total_pages = int(total_pages_str)
            if total_pages > 0:
                update_data['total_pages'] = total_pages
        except ValueError:
            pass
        
    db.books.update_one({'_id': ObjectId(book_id)}, {'$set': update_data})
    return redirect(url_for('books.books'))

@books_bp.route('/books/delete', methods=['POST'])
def delete_book():
    book_id = request.form.get('book_id')
    db.books.delete_one({'_id': ObjectId(book_id)})
    return redirect(url_for('books.books'))
