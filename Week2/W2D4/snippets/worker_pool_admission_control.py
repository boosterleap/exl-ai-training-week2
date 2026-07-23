"""Day 4 AM Topic 06: Bounded queue with admission control.

Simulates 25 claim resolution requests arriving at once against a 3-worker
pool with a queue capacity capped at 10. Demonstrates graceful rejection
("try later") for requests beyond capacity, rather than silent dropping or
crashing the pool.

This is what production systems do under overload:
  - Accept up to queue capacity
  - Reject excess with clear "try later" signal
  - Client retries later when system has capacity
  - Pool stays stable, doesn't crash or lose work
"""

import threading
import time
import queue
from dataclasses import dataclass

# Global tracking
lock = threading.Lock()
active_workers = 0
max_concurrent = 0
accepted_count = 0
rejected_count = 0
completed_count = 0
completion_order = []


@dataclass
class ClaimRequest:
    """Represents a claim resolution request."""
    request_id: int
    claim_id: str
    processing_time: float

    def __str__(self):
        return f"REQ-{self.request_id:03d} (CLM-{self.claim_id})"


@dataclass
class RequestResult:
    """Result of attempting to submit a request."""
    accepted: bool
    request: ClaimRequest
    message: str




def worker(worker_id: int, work_queue: queue.Queue, semaphore: threading.Semaphore):
    """Process claims from the queue, respecting concurrency limit."""
    global active_workers, max_concurrent, completed_count

    while True:
        try:
            request = work_queue.get(block=False)
        except queue.Empty:
            break

        with semaphore:
            with lock:
                active_workers += 1
                max_concurrent = max(max_concurrent, active_workers)

            # Simulate claim processing
            time.sleep(request.processing_time)

            with lock:
                active_workers -= 1
                completed_count += 1
                completion_order.append(request.request_id)

        work_queue.task_done()


