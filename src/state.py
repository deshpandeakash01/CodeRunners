import heapq
import logging

logger = logging.getLogger(__name__)

class OrderQueue:
    """Priority queue for orders based on priority level and timestamp."""
    PRIORITY_MAP = {
        'high': 0,
        'normal': 1,
        'low': 2
    }

    def __init__(self):
        self.queue = [] # List of (priority_val, timestamp, order_id, order_dict)
        self.pending_orders = {} # order_id -> order_dict

    def push(self, order):
        """Push a new order into the queue."""
        priority_val = self.PRIORITY_MAP.get(order['priority'].lower(), 2)
        # Using timestamp as secondary sort key for FIFO within same priority
        heapq.heappush(self.queue, (priority_val, order['timestamp'], order['order_id'], order))
        self.pending_orders[order['order_id']] = order
        order['state'] = 'PENDING'

    def pop(self):
        """Pop the highest priority order."""
        if not self.queue:
            return None
        _, _, order_id, order = heapq.heappop(self.queue)
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]
        return order

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)

class AgentRegistry:
    """Registry to track agent states."""
    def __init__(self, agents_list, constraints):
        self.agents = {a['agent_id']: a for a in agents_list}
        self.max_capacity = int(constraints.get('max_orders_per_agent', 2))

    def get_agent(self, agent_id):
        return self.agents.get(agent_id)

    def get_available_agents(self):
        """Return agents with active_orders < max_capacity."""
        return [a for a in self.agents.values() if len(a['active_orders']) < self.max_capacity]

    def update_agent_location(self, agent_id, x, y):
        if agent_id in self.agents:
            self.agents[agent_id]['current_x'] = x
            self.agents[agent_id]['current_y'] = y

    def add_order_to_agent(self, agent_id, order_id):
        agent = self.get_agent(agent_id)
        if agent and len(agent['active_orders']) < self.max_capacity:
            agent['active_orders'].append(order_id)
            agent['cumulative_assignments'] += 1
            return True
        return False

    def remove_order_from_agent(self, agent_id, order_id):
        agent = self.get_agent(agent_id)
        if agent and order_id in agent['active_orders']:
            agent['active_orders'].remove(order_id)
            return True
        return False
