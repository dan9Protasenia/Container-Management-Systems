import asyncio
import datetime

from docker.errors import APIError

from src.app.api.container.service import ContainerService, ContainerInfoService
from src.app.core.schemas.container import ContainerCreate


class ScaleService:
    def __init__(self, client):
        self.client = client
        self.container_service = ContainerService(client)
        self.container_info_service = ContainerInfoService(client)

    async def scale_up(self, request: ContainerCreate):
        print("Масштабирование вверх")
        await self.container_service.create_container(request)

    async def scale_down(self):
        current_containers = self.container_info_service.list_active_containers()

        if len(current_containers) <= self.container_service.initial_containers_count:
            return

        containers_to_remove = []

        for container in current_containers:
            docker_container = self.client.containers.get(container.id)
            created_at_str = docker_container.attrs["Created"]
            created_at = datetime.datetime.strptime(created_at_str[:-4], "%Y-%m-%dT%H:%M:%S.%f").replace(
                tzinfo=datetime.timezone.utc
            )
            print(f"Контейнер {docker_container.short_id}: время создания {created_at}")

            container_label_value = docker_container.attrs["Config"]["Labels"].get("scale-purpose", None)

            if container_label_value == "scale-up":
                print(f"Контейнер {docker_container.short_id} помечен для удаления.")
                containers_to_remove.append(docker_container)

            else:
                print(f"Контейнер {docker_container.short_id} не подходит для удаления.")

        for docker_container in containers_to_remove:
            try:
                await asyncio.get_running_loop().run_in_executor(None, lambda: docker_container.remove(force=True))
                print(f"Контейнер {docker_container.short_id} успешно удален.")
            except APIError as e:
                print(f"Ошибка при удалении контейнера {docker_container.short_id}: {e}")

        self.container_service.update_containers_list()

    def scale_container(self, container_id: str, scale_target: int):
        container = self.client.containers.get(container_id)
        image_name = container.attrs["Config"]["Image"]
        current_containers = self.container_info_service.get_containers_by_image(image_name)
        current_count = len(current_containers)

        if current_count < scale_target:
            self.start_new_containers(image_name, scale_target - current_count)

        elif current_count > scale_target:
            self.stop_excess_containers(current_containers, current_count - scale_target)

        return {"container_id": container_id, "scaled_to": scale_target}

    def start_new_containers(self, image_name: str, count: int):
        for _ in range(count):
            self.client.containers.run(image_name, detach=True)

    @staticmethod
    def stop_excess_containers(containers: list, count: int):
        for container in containers[:count]:
            container.stop()
            container.remove()
