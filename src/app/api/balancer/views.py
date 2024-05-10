import docker

from src.app.api.balancer.service import LoadBalancer

client = docker.from_env()
load_service = LoadBalancer(client)


async def proxy_request(path: str):
    return await load_service.proxy_request(path)
