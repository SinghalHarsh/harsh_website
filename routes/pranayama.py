from flask import Blueprint, render_template

pranayama_bp = Blueprint('pranayama', __name__)

@pranayama_bp.route('/pranayama')
def pranayama():
    return render_template('pranayama.html')
