from flask import Flask, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from data_loader import load_constraints, load_orders, load_agents, build_graph
from state import OrderQueue, AgentRegistry
from dispatcher import Dispatcher
from metrics import MetricsTracker
from simulation import Simulation

app = Flask(__name__)
# Restrict CORS to specific origins for security
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

# Global simulation state
sim_data = {
    "history": [],
    "nodes": [],
    "edges": []
}

def init_simulation():
    global sim_data
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_path, "data", "raw")
    config_path = os.path.join(base_path, "config.json")
    
    constraints = load_constraints(os.path.join(data_dir, "constraints.csv"))
    orders_df = load_orders(os.path.join(data_dir, "orders.csv"))
    agents_list = load_agents(os.path.join(data_dir, "agents.csv"))
    dist_matrix, nodes = build_graph(os.path.join(data_dir, "environment_edges.csv"))
    
    # Get edges for map visualization
    import pandas as pd
    edges_df = pd.read_csv(os.path.join(data_dir, "environment_edges.csv"))
    edges = []
    for _, row in edges_df.iterrows():
        edges.append({
            "from": [int(row['from_x']), int(row['from_y'])],
            "to": [int(row['to_x']), int(row['to_y'])],
            "dist": float(row['distance_minutes'])
        })

    order_queue = OrderQueue()
    for _, row in orders_df.iterrows():
        order_queue.push(row.to_dict())

    agent_registry = AgentRegistry(agents_list, constraints)
    dispatcher = Dispatcher(config_path, dist_matrix)
    metrics_tracker = MetricsTracker()
    sim = Simulation(order_queue, agent_registry, dispatcher, metrics_tracker)
    
    start_time_str = orders_df['timestamp'].min()
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    
    sim.run(start_time)
    
    sim_data["history"] = sim.history
    sim_data["nodes"] = [{"x": x, "y": y} for x, y in nodes]
    sim_data["edges"] = edges
    
    # Save results.json as well
    results_path = os.path.join(base_path, "results.json")
    metrics_tracker.save_results(results_path)

@app.route('/api/simulation', methods=['GET'])
def get_simulation():
    return jsonify(sim_data)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init_simulation()
    app.run(port=5000, debug=False)
