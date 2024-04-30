import os

from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator

from src.app.api.balancer.service import LoadBalancer
from src.app.api.container.service import start_health_check_loop

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

from src.app.startup import create_app

app = create_app()
Instrumentator().instrument(app).expose(app)
load_balancer = LoadBalancer()

@app.on_event("startup")
async def startup_event():
    load_balancer.start()
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
    start_health_check_loop()
