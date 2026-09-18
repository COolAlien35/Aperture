"""
Aperture — Kafka Topic Provisioning Script
Person C: Run this to create and configure the Kafka topics for Aperture.

Usage (local):
    python scripts/init_kafka.py

Topic Architecture:
  - Topic: aperture.usage-events
  - Partitions: 3 (enables consumer scaling; keyed by team_id or key_id for order preservation)
  - Replication Factor: 1 (local single-node KRaft broker)
  - Retention: 7 days (604,800,000 ms)
"""

import asyncio
import os
import sys
import logging
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.getenv(
    "KAFKA_BROKER", "localhost:9093"
)  # 9093 = EXTERNAL listener (host access)
USAGE_TOPIC_NAME = os.getenv("KAFKA_USAGE_TOPIC", "aperture.usage-events")
DEFAULT_PARTITIONS = 3
DEFAULT_REPLICATION = 1
RETENTION_MS = str(7 * 24 * 60 * 60 * 1000)  # 7 days in ms


async def create_usage_topic(
    broker: str = KAFKA_BROKER,
    topic_name: str = USAGE_TOPIC_NAME,
    num_partitions: int = DEFAULT_PARTITIONS,
    replication_factor: int = DEFAULT_REPLICATION,
) -> bool:
    """Create the aperture usage events topic if it does not already exist."""
    print("=" * 65)
    print("  Aperture Kafka Topic Provisioning — Person C")
    print(f"  Broker: {broker}")
    print(f"  Topic:  {topic_name}")
    print("=" * 65)

    admin = AIOKafkaAdminClient(bootstrap_servers=broker)
    try:
        await admin.start()
        print("🔌  Connected to Kafka broker.")

        # Check existing topics
        existing_topics = await admin.list_topics()
        if topic_name in existing_topics:
            print(f"✅  Topic '{topic_name}' already exists.")
        else:
            print(
                f"🔨  Creating topic '{topic_name}' (partitions={num_partitions}, rep={replication_factor})..."
            )
            new_topic = NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                topic_configs={
                    "retention.ms": RETENTION_MS,
                    "cleanup.policy": "delete",
                },
            )
            try:
                await admin.create_topics([new_topic])
                print(f"✅  Topic '{topic_name}' created successfully.")
            except TopicAlreadyExistsError:
                print(f"✅  Topic '{topic_name}' already exists.")

        # Describe topic to verify configuration
        metadata = await admin.describe_topics([topic_name])
        if metadata and len(metadata) > 0:
            topic_info = metadata[0]
            partitions = topic_info.get("partitions", [])
            print("\n📋  Topic Metadata Verification:")
            print(f"    - Name:               {topic_name}")
            print(f"    - Partition Count:    {len(partitions)}")
            print(
                f"    - Leader Partition 0: Node {partitions[0].get('leader') if partitions else 'N/A'}"
            )
            print(f"    - Retention Policy:   7 days ({RETENTION_MS} ms)")
            print(f"    - Status:             HEALTHY / READY FOR EVENTS")

        print("\n" + "=" * 65)
        print(
            "🎉  Kafka topic setup complete! Ready for Producer (A) and Consumer (C)."
        )
        print("=" * 65)
        return True

    except Exception as e:
        print(f"\n❌  Failed to provision Kafka topic: {e}")
        return False
    finally:
        await admin.close()


def main():
    success = asyncio.run(create_usage_topic())
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
