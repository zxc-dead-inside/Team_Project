from aiokafka import AIOKafkaProducer


class KafkaProducer(AIOKafkaProducer):
    def __init__(self, bootstrap_servers):
        super().__init__(bootstrap_servers=bootstrap_servers)
    
    async def healthcheck(self):
        if not self.client or not self.client._conns:
            return {'status': False, 'detail':'Kafka producer is not ready'}
        if not self.client.cluster.brokers():
            return {'status': False, 'detail':'No brokers available'}
        return {'status': True, 'detail':''}
