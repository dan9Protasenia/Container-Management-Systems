import docker
from typing import Dict, Any

client = docker.from_env()


class MetricsService:
    @staticmethod
    def get_container_stats(container_id: str) -> Dict[str, Any]:
        print(f"Получение статистики для ID контейнера: {container_id}")
        container = client.containers.get(container_id)
        stats = container.stats(stream=False)

        return dict(stats)

    @staticmethod
    def analyze_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
        cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
        # memory_usage = stats['memory_stats']['usage']
        formatted_stats = {
            "cpu_usage": f"{cpu_usage / 1e9:.2f}%",
            # "memory_usage": f"{memory_usage / 1e6:.2f} MB",
            # "network": {
            #     "input": f"{net_input / 1e6:.2f} MB",
            #     "output": f"{net_output / 1e6:.2f} MB"
            # },
        }

        return formatted_stats
