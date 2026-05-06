import json
import logging
import math
import statistics

logger = logging.getLogger(__name__)

class MetricsTracker:
    def __init__(self):
        # Welford's algorithm state: {priority: (count, mean, M2)}
        self.delivery_times = {
            'high': [0, 0.0, 0.0],
            'normal': [0, 0.0, 0.0],
            'low': [0, 0.0, 0.0],
            'overall': [0, 0.0, 0.0]
        }
        
        self.sla_stats = {
            'high': {'violations': 0, 'total': 0},
            'normal': {'violations': 0, 'total': 0},
            'low': {'violations': 0, 'total': 0},
            'overall': {'violations': 0, 'total': 0}
        }
        
        self.agent_assignments = {} # agent_id -> count

    def update_delivery_time(self, priority, time_taken):
        priority = priority.lower()
        for key in [priority, 'overall']:
            count, mean, M2 = self.delivery_times[key]
            count += 1
            delta = time_taken - mean
            mean += delta / count
            delta2 = time_taken - mean
            M2 += delta * delta2
            self.delivery_times[key] = [count, mean, M2]

    def update_sla(self, priority, is_violation):
        priority = priority.lower()
        for key in [priority, 'overall']:
            self.sla_stats[key]['total'] += 1
            if is_violation:
                self.sla_stats[key]['violations'] += 1

    def update_agent_workload(self, agent_id):
        self.agent_assignments[agent_id] = self.agent_assignments.get(agent_id, 0) + 1

    def get_metrics(self):
        report = {
            "delivery_metrics": {},
            "sla_metrics": {},
            "fairness_metrics": {}
        }
        
        # Delivery times
        for key, (count, mean, _) in self.delivery_times.items():
            if count > 0:
                report["delivery_metrics"][key] = {
                    "average_time": round(mean, 2),
                    "count": count
                }
        
        # SLA compliance
        for key, stats in self.sla_stats.items():
            if stats['total'] > 0:
                violation_rate = (stats['violations'] / stats['total']) * 100
                report["sla_metrics"][key] = {
                    "violation_rate": round(violation_rate, 2),
                    "compliance_rate": round(100 - violation_rate, 2),
                    "violations": stats['violations'],
                    "total": stats['total']
                }
                
        # Fairness
        if self.agent_assignments:
            counts = list(self.agent_assignments.values())
            # Fill in 0s for agents with no assignments if we had the full list
            # But for now, just use what we have
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0.0
            report["fairness_metrics"] = {
                "std_deviation": round(std_dev, 2),
                "min_assignments": min(counts),
                "max_assignments": max(counts),
                "range": max(counts) - min(counts)
            }
            
        return report

    def save_results(self, filepath):
        metrics = self.get_metrics()
        try:
            with open(filepath, 'w') as f:
                json.dump(metrics, f, indent=4)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_summary(self):
        metrics = self.get_metrics()
        print("\n=== SIMULATION SUMMARY ===")
        print(f"Overall Avg Delivery Time: {metrics['delivery_metrics'].get('overall', {}).get('average_time', 'N/A')} mins")
        print(f"Overall SLA Compliance: {metrics['sla_metrics'].get('overall', {}).get('compliance_rate', 'N/A')}%")
        print(f"Workload Fairness (StdDev): {metrics['fairness_metrics'].get('std_deviation', 'N/A')}")
        print("==========================\n")
