from typing import Any, Dict

import docker

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
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})
        cpu_usage_stats = cpu_stats.get("cpu_usage", {})

        cpu_usage_total = cpu_usage_stats.get("total_usage", 0)
        system_cpu_usage = cpu_stats.get("system_cpu_usage", 0)
        precpu_usage_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        pre_system_cpu_usage = precpu_stats.get("system_cpu_usage", 0)

        cpu_delta = cpu_usage_total - precpu_usage_total
        system_cpu_delta = system_cpu_usage - pre_system_cpu_usage

        number_cpus = len(cpu_usage_stats.get("percpu_usage", [0]))

        cpu_percentage = 0.0
        if cpu_delta > 0 and system_cpu_delta > 0:
            cpu_percentage = (cpu_delta / system_cpu_delta) * number_cpus * 100.0

        memory_stats = stats.get("memory_stats", {})
        memory_usage = memory_stats.get("usage", 0)
        memory_limit = memory_stats.get("limit", 0)
        memory_percentage = (memory_usage / memory_limit) * 100.0 if memory_limit else 0

        networks = stats.get("networks", {})
        network_data = next(iter(networks.values()), {})
        network_rx = network_data.get("rx_bytes", 0)
        network_tx = network_data.get("tx_bytes", 0)

        blk_read, blk_write = 0, 0
        for blk_stat in stats.get("blkio_stats", {}).get("io_service_bytes_recursive", []):
            if blk_stat["op"] == "Read":
                blk_read += blk_stat.get("value", 0)
            elif blk_stat["op"] == "Write":
                blk_write += blk_stat.get("value", 0)

        num_procs = stats.get("pids_stats", {}).get("current", 0)

        formatted_stats = {
            "cpu_usage": f"{cpu_usage_total / 1e9:.2f} GHz",
            "cpu_percentage": f"{cpu_percentage:.2f}%",
            "memory_usage": f"{memory_usage / 1e6:.2f} MB",
            "memory_percentage": f"{memory_percentage:.2f}%",
            "network_rx": f"{network_rx / 1e6:.2f} MB",
            "network_tx": f"{network_tx / 1e6:.2f} MB",
            "block_read": f"{blk_read / 1e6:.2f} MB",
            "block_write": f"{blk_write / 1e6:.2f} MB",
            "num_procs": num_procs,
        }

        return formatted_stats
