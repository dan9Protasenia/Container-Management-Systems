from src.app.api.balancer.service import LoadBalancer

load_service = LoadBalancer()


async def proxy_request(path: str):
    return await load_service.proxy_request(path)
