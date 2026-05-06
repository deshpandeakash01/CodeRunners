import os
import logging
from datetime import datetime
from data_loader import load_constraints, load_orders, load_agents, build_graph
from state import OrderQueue, AgentRegistry
from dispatcher import Dispatcher
from metrics import MetricsTracker
from simulation import Simulation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_path, "data", "raw")
    config_path = os.path.join(base_path, "config.json")
    results_path = os.path.join(base_path, "results.json")

    logger.info("Starting Smart Delivery Dispatch System")

    # PHASE 1: Load Data
    constraints = load_constraints(os.path.join(data_dir, "constraints.csv"))
    orders_df = load_orders(os.path.join(data_dir, "orders.csv"))
    agents_list = load_agents(os.path.join(data_dir, "agents.csv"))
    dist_matrix, nodes = build_graph(os.path.join(data_dir, "environment_edges.csv"))

    if orders_df.empty or not agents_list or not dist_matrix:
        logger.error("Failed to load required data. Exiting.")
        return

    # PHASE 2: Initialize State
    order_queue = OrderQueue()
    for _, row in orders_df.iterrows():
        order_queue.push(row.to_dict())

    agent_registry = AgentRegistry(agents_list, constraints)
    
    # PHASE 3: Core Logic
    dispatcher = Dispatcher(config_path, dist_matrix)
    
    # PHASE 4: Metrics
    metrics_tracker = MetricsTracker()
    
    # PHASE 5: Simulation
    sim = Simulation(order_queue, agent_registry, dispatcher, metrics_tracker)
    
    # Determine simulation start time (earliest order)
    start_time_str = orders_df['timestamp'].min()
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    
    logger.info("Running simulation...")
    sim.run(start_time)
    
    # Export Results
    metrics_tracker.save_results(results_path)
    metrics_tracker.print_summary()
    
    logger.info("Simulation complete.")

if __name__ == "__main__":
    main()
