import pandas as pd
import os
import logging
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_constraints(filepath):
    """Load constraints from CSV."""
    try:
        df = pd.read_csv(filepath)
        constraints = dict(zip(df['constraint'], df['value']))
        logger.info(f"Loaded {len(constraints)} constraints from {filepath}")
        return constraints
    except Exception as e:
        logger.error(f"Error loading constraints: {e}")
        return {}

def load_orders(filepath):
    """Load and validate orders from CSV."""
    try:
        df = pd.read_csv(filepath)
        required_cols = ['order_id', 'timestamp', 'location_x', 'location_y', 'prep_time_minutes', 'priority', 'sla_minutes']
        
        # Check for missing columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in orders.csv: {missing_cols}")
            return pd.DataFrame()

        # Basic validation: drop rows with null required fields
        initial_count = len(df)
        df = df.dropna(subset=required_cols)
        if len(df) < initial_count:
            logger.warning(f"Dropped {initial_count - len(df)} malformed order rows.")

        logger.info(f"Loaded {len(df)} orders from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Error loading orders: {e}")
        return pd.DataFrame()

def load_agents(filepath):
    """Load and validate agents from CSV."""
    try:
        df = pd.read_csv(filepath)
        required_cols = ['agent_id', 'current_x', 'current_y', 'rating']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in agents.csv: {missing_cols}")
            return pd.DataFrame()

        df = df.dropna(subset=required_cols)
        
        # Initialize agent state
        agents = []
        for _, row in df.iterrows():
            agent = row.to_dict()
            agent['active_orders'] = []
            agent['cumulative_assignments'] = 0
            agents.append(agent)
            
        logger.info(f"Loaded {len(agents)} agents from {filepath}")
        return agents
    except Exception as e:
        logger.error(f"Error loading agents: {e}")
        return []

def build_graph(filepath):
    """Build environment graph and compute all-pairs shortest paths using Floyd-Warshall."""
    try:
        df = pd.read_csv(filepath)
        required_cols = ['from_x', 'from_y', 'to_x', 'to_y', 'distance_minutes', 'delay_multiplier']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in edges.csv: {missing_cols}")
            return {}, {}

        # Use (x, y) as node identifier
        nodes = set()
        edges = []
        for _, row in df.iterrows():
            u = (int(row['from_x']), int(row['from_y']))
            v = (int(row['to_x']), int(row['to_y']))
            dist = float(row['distance_minutes']) * float(row['delay_multiplier'])
            nodes.add(u)
            nodes.add(v)
            edges.append((u, v, dist))

        # Floyd-Warshall initialization
        dist = defaultdict(lambda: defaultdict(lambda: float('inf')))
        for node in nodes:
            dist[node][node] = 0
            
        for u, v, d in edges:
            dist[u][v] = min(dist[u][v], d)
            dist[v][u] = min(dist[v][u], d) # Undirected graph

        # Floyd-Warshall algorithm
        sorted_nodes = sorted(list(nodes))
        for k in sorted_nodes:
            for i in sorted_nodes:
                if dist[i][k] == float('inf'): continue
                for j in sorted_nodes:
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]

        # Convert keys to strings for JSON serialization if needed later, but for internal use tuples are fine
        # For now, return as is.
        logger.info(f"Built graph with {len(nodes)} nodes and computed all-pairs shortest paths.")
        return dict(dist), nodes
    except Exception as e:
        logger.error(f"Error building graph: {e}")
        return {}, set()

if __name__ == "__main__":
    # Test loading
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(base_path, "data", "raw")
    constraints = load_constraints(os.path.join(data_dir, "constraints.csv"))
    orders = load_orders(os.path.join(data_dir, "orders.csv"))
    agents = load_agents(os.path.join(data_dir, "agents.csv"))
    dist_matrix, nodes = build_graph(os.path.join(data_dir, "environment_edges.csv"))
    
    print(f"Constraints: {constraints}")
    print(f"Total Orders: {len(orders)}")
    print(f"Total Agents: {len(agents)}")
    print(f"Total Nodes: {len(nodes)}")
