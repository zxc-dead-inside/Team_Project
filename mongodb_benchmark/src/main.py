import argparse
import json
import logging
import multiprocessing
import time
from datetime import datetime
from pathlib import Path

from config import settings
from db_clients.mongo_client import MongoClientWrapper
from db_clients.postgres_client import PostgresClient
from logger import setup_logging
from stress_tester import StressTester

setup_logging()


def get_args():
    parser = argparse.ArgumentParser(description="Database Performance Tester")
    parser.add_argument("-d", "--database", choices=["postgres", "mongo"], 
                        required=True, help="Database type to test")
    parser.add_argument("-r", "--records", type=int, default=10000000,
                        help="Total records to generate (default: 10,000,000)")
    parser.add_argument("-p", "--processes", type=int, default=4,
                        help="Number of processes (default: 4)")
    parser.add_argument("-n", "--requests", type=int, default=1000,
                        help="Requests per process (default: 1000)")
    parser.add_argument("-t", "--type", choices=["mixed", "sequential"],
                        default="mixed", help="Load type of benchmark")

    return parser.parse_args()

def main(
        db_type: str, total_records: int, processes: int, requests: int,
        load_type: str
    ):
    # Выбор конфигурации и класса клиента
    if db_type == "postgres":
        db_config =  settings.postgres_config.model_dump()
        db_client_class = PostgresClient
    elif db_type == "mongo":
        db_config = settings.mongo_config.model_dump()
        db_client_class = MongoClientWrapper
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
    
    logging.info(f"Starting test for {db_type.upper()} with {total_records} records")
    
    # Создаем и подключаем клиент для генерации данных
    db_client = db_client_class(db_config)
    db_client.connect()
    logging.info("Clean up all data.")
    db_client.cleanup()
    logging.info("Initialize schema")
    db_client.initialize_schema()

    
    # Генерируем тестовые данные
    logging.info(f"Generating test data ({total_records} records)...")
    start_data_gen = time.time()
    db_client.generate_test_data(total_records)
    data_gen_time = time.time() - start_data_gen
    logging.info(f"Data generation completed in {data_gen_time:.2f} seconds")
    
    # Закрываем соединение после генерации данных
    db_client.disconnect()
    
    # Создаем тестер с КЛАССОМ клиента и конфигурацией
    tester = StressTester(db_client_class, db_config)
    
    # Запускаем тестирование
    logging.info("Starting stress tests...")
    start_test = time.time()
    test_results = tester.run_tests(
        processes=processes,
        requests_per_process=requests,
        load_type=load_type
    )
    test_time = time.time() - start_test
    logging.info(f"Stress tests completed in {test_time:.2f} seconds")
    
    # Отключаемся от БД
    db_client.disconnect()
    
    # Сохраняем результаты
    Path("results").mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/results_{db_type}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump({
            "db_type": db_type,
            "total_records": total_records,
            "processes": processes,
            "requests_per_process": requests,
            "data_generation_time": data_gen_time,
            "test_time": test_time,
            "load_type": load_type,
            "results": test_results,
        }, f, indent=2, default=str)
    
    logging.info(f"Results saved to {filename}")
    
    # Выводим сводку результатов
    print("\nTest Summary:")
    print(f"Database: {db_type.upper()}")
    print(f"Total records: {total_records}")
    print(f"Processes: {processes}")
    print(f"Requests per process: {requests}")
    print(f"Total requests: {processes * requests}")
    print(f"Data generation time: {data_gen_time:.2f} sec")
    print(f"Test execution time: {test_time:.2f} sec")
    print(f"Load type: {load_type}")
    
    print("\nOperation Performance (avg ms per request):")
    for op, metrics in test_results['aggregated'].items():
        print(f"  {op}: {metrics['avg_time_ms']:.2f} ms")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
   
    args = get_args()

    main(
        db_type=args.database,
        total_records=args.records,
        processes=args.processes,
        requests=args.requests,
        load_type=args.type
    )