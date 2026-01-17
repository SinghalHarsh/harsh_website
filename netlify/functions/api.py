import sys
import os
import awsgi

# Add the root directory to sys.path to allow importing app
# This assumes this file is in netlify/functions/
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) 
# Actually, let's differ calculating root dir.
# file is at /netlify/functions/api.py.
# root is ../../
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.insert(0, root_dir)

from app import app

def handler(event, context):
    return awsgi.response(app, event, context)
