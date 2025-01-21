import time
from etl.etl_process import etl_pipeline

def main():
    """Основной цикл для выполнения ETL.
    Честно я пытался реализовать это на celery расписании, но
    у меня не получилось, как я понял это cerlery в Docker на Windows не дружит с кодировками
    поэтому юзаю простой цикл
    """
    while True:
        etl_pipeline()
        time.sleep(60)

if __name__ == "__main__":
    main()
