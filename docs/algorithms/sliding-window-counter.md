# Sliding Window Counter

The **Sliding Window Counter** algorithm is a hybrid approach that combines the low memory cost of the Fixed Window Counter with the smoothness of the Sliding Window Log.

Instead of storing individual request timestamps, it keeps the simple counters from the fixed windows and dynamically calculates an approximation of the requests within the sliding window.

## How It Works

It looks at the counter of the *current* fixed window and the *previous* fixed window, and weights the previous window's counter based on how much time has passed in the current window.

**Formula:**
`Requests in Sliding Window = (Requests in Previous Window * weight) + Requests in Current Window`

Where `weight` is the percentage of the current window that has *not* yet passed.

**Example:**
*   Limit: 50 requests per minute.
*   We are at 12:01:15 (i.e., 25% of the way through the current 1-minute window).
*   Requests in previous window (12:00:00 - 12:00:59): 40
*   Requests in current window (12:01:00 - 12:01:15): 10

Calculation:
*   Weight of previous window = `(60s - 15s) / 60s` = 0.75
*   Approximated Sliding Window Requests = `(40 * 0.75) + 10` = `30 + 10 = 40`.
*   Since `40 < 50`, the next request is allowed.

### Diagram

```mermaid
graph TD
    Prev[Previous Window: 12:00] -->|Count: 40| Calc
    Curr[Current Window: 12:01] -->|Count: 10| Calc
    
    Time[Current Time: 12:01:15] -.->|Elapsed: 25%| Weighting
    
    Weighting[Weight of Previous Window = 75%] --> Calc
    
    Calc((Calculate<br/>40 * 0.75 + 10 = 40)) --> Condition{40 < Limit (50)?}
    
    Condition -->|Yes| Allow[Allow Request & Increment Current Window]
    Condition -->|No| Block[Block Request (429)]
```

## Pros and Cons

*   **Pros:**
    *   **Memory Efficient:** Requires storing only two integers per user (current bucket count, previous bucket count).
    *   **Smooths out edges:** Mitigates the bursting at the boundaries that plagues the simple Fixed Window Counter.
*   **Cons:**
    *   **An Approximation:** It assumes that requests in the previous window were distributed perfectly evenly. If all 40 of earlier requests happened at 12:00:59, the math strictly fails us, letting through a burst. However, in practical scale, distribution is often even enough.

## Code Example

Implementation using Valkey:

```python
import time
import valkey

def is_allowed(user_id: str, limit: int, window_in_seconds: int, client: valkey.Valkey) -> bool:
    now = time.time()
    current_time_bucket = int(now // window_in_seconds)
    previous_time_bucket = current_time_bucket - 1
    
    curr_key = f"rate_limit:{user_id}:{current_time_bucket}"
    prev_key = f"rate_limit:{user_id}:{previous_time_bucket}"
    
    # Fetch current and previous bucket counts
    counts = client.mget([curr_key, prev_key])
    curr_count = int(counts[0] or 0)
    prev_count = int(counts[1] or 0)
    
    # Calculate approximation
    elapsed_time_in_curr_window = now % window_in_seconds
    weight_of_prev_window = 1 - (elapsed_time_in_curr_window / window_in_seconds)
    
    estimated_count = (prev_count * weight_of_prev_window) + curr_count + 1 # +1 for upcoming request
    
    if estimated_count > limit:
        return False
        
    # Increment the current bucket since we allowed it
    pipeline = client.pipeline()
    pipeline.incr(curr_key)
    pipeline.expire(curr_key, window_in_seconds * 2)
    pipeline.execute()
    
    return True
```
