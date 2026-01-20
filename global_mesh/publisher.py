import redis
import json
import time
import yaml
import os
from datetime import datetime

# Load Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

class GlobalPublisher:
    def __init__(self):
        self.config = load_config()
        self.r = redis.Redis(
            host=self.config['redis']['host'],
            port=self.config['redis']['port'],
            password=self.config['redis']['password'],
            db=self.config['redis']['db'],
            socket_timeout=self.config['redis']['socket_timeout'],
            decode_responses=True
        )
        self.channel = self.config['channels']['alerts']
        self.location = self.config['node']['location']
        print(f"[{self.location}] Publisher initialized. Connecting to Brain at {self.config['redis']['host']}...")

    def publish_alert(self, token_data):
        """
        Publishes an alert to the global mesh network.
        """
        message = {
            "source": self.location,
            "timestamp": datetime.now().isoformat(),
            "type": "PUMP_DETECTED",
            "data": token_data
        }
        
        try:
            # Publishing returns the number of subscribers that received the message
            receivers = self.r.publish(self.channel, json.dumps(message))
            print(f"[{self.location}] 🚀 Sent alert! Received by {receivers} nodes.")
        except redis.ConnectionError:
            print(f"[{self.location}] ❌ Connection Lost! Retrying...")

    def start_mock_loop(self):
        """
        Simulates detecting opportunities for testing purposes.
        """
        print(f"[{self.location}] Starting mock detection loop...")
        while True:
            # Mocking a detection event every 10 seconds
            mock_data = {
                "token": "SolanaGlobalPubSub",
                "price": 0.0023,
                "reason": "Huge Volume Spike"
            }
            self.publish_alert(mock_data)
            time.sleep(10)

if __name__ == "__main__":
    # Example usage
    publisher = GlobalPublisher()
    try:
        publisher.start_mock_loop()
    except KeyboardInterrupt:
        print("\nStopping publisher...")
