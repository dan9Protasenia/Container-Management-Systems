import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

# from src.app.config import MainConfig
from src.app.startup import create_app

# config = MainConfig()
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
