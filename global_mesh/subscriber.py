import redis
import json
import yaml
import os
import time

# Load Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

class GlobalSubscriber:
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
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(self.channel)
        print(f"[BOT] Listening on channel: {self.channel}...")

    def process_message(self, message):
        """
        Handles incoming messages from the mesh network.
        """
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                source = data.get('source', 'UNKNOWN')
                timestamp = data.get('timestamp')
                content = data.get('data')
                
                print(f"\n⚡ [ALERT RECEIVED] from {source} at {timestamp}")
                print(f"   Payload: {content}")
                
                # Here you would trigger your Telegram Bot or Trading Action
                self.trigger_action(content)
                
            except json.JSONDecodeError:
                print(f"Received raw message: {message['data']}")

    def trigger_action(self, data):
        # Placeholder for actual action
        print(f"   >>> EXECUTING TRADE/ALERT FOR {data.get('token')} <<<")

    def run(self):
        print("Waiting for signals instantly via Redis/PubSub...")
        try:
            for message in self.pubsub.listen():
                self.process_message(message)
        except redis.ConnectionError:
            print("❌ Connection to Redis Master lost! Reconnecting...")
            time.sleep(2)
            self.run() # Simple reconnect logic

if __name__ == "__main__":
    bot = GlobalSubscriber()
    bot.run()
