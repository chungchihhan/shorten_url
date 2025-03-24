import random
import re
import string
from datetime import datetime, timedelta

from flask import Flask, jsonify, redirect, request

app = Flask(__name__)

url_mapping = {}

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# API 1: Create Short URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()

    if not data or 'original_url' not in data:
        return jsonify({'success': False, 'reason': 'Missing URL'}), 400

    original_url = data['original_url']

    if len(original_url) > 2048:
        return jsonify({'success': False, 'reason': 'URL too long'}), 400

    if not is_valid_url(original_url):
        return jsonify({'success': False, 'reason': 'Invalid URL'}), 400

    short_url = generate_short_url(original_url)
    expiration_date = (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

    url_mapping[short_url] = {
        'original_url': original_url,
        'expiration_date': expiration_date
    }

    return jsonify({
        'short_url': short_url,
        'expiration_date': expiration_date,
        'success': True,
        'reason': ''
    })

# API 2: Redirect Using Short URL
@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    if short_url not in url_mapping:
        return jsonify({'success': False, 'reason': 'Short URL not found'}), 404

    original_url = url_mapping[short_url]['original_url']
    expiration_date = datetime.strptime(url_mapping[short_url]['expiration_date'], '%Y-%m-%d %H:%M:%S')

    if datetime.utcnow() > expiration_date:
        return jsonify({'success': False, 'reason': 'Short URL expired'}), 410

    return redirect(original_url)

def generate_short_url(original_url):
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choices(characters, k=6)) # 6 characters random string
    while short_url in url_mapping:
        short_url = ''.join(random.choices(characters, k=6))
    return short_url

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)