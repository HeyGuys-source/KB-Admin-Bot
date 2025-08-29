#!/usr/bin/env python3
"""
Flask-based keep-alive server for Discord bot.
Provides web interface for monitoring bot status and handles ping requests.
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request
from utils.logger import setup_logger

# Setup logging
logger = setup_logger('keep_alive')

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "advanced-discord-bot-secret-key")

# Global bot status storage
bot_status = {
    'online': False,
    'last_ping': None,
    'latency': 0,
    'guilds': 0,
    'users': 0,
    'uptime': 0,
    'stats': {},
    'start_time': datetime.now(timezone.utc).isoformat()
}

def update_bot_status(status_data):
    """Update global bot status."""
    global bot_status
    bot_status.update(status_data)
    bot_status['last_ping'] = datetime.now(timezone.utc).isoformat()
    logger.debug(f"Bot status updated: {status_data}")

@app.route('/')
def status_page():
    """Main status page showing bot health and statistics."""
    try:
        # Calculate uptime
        if bot_status.get('last_ping'):
            last_ping = datetime.fromisoformat(bot_status['last_ping'].replace('Z', '+00:00'))
            time_since_ping = (datetime.now(timezone.utc) - last_ping).total_seconds()
            is_online = time_since_ping < 60  # Consider offline if no ping for 60 seconds
        else:
            is_online = False
            time_since_ping = 0
            
        status_info = {
            'online': is_online,
            'bot_status': bot_status,
            'time_since_ping': int(time_since_ping),
            'server_time': datetime.now(timezone.utc).isoformat()
        }
        
        return render_template('status.html', status=status_info)
        
    except Exception as e:
        logger.error(f"Error rendering status page: {e}")
        return f"Error: {e}", 500

@app.route('/ping')
def ping():
    """Ping endpoint for external monitoring."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'bot_online': bot_status.get('online', False)
    })

@app.route('/api/status')
def api_status():
    """API endpoint returning detailed bot status."""
    return jsonify(bot_status)

@app.route('/api/ping', methods=['POST'])
def api_ping():
    """API endpoint for bot to report its status."""
    try:
        data = request.get_json()
        if data:
            update_bot_status(data)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    except Exception as e:
        logger.error(f"Error in API ping endpoint: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime': int((datetime.now(timezone.utc) - 
                      datetime.fromisoformat(bot_status['start_time'])).total_seconds())
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('status.html', 
                         status={'error': 'Page not found'}, 
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template('status.html', 
                         status={'error': 'Internal server error'}, 
                         error_code=500), 500

if __name__ == '__main__':
    logger.info("Starting Flask keep-alive server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
