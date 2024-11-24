import uvicorn
from src.api.routes import app, initialize_app
from src.config.settings import API_HOST, API_PORT, DATABASE_URL

def main():
    # Initialize the application with database
    initialize_app(DATABASE_URL)
    
    # Run the server
    uvicorn.run(
        "src.api.routes:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        workers=1
    )

if __name__ == "__main__":
    main() 