def submit_request(request: ClaimRequest, work_queue: queue.Queue,
                   max_queue_size: int) -> RequestResult:
    """
    Try to submit a request to the queue.

    Returns:
        RequestResult with accepted=True and message if queued
        RequestResult with accepted=False and "try later" if queue is full
    """
    global accepted_count, rejected_count

    try:
        # Try to add without blocking
        work_queue.put_nowait(request)
        with lock:
            accepted_count += 1
        return RequestResult(
            accepted=True,
            request=request,
            message=f"Accepted (queue size: {work_queue.qsize()}/{max_queue_size})"
        )
    except queue.Full:
        with lock:
            rejected_count += 1
        return RequestResult(
            accepted=False,
            request=request,
            message=f"REJECTED - queue full ({max_queue_size}/{max_queue_size}), try later"
        )


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
    print(f"  Worker pool size:  {NUM_WORKERS}")
    print(f"  Queue capacity:    {MAX_QUEUE_SIZE}")
    print(f"  Expected behavior: Accept first {3 + MAX_QUEUE_SIZE}, reject rest")
    print(f"  (First 3 are processing, next {MAX_QUEUE_SIZE} queued, remaining {NUM_REQUESTS - 3 - MAX_QUEUE_SIZE} rejected)")
    print()

    # Create bounded queue
    work_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

    # Semaphore limits concurrency to 3
    semaphore = threading.Semaphore(NUM_WORKERS)

    # Start workers
    workers = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker, args=(i + 1, work_queue, semaphore))
        t.start()
        workers.append(t)

    print("=" * 80)
    print("SUBMISSION PHASE - 50 requests arrive at once")
    print("=" * 80)
    print()

    # Submit all 50 requests at once
    submission_results = []
    start_time = time.time()

    print("Submitting requests 1-50...")

    for i in range(1, NUM_REQUESTS + 1):
        # Vary processing times to make it interesting (0.1-0.25s range)
        processing_time = 0.1 + ((i - 1) % 4) * 0.04
        request = ClaimRequest(i, f"CLM-{i:05d}", processing_time)

        result = submit_request(request, work_queue, MAX_QUEUE_SIZE)
        submission_results.append(result)

    # Print summary of submissions
    print("Submission complete.")

    print()
    print("=" * 80)
    print("PROCESSING PHASE - Workers drain the queue")
    print("=" * 80)
    print()
    print("Processing in progress...")

    # Wait for all accepted requests to complete
    work_queue.join()
    for t in workers:
        t.join()

    elapsed = time.time() - start_time
    print(f"Processing complete. Elapsed: {elapsed:.2f}s")
    print()

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    print("Request Disposition:")
    print(f"  Total requests:   {NUM_REQUESTS}")
    print(f"  Accepted:         {accepted_count}")
    print(f"  Rejected:         {rejected_count}")
    print(f"  Completed:        {completed_count}")
    print()

    print("Which requests were rejected:")
    rejected_ids = [i + 1 for i, r in enumerate(submission_results) if not r.accepted]
    if rejected_ids:
        print(f"  Requests {rejected_ids[0]} through {rejected_ids[-1]}")
        print(f"  Total rejected: {len(rejected_ids)}")
    else:
        print("  None (all requests were accepted)")
    print()

    print("Performance:")
    print(f"  Max concurrent workers: {max_concurrent}/{NUM_WORKERS}")
    print(f"  Requests processed:    {completed_count}/{accepted_count}")
    print(f"  Total elapsed time:    {elapsed:.2f}s")
    print()

    print("=" * 80)
    print(f"KEY INSIGHT: REQUEST #{3 + MAX_QUEUE_SIZE + 1}")
    print("=" * 80)
    print()

    first_rejection_idx = None
    for idx, result in enumerate(submission_results):
        if not result.accepted:
            first_rejection_idx = idx
            break

    if first_rejection_idx is not None:
        req_result = submission_results[first_rejection_idx]
        print(f"Request #{first_rejection_idx + 1} status: REJECTED")
        print(f"Message: {req_result.message}")
    else:
        print("All requests were accepted (no rejections occurred)")
    print()

    if first_rejection_idx is not None:
        print("What happened:")
        print(f"  1. Requests 1-3 started processing (3 workers)")
        print(f"  2. Requests 4-{3 + MAX_QUEUE_SIZE} queued up (queue capacity: {MAX_QUEUE_SIZE})")
        print(f"  3. Request {first_rejection_idx + 1} arrived while queue was full")
        print(f"  4. Queue.put_nowait() raised queue.Full exception")
        print(f"  5. Exception caught, request marked REJECTED")
        print(f"  6. Client received 'try later' response, not a crash")
        print()
        print("Why this is better than alternatives:")
        print("  X Silent drop: Client never knows request failed")
        print("  X Crash: Pool becomes unavailable to all clients")
        print("  [OK] Graceful rejection: Clear signal to retry later")
    print()

    print("=" * 80)
    print("DAY 4 AM TOPIC 06 LESSON: GRACEFUL DEGRADATION")
    print("=" * 80)
    print("""
This demo shows the difference between three approaches under overload:

1. SILENT DROPPING (BAD)
   - Queue fills up
   - New requests silently discarded
   - Client has no idea it failed
   - Data loss, customer sees no response

2. CRASHING THE POOL (WORSE)
   - Queue fills up
   - Pool crashes or hangs trying to process
   - All requests fail, including ones that were queued
   - Cascading failure

3. GRACEFUL REJECTION (GOOD) - What we just saw
   - Queue fills up to capacity (20)
   - Request #21 rejected with "try later" signal
   - Client knows to retry later
   - Pool stays stable and healthy
   - In-flight requests still complete
   - System degrades predictably

Production Pattern:
   while (true) {
     try {
       submit(request);  // Might get "queue full" back
     } catch (QueueFull) {
       // Client-side: wait, then retry
       wait_backoff();
       retry(request);
     }
   }

Checkpoints implemented in this demo:
  [OK] Bounded queue (maxsize=20)
  [OK] Admission control (reject when full)
  [OK] Clear error signal (not silent, not crash)
  [OK] Atomic accept/reject (no double-processing)

What's missing (production needs):
  [ ] Backoff/jitter on client side
  [ ] Metrics: latency of rejected requests
  [ ] Circuit breaker: stop accepting if rejection rate > threshold
  [ ] Load shedding: proactively reject if queue > 80% full
    """)

    print()


if __name__ == "__main__":
    main()
