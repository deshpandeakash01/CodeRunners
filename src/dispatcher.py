import json
import os
import logging

logger = logging.getLogger(__name__)

class Dispatcher:
    """
    Evaluates candidates and assigns orders to delivery agents.
    
    This class handles the core assignment logic by calculating a 
    weighted score for each valid (agent, order) pair based on 
    travel time, SLA urgency, workload fairness, and agent rating.
    """
    def __init__(self, config_path, dist_matrix):
        self.config = self.load_config(config_path)
        self.dist_matrix = dist_matrix
        self.weights = self.config.get('weights', {
            "travel_time": 0.4,
            "sla_urgency": 0.3,
            "workload": 0.2,
            "rating": 0.1
        })

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def find_candidates(self, order, available_agents):
        """Filter agents that have a path to the order location."""
        candidates = []
        order_loc = (int(order['location_x']), int(order['location_y']))
        
        for agent in available_agents:
            agent_loc = (int(agent['current_x']), int(agent['current_y']))
            if agent_loc in self.dist_matrix and order_loc in self.dist_matrix[agent_loc]:
                travel_time = self.dist_matrix[agent_loc][order_loc]
                if travel_time != float('inf'):
                    candidates.append((agent, travel_time))
        return candidates

    def score_agent(self, agent, order, travel_time, total_orders_dispatched):
        """
        Score formula:
        score = (w_time * travel_time)
              + (w_sla * sla_urgency)
              + (w_load * current_workload)
              - (w_rating * rating) # Higher rating is better, so subtract
        """
        # travel_time is already provided
        
        # sla_urgency: inverse of sla_minutes (lower sla = more urgent)
        # Or more accurately: how close we are to the deadline.
        # For simplicity in scoring candidate selection:
        sla_urgency = 1.0 / max(float(order['sla_minutes']), 1.0)
        
        # current_workload: ratio of active orders to max capacity (but here we just use active orders count)
        workload = len(agent['active_orders'])
        
        # rating: agent rating (normalized or just raw)
        rating = float(agent['rating'])
        
        score = (self.weights['travel_time'] * travel_time) + \
                (self.weights['sla_urgency'] * sla_urgency * 100) + \
                (self.weights['workload'] * workload * 10) - \
                (self.weights['rating'] * rating)
        
        return score

    def dispatch(self, order, available_agents, total_orders_dispatched):
        candidates = self.find_candidates(order, available_agents)
        if not candidates:
            return None, None
        
        best_agent = None
        best_score = float('inf')
        best_travel_time = 0
        
        for agent, travel_time in candidates:
            score = self.score_agent(agent, order, travel_time, total_orders_dispatched)
            if score < best_score:
                best_score = score
                best_agent = agent
                best_travel_time = travel_time
                
        return best_agent, best_travel_time
