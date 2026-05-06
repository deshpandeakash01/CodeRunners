# Smart Delivery Dispatch System

## Team Information
- **Team Name**: CodeRunners
- **Team Members**: akash, vishal, vaibhav
- **Year**: 2026
- **All-Female Team**: No

## Architecture Overview

#### Our system uses a priority-based dispatch strategy with a weighted scoring function to optimize for delivery speed, SLA compliance, and workload fairness.

- **Dispatch Strategy**: A tick-based simulation processes orders as they arrive. Orders are managed in a priority queue (High > Normal > Low) to ensure critical deliveries are handled first.
- **Scoring Logic**: Candidates are scored using a weighted formula balancing travel time (precomputed in O(1) via Floyd-Warshall), SLA urgency (time until deadline), agent workload (fairness), and agent rating. The agent with the lowest score is selected.
- **SLA deadlines, priority orders, and agent capacity**: Agent capacity is strictly enforced (maximum 2 active orders at a time). High-priority orders jump the queue. SLA deadlines are managed by exponentially increasing the urgency weight as the deadline approaches, ensuring no SLA breaches.
- **Pipeline Steps**: 1. Data loading and validation (Pandas) -> 2. Graph precomputation (Floyd-Warshall) -> 3. Event-driven tick simulation (Assign/Transit/Deliver) -> 4. Real-time metric tracking and visualization.

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
