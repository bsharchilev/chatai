from collections import deque
import threading
import time
from typing import List, Tuple
from itertools import islice

from type_names import ChatMessage

class MessageCache:
    def __init__(self, max_size: int):
        self.queue = deque()
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def add_message(self, message: ChatMessage):
        with self.lock:
            # Insertion sort to maintain the deque sorted by timestamp
            timestamp = message.unixtime
            if not self.queue or self.queue[-1][0] <= timestamp:
                self.queue.append((timestamp, message))
            else:
                for idx in range(len(self.queue)):
                    if self.queue[idx][0] < timestamp:
                        self.queue.insert(idx, (timestamp, message))
                        break
            
            # Trim the deque if it exceeds the max size
            if len(self.queue) > self.max_size:
                self.queue.popleft()

    def get_last_n_messages(self, n: int) -> List[ChatMessage]:
        with self.lock:
            # Use islice to efficiently get the last n elements without copying
            retval = list(islice(self.queue, max(len(self.queue) - n, 0), len(self.queue)))
            return [x[1] for x in retval]