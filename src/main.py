import uvicorn
from fastapi import FastAPI
from multiprocessing import Process
from src.web.app import app as flask_app
from fastapi.middleware.cors import CORSMiddleware
from flask_cors import CORS
from src.api.routes import router  # Import router instead of app

# Create the FastAPI application
app = FastAPI(title="AI Agent Management System")

# Update the CORS configuration for FastAPI
origins = [
    "http://localhost:8000",
    "http://localhost:8080",
]

# Add router with /api prefix
app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS to Flask app
CORS(flask_app, resources={
    r"/*": {
        "origins": origins,
        "methods": ["OPTIONS", "GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

def main():
    # Create processes for both apps
    fastapi_process = Process(target=run_fastapi)
    flask_process = Process(target=run_flask)

    try:
        # Start both processes
        fastapi_process.start()
        flask_process.start()

        # Wait for both processes to complete
        fastapi_process.join()
        flask_process.join()
    except KeyboardInterrupt:
        print("Shutting down servers...")
        fastapi_process.terminate()
        flask_process.terminate()

if __name__ == '__main__':
    main() 