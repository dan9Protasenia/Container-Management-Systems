import docker

from src.app.api.container.service import ContainerService

client = docker.from_env()

container_service = ContainerService()

import itertools


class LoadBalancer:
    def __init__(self):
        self.container_cycle = None

    def update_containers(self, containers):
        self.container_cycle = itertools.cycle(containers)

    def get_next_container(self):
        return next(self.container_cycle)


load_balancer = LoadBalancer()


class ScaleService:

    def scale_container(self, container_id: str, scale_target: int):
        container = client.containers.get(container_id)
        image_name = container.attrs["Config"]["Image"]
        current_containers = container_service.get_containers_by_image(image_name)
        current_count = len(current_containers)

        if current_count < scale_target:
            self.start_new_containers(image_name, scale_target - current_count)
        elif current_count > scale_target:
            self.stop_excess_containers(current_containers, current_count - scale_target)

        return {"container_id": container_id, "scaled_to": scale_target}

    @staticmethod
    def start_new_containers(image_name: str, count: int):
        for _ in range(count):
            client.containers.run(image_name, detach=True)

    @staticmethod
    def stop_excess_containers(containers: list, count: int):
        for container in containers[:count]:
            container.stop()
            container.remove()

    @staticmethod
    def balance_load():
        active_containers = [container.id for container in client.containers.list()]
        load_balancer.update_containers(active_containers)

        next_container_id = load_balancer.get_next_container()
        return next_container_id
