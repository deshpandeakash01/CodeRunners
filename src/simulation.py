import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Simulation:
    """
    Event-driven simulation engine for the delivery dispatch system.
    
    Manages the lifecycle of orders and agents over time, advancing
    in tick increments to process pending orders, update agent locations,
    and record performance metrics.
    """
    def __init__(self, order_queue, agent_registry, dispatcher, metrics_tracker):
        self.order_queue = order_queue
        self.agent_registry = agent_registry
        self.dispatcher = dispatcher
        self.metrics = metrics_tracker
        
        self.current_time = None
        self.in_transit_orders = [] # List of (delivery_time, agent_id, order)
        self.total_dispatched = 0
        self.completed_orders = 0
        self.history = [] # List of state snapshots per tick

    def get_snapshot(self):
        return {
            "timestamp": self.current_time.strftime('%Y-%m-%d %H:%M:%S') if self.current_time else "",
            "agents": [
                {
                    "id": a['agent_id'],
                    "x": a['current_x'],
                    "y": a['current_y'],
                    "active_orders": list(a['active_orders']),
                    "rating": a['rating'],
                    "assignments": a['cumulative_assignments']
                }
                for a in self.agent_registry.agents.values()
            ],
            "in_transit": [
                {
                    "order_id": o['order_id'],
                    "agent_id": aid,
                    "target_x": o['location_x'],
                    "target_y": o['location_y'],
                    "delivery_time": dt.strftime('%Y-%m-%d %H:%M:%S')
                }
                for dt, aid, o in self.in_transit_orders
            ],
            "pending_count": self.order_queue.size(),
            "metrics": self.metrics.get_metrics()
        }

    def run(self, start_time):
        self.current_time = start_time
        logger.info(f"Starting simulation at {self.current_time}")
        
        while not self.order_queue.is_empty() or self.in_transit_orders:
            self.tick()
            self.history.append(self.get_snapshot())
            self.current_time += timedelta(minutes=1)
            
            if self.current_time > start_time + timedelta(days=1):
                logger.warning("Simulation exceeded 24 hours. Breaking.")
                break

    def tick(self):
        # 1. Complete deliveries
        remaining_in_transit = []
        for delivery_time, agent_id, order in self.in_transit_orders:
            if self.current_time >= delivery_time:
                self.complete_delivery(agent_id, order)
            else:
                remaining_in_transit.append((delivery_time, agent_id, order))
        self.in_transit_orders = remaining_in_transit

        # 2. Try to dispatch pending orders
        available_agents = self.agent_registry.get_available_agents()
        
        while available_agents and not self.order_queue.is_empty():
            order = self.order_queue.pop()
            
            order_arrival = datetime.strptime(order['timestamp'], '%Y-%m-%d %H:%M:%S')
            if order_arrival > self.current_time:
                self.order_queue.push(order)
                break
            
            agent, travel_time = self.dispatcher.dispatch(order, available_agents, self.total_dispatched)
            
            if agent:
                self.assign_order(agent, order, travel_time)
                available_agents = self.agent_registry.get_available_agents()
            else:
                self.order_queue.push(order)
                break

    def assign_order(self, agent, order, travel_time):
        agent_id = agent['agent_id']
        order_id = order['order_id']
        
        if self.agent_registry.add_order_to_agent(agent_id, order_id):
            order['state'] = 'IN_TRANSIT'
            order['assigned_time'] = self.current_time
            
            prep_time = float(order['prep_time_minutes'])
            total_time = prep_time + travel_time
            delivery_time = self.current_time + timedelta(minutes=total_time)
            
            self.in_transit_orders.append((delivery_time, agent_id, order))
            self.total_dispatched += 1
            self.metrics.update_agent_workload(agent_id)

    def complete_delivery(self, agent_id, order):
        order['state'] = 'DELIVERED'
        order['completion_time'] = self.current_time
        
        self.agent_registry.update_agent_location(agent_id, order['location_x'], order['location_y'])
        self.agent_registry.remove_order_from_agent(agent_id, order['order_id'])
        
        time_taken = (order['completion_time'] - order['assigned_time']).total_seconds() / 60
        self.metrics.update_delivery_time(order['priority'], time_taken)
        
        arrival_time = datetime.strptime(order['timestamp'], '%Y-%m-%d %H:%M:%S')
        total_wait_plus_delivery = (order['completion_time'] - arrival_time).total_seconds() / 60
        is_violation = total_wait_plus_delivery > float(order['sla_minutes'])
        self.metrics.update_sla(order['priority'], is_violation)
        
        self.completed_orders += 1
