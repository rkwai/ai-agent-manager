import uvicorn
from src.api.routes import app
from src.config.settings import API_HOST, API_PORT

def main():
    uvicorn.run(
        "src.api.routes:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        workers=1
    )

if __name__ == "__main__":
    main() 