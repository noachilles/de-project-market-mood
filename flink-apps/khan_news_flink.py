from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
import json

def process(record):
    data = json.loads(record)
    data["processed"] = True
    return json.dumps(data, ensure_ascii=False)

def main():
    env = StreamExecutionEnvironment.get_execution_environment()

    props = {
        "bootstrap.servers": "kafka:9092",
        "group.id": "pyflink-khan-group",
        "key.deserializer": "org.apache.kafka.common.serialization.StringDeserializer",
        "value.deserializer": "org.apache.kafka.common.serialization.StringDeserializer",
        "auto.offset.reset": "earliest"
    }

    consumer = FlinkKafkaConsumer(
        topics="khan-news",
        deserialization_schema=SimpleStringSchema(),
        properties=props
    )

    producer = FlinkKafkaProducer(
        topic="processed-khan-news",
        serialization_schema=SimpleStringSchema(),
        producer_config={"bootstrap.servers": "kafka:9092"}
    )

    stream = env.add_source(consumer)
    processed = stream.map(process, output_type=Types.STRING())

    processed.add_sink(producer)

    env.execute("PyFlink - Khan News Processor")

if __name__ == "__main__":
    main()
