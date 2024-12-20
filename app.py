from flask import Flask, request, jsonify
import re
import json
import time
from scraper import get_tiktok_info, clean_tiktok_url

app = Flask(__name__)

@app.route('/extract', methods=['GET'])
def extract():
    # Get the URL parameter
    profile_url = request.args.get('url')
    if not profile_url:
        return jsonify({"error": "Please provide a 'url' parameter"}), 400

    # Clean the URL
    cleaned_url = clean_tiktok_url(profile_url)

    # Get the info
    data = get_tiktok_info(cleaned_url)

    # Return the data as JSON
    return jsonify(data), 200

if __name__ == '__main__':
    # For testing locally (not in production)
    app.run(host='0.0.0.0', port=8000)