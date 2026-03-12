# User Rate Limit

This repository serves as a practical implementation reference and study guide for various **Rate Limiting** algorithms. It contains both a working implementation of a rate limiter using FastAPI and Valkey (Redis), as well as comprehensive documentation explaining the theory behind different rate limiting strategies.

## What's Included

*   **API Server (`/api-server`)**: A Python FastAPI application that implements a custom `ValkeyRateLimitMiddleware`. It demonstrates how to apply rate limits based on user IDs.
*   **Infrastructure (`docker-compose.yaml`)**: Docker-ready setup that spins up the FastAPI application alongside Valkey and Keycloak (for authentication).
*   **Test Suite (`test_client.py`)**: A script to test the rate-limiting functionality under load, verifying that exactly the right amount of requests are allowed through.

## Rate Limiting Algorithms Covered

The documentation explores the following rate limiting strategies:
1.  Fixed Window Counter
2.  Sliding Window Log
3.  Sliding Window Counter
4.  Token Bucket
5.  Leaky Bucket

You can view the full documentation site [here](https://arjunraghurama.github.io/user-rate-limit/), or by navigating directly to the `/docs` folder in this repository.

## Getting Started

### Prerequisites
*   Docker and Docker Compose
*   Python 3.10+ (for running the test client locally)

### Running the Application

1.  Start the infrastructure (FastAPI, Valkey, Keycloak):
    ```bash
    docker compose up --build -d
    ```

2.  The API will be available at `http://localhost:8000`.

### Running the Test Client

To see the rate limiting in action, you can run the provided test script. It will attempt to burst requests to the API and print out which requests succeed (200 OK) and which are throttled (429 Too Many Requests).

```bash
# Install dependencies using uv
uv init

uv add requests

# Run the test
uv run test_client.py
```