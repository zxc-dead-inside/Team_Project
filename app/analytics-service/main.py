from time import sleep
from src.services.kafka.producer import KafkaProducer
from src.services.kafka.consumer import KafkaConsumer

print('Producer initing')
producer = KafkaProducer(
    bootstrap_servers=['localhost:9094', 'localhost:9095', 'localhost:9096'],
    topic='topic',
    buffer_memory=1048576
)
print('Producer inited')

print('Sending message')
producer.send(
    value='my message from python2',
    key='python-message2',
)
print('Message was sent')
sleep(1)

print('Consumer initing')
consumer = KafkaConsumer(
    topic='topic',
    bootstrap_servers=['localhost:9094'],
    auto_offset_reset='earliest',
    group_id='echo-messages-to-stdout',
)
print('Consumer inited')


for message in consumer:
    print(message.value)
