from flask import Flask, render_template, request
from flask_socketio import SocketIO
#import eventlet

# Configure eventlet for concurrent connections
#eventlet.monkey_patch()

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Initialize content list
content = []

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html', content=content)

@app.route('/submit', methods=['POST'])
def submit():
    """Handle POST requests to add content."""
    message_type = request.form.get('type', 'user')  # Default to 'user' if type is not provided
    new_content = request.form.get('content', '')
    if new_content:
        content.append({'type': message_type, 'content': new_content})
        # Notify clients of new content
        socketio.emit('update_content', {'content': content})
    return "Content added", 200


def start_server():
    socketio.run(app, host='localhost', port=6969)
