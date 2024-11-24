from flask import Flask, render_template, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# FastAPI backend URL
BACKEND_URL = "http://localhost:8000"

@app.route('/')
def home():
    return render_template('index.html')

# Proxy all API requests to the FastAPI backend
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_backend(path):
    # Forward the request to the FastAPI backend
    resp = requests.request(
        method=request.method,
        url=f"{BACKEND_URL}/api/{path}",
        headers={key: value for key, value in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    # Return the response from the backend
    return resp.content, resp.status_code, resp.headers.items()

if __name__ == '__main__':
    app.run(debug=True, port=8080) 