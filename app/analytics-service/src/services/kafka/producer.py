from aiokafka import AIOKafkaProducer


class KafkaProducer(AIOKafkaProducer):
    def __init__(self, bootstrap_servers):
        super().__init__(bootstrap_servers=bootstrap_servers)
