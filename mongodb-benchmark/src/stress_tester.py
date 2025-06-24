import time
import random
import multiprocessing
import logging
import time
from typing import Dict, List, Any

from tqdm import tqdm

from db_clients.base_client import DBClient, PerformanceResult
from config import settings


logger = logging.getLogger(__name__)


class ProgressDisplay:
    """Класс для управления отображением прогресса"""
    def __init__(self, num_processes: int, total_requests: int):
        self.num_processes = num_processes
        self.total_requests = total_requests
        self.bars = []
        self.last_update = time.time()
        
    def start(self):
        """Инициализация прогресс-баров"""
        for i in range(self.num_processes):
            self.bars.append(tqdm(
                total=self.total_requests,
                desc=f"Worker {i}",
                position=i,
                colour=random.choice(settings.colors),
                leave=False,
                bar_format="{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
                mininterval=0.5
            ))
    
    def update(self, worker_id: int, progress: int):
        """Обновление прогресса для конкретного воркера"""
        if worker_id < len(self.bars):
            self.bars[worker_id].n = progress
            self.bars[worker_id].refresh()
    
    def finish(self):
        """Завершение отображения прогресса"""
        for bar in self.bars:
            bar.close()


class StressTester:
    """Класс для проведения тестирования"""
    def __init__(self, db_client_class, db_config: Dict[str, Any]):
        self.db_client_class = db_client_class
        self.db_config = db_config
    
    def run_tests(
        self, 
        processes: int, 
        requests_per_process: int,
        load_type: str = "mixed"
    ) -> Dict[str, List[PerformanceResult]]:
        """Запускает тесты"""

        logger.info(f"Starting stress tests: {processes} processes, {requests_per_process} requests per process")
        
        test_operations = [
            "test_insert_review",
            "test_get_reviews",
            "test_add_rating",
            "test_get_ratings_summary",
            "test_add_bookmark",
            "test_get_user_bookmarks",
            "test_complex_query",
            "test_top_movies_by_comments",
            "test_top_helpful_reviews",
            "test_top_users_by_comments"
        ]
        
        manager = multiprocessing.Manager()
        results_queue = manager.Queue()
        stats_dict = manager.dict()
        lock = manager.Lock()
        
        for operation in test_operations:
            stats_dict[operation] = [0.0, 0]

        progress_bars = manager.list([0] * processes)
        progress_display = ProgressDisplay(processes, requests_per_process)
        progress_display.start()

        workers = []
        
        for i in range(processes):
            w = multiprocessing.Process(
                target=self._worker_process,
                args=(i, test_operations, requests_per_process, 
                     load_type, results_queue, stats_dict, lock, progress_bars)
            )
            w.start()
            workers.append(w)
        
        try:
            while any(w.is_alive() for w in workers):
                for i in range(processes):
                    progress_display.update(i, progress_bars[i])
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.warning("Test interrupted by user")
            for w in workers:
                w.terminate()

        for i in range(processes):
            progress_display.update(i, progress_bars[i])
        progress_display.finish()


        for w in workers:
            w.join()

        detailed_results = []
        while not results_queue.empty():
            detailed_results.append(results_queue.get())
        
        aggregated_results = {}
        for operation, (total_time, count) in stats_dict.items():
            avg_time = total_time / count if count > 0 else 0
            aggregated_results[operation] = {
                "total_requests": count,
                "avg_time_ms": avg_time,
                "total_time_sec": total_time / 1000
            }
        
        return {
            "aggregated": aggregated_results,
            "detailed": detailed_results
        }
  
    def _worker_process(
        self,
        worker_id: int,
        test_operations: List[str],
        requests_count: int,
        load_type: str,
        results_queue: multiprocessing.Queue,
        stats_dict: Dict[str, List[float]],
        lock: multiprocessing.Lock ,
        progress_bars
    ):
        """Создание процессов."""
        try:
            client = self.db_client_class(self.db_config)
            client.connect()
            client.load_ids_cache()  # Загрузка ID
            operation_weights = settings.operation_weights.model_dump()
            completed = 0
            if load_type == "mixed":
                for _ in range(requests_count):
                    operation = random.choices(
                        test_operations,
                        weights=[operation_weights[op] for op in test_operations],
                        k=1
                    )[0]
                    self._execute_operation(
                        worker_id, client, operation, results_queue, stats_dict, lock
                    )
                    completed += 1
                    progress_bars[worker_id] = completed
            else:
                for operation in test_operations:
                    for _ in range(requests_count):
                        self._execute_operation(
                            worker_id, client, operation, results_queue, stats_dict, lock
                        )
                        completed += 1
                        progress_bars[worker_id] = completed
            
            client.disconnect()
        except Exception as e:
            logger.error(f"Worker {worker_id} failed: {e}")
            progress_bars[worker_id] = requests_count
    
    def _execute_operation(
        self,
        worker_id: int,
        client: DBClient,
        operation: str,
        results_queue: multiprocessing.Queue,
        stats_dict: Dict[str, List[float]],
        lock: multiprocessing.Lock
    ):
        """Выполнение запросов."""
        try:
            start_time = time.perf_counter()
            records_processed = getattr(client, operation)()
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            with lock:
                if operation in stats_dict:
                    total_time, count = stats_dict[operation]
                    stats_dict[operation] = [total_time + duration_ms, count + 1]
                else:
                    logger.warning(f"Operation {operation} not found in stats_dict")
            
            result = PerformanceResult(
                operation=operation,
                execution_time_ms=duration_ms,
                records_processed=records_processed
            )
            results_queue.put(result)
        except Exception as e:
            logger.error(f"Operation {operation} failed in worker {worker_id}: {e}")