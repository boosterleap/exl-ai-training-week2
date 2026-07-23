"""Day 4 AM Topic 06: Admission control - Fast demo version.

Demonstrates graceful rejection when queue capacity is exceeded.
Uses synchronous processing to run instantly without threading overhead.
"""

import queue
from dataclasses import dataclass

@dataclass
class Request:
    request_id: int
    claim_id: str


def main():
    print("=" * 80)
    print("ADMISSION CONTROL DEMO - Day 4 AM Topic 06")
    print("=" * 80)
    print()

    MAX_QUEUE_SIZE = 10
    NUM_REQUESTS = 25
    NUM_WORKERS = 3

    print(f"Configuration:")
    print(f"  Incoming requests: {NUM_REQUESTS}")
    print(f"  Worker pool size:  {NUM_WORKERS} (concurrent capacity)")
    print(f"  Queue capacity:    {MAX_QUEUE_SIZE}")
    print(f"  Total acceptance capacity: {NUM_WORKERS + MAX_QUEUE_SIZE} requests")
    print()

    # Create bounded queue
    work_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

    # Simulate all 50 requests arriving at once
    print("=" * 80)
    print("SUBMISSION PHASE - All 25 requests arrive simultaneously")
    print("=" * 80)
    print()

    accepted = []
    rejected = []

    for i in range(1, NUM_REQUESTS + 1):
        request = Request(i, f"CLM-{i:05d}")

        try:
            # Try to add to queue without blocking
            work_queue.put_nowait(request)
            accepted.append(i)
        except queue.Full:
            # Queue is full, reject this request
            rejected.append(i)

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Request Disposition:")
    print(f"  Total requests:    {NUM_REQUESTS}")
    print(f"  Accepted:          {len(accepted)}")
    print(f"    - Processing:    {min(NUM_WORKERS, len(accepted))}")
    print(f"    - Queued:        {len(accepted) - min(NUM_WORKERS, len(accepted))}")
    print(f"  Rejected:          {len(rejected)}")
    print()

    if rejected:
        print(f"Rejected requests: REQ-{rejected[0]:02d} through REQ-{rejected[-1]:02d}")
        print(f"  (First rejection at request #{rejected[0]})")
    print()

    print("=" * 80)
    print("WHAT JUST HAPPENED")
    print("=" * 80)
    print()

    print("Request flow:")
    print(f"  Requests 1-3:   Assigned to 3 workers (processing immediately)")
    print(f"  Requests 4-13:  Queued up (waiting for worker to free up)")
    print(f"  Requests 14-25: REJECTED - queue was full (capacity {MAX_QUEUE_SIZE})")
    print()

    print("Why request #14 got rejected:")
    print("  1. Requests 1-3 claimed all 3 worker slots")
    print("  2. Requests 4-13 filled the queue (capacity 10)")
    print("  3. Request 14 arrived to find: 3 workers busy + 10 queued = FULL")
    print("  4. Queue.put_nowait() raised queue.Full exception")
    print("  5. Exception caught, request marked REJECTED with 'try later' message")
    print()

    print("=" * 80)
    print("WHY THIS IS CORRECT BEHAVIOR")
    print("=" * 80)
    print()

    print("""
Three approaches to overload:

1. SILENT DROPPING (WRONG)
   - Accept request into queue
   - Queue grows without bounds
   - Memory exhausted, system crashes
   - Client never knows request failed
   X Result: Data loss, cascading failure

2. BLOCKING THE CALLER (WRONG)
   - Try to add to unbounded queue
   - Queue fills memory
   - Thread blocks indefinitely
   - Everything stalls
   X Result: Complete deadlock

3. GRACEFUL REJECTION (CORRECT) - What we see here
   - Bounded queue with explicit capacity
   - Try to submit request
   - If queue is full, reject immediately
   - Client gets "try later" signal
   - Client can retry with backoff
   [OK] Result: System stays healthy under overload

The pattern in pseudocode:

   try {
     queue.put_nowait(request);  // Add to queue
   } catch (QueueFull) {
     return HttpResponse(503, "Queue full, retry in 10s");
   }

   Client side receives 503 and knows to:
   - Wait X seconds
   - Retry the request
   - Route to fallback system
   - Show user "system busy" message
    """)

    print()
    print("=" * 80)
    print("DAY 4 AM TOPIC 06 PRINCIPLE: BACKPRESSURE")
    print("=" * 80)
    print()

    print("""
A healthy system under overload:

OVERLOADED (typical in production):
  Incoming: 100 req/sec
  Processing: 30 req/sec
  Queue capacity: 20

  Result:
    - First 30 requests: accepted + processing
    - Next 20 requests: accepted + queued
    - Next 50 requests: REJECTED with 503

  Why this is healthy:
    [OK] Clients see failures and back off
    [OK] Queue doesn't grow unbounded
    [OK] System stays responsive
    [OK] No cascading failures

WITHOUT BACKPRESSURE (bad):
  Incoming: 100 req/sec
  Processing: 30 req/sec
  Queue capacity: UNLIMITED

  Result:
    - All 100 requests accepted
    - 30 processing, 70 queued
    - Next second: 100 more added, 70 still queued
    - Next second: Queue now has 140 items
    - Memory fills up, GC pauses, system slows
    - All requests timeout, cascading failure
    [FAIL] Clients get timeouts instead of clear rejection
    """)

    print()


if __name__ == "__main__":
    main()
