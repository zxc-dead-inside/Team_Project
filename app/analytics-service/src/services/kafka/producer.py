from kafka import KafkaProducer as _KafkaProducer

class KafkaProducer(_KafkaProducer):
    def __init__(self, topic: str, **configs):
        super().__init__(**configs)
        self.topic = topic
    
    def send(self, key: str, value: str) -> None:
        super().send(
            topic=self.topic,
            value=value.encode(),
            key=key.encode()
        )