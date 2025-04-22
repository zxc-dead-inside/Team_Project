from kafka import KafkaConsumer as _KafkaConsumer

class KafkaConsumer(_KafkaConsumer):
    def __init__(self, topic, **configs):
        super().__init__(topic, **configs)
        self.topic = topic
