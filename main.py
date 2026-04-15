from flask import Flask, request, jsonify
import cloudscraper
import os
import json

app = Flask(__name__)

# Environment variables
REAL_API_URL = os.environ.get('REAL_API_URL')
API_KEY = os.environ.get('API_KEY')

@app.route('/', methods=['GET', 'POST'])
def clone_api():
    # Handle both GET and POST
    if request.method == 'GET':
        key = request.args.get('key')
        vnums = request.args.get('vnums')
    else:
        data = request.get_json()
        key = data.get('key') if data else None
        vnums = data.get('vnums') if data else None
    
    # Validate API key
    if not key:
        return jsonify({
            "status": False,
            "error": "Missing 'key' parameter. Use: ?key=mykey&vnums=KA20AA7421"
        }), 400
    
    if key != API_KEY:
        return jsonify({
            "status": False,
            "error": "Invalid API key"
        }), 401
    
    # Validate vehicle number
    if not vnums:
        return jsonify({
            "status": False,
            "error": "Missing 'vnums' parameter. Use: ?key=mykey&vnums=KA20AA7421"
        }), 400
    
    try:
        # Create cloudscraper instance
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'desktop': False
            }
        )
        
        # Call real API
        response = scraper.get(
            REAL_API_URL,
            params={"vehicle": vnums.upper()},
            timeout=30
        )
        
        # Check if response is empty
        if not response.text:
            return jsonify({
                "status": False,
                "error": "Empty response from real API",
                "vehicle": vnums
            }), 502
        
        # Try to parse JSON
        try:
            data = response.json()
            return jsonify(data), response.status_code
        except json.JSONDecodeError as e:
            # Return raw response for debugging
            return jsonify({
                "status": False,
                "error": "Invalid JSON from real API",
                "details": str(e),
                "raw_response": response.text[:500]  # First 500 chars
            }), 502
        
    except cloudscraper.exceptions.CloudflareChallengeError as e:
        return jsonify({
            "status": False,
            "error": "Cloudflare challenge failed. Try again.",
            "details": str(e)
        }), 503
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": "Failed to fetch vehicle data",
            "details": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "API is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)