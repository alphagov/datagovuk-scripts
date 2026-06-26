import argparse
import csv
import sys
import time
import random
from enum import StrEnum
from collections import defaultdict
from pprint import pprint
import asyncio
from urllib.parse import urlparse
import aiohttp
from aiolimiter import AsyncLimiter

# Configuration
NUM_WORKERS = 100                   # Fixed number of parallel worker tasks
RATE_LIMIT_PER_HOST = 2             # Max requests per host...
RATE_LIMIT_PERIOD = 2.0             # ...per this many seconds


class Category(StrEnum):
    OK = "OK"
    NOT_FOUND = "404"
    GONE = "410"
    TOO_MANY_REQUESTS = "429"
    OTHER_CLIENT_ERROR = "OTHER_CLIENT_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    DNS_ERROR = "DNS_ERROR"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    OTHER_ERROR = "OTHER_ERROR"


def classify_response(
    status_code: int | None, exc: BaseException | None
) -> tuple[Category, str | None]:
    match (status_code, exc):
        case (_, asyncio.TimeoutError()):
            return Category.TIMEOUT, str(exc)
        case (_, aiohttp.ClientConnectorDNSError()):
            return Category.DNS_ERROR, str(exc)
        case (_, aiohttp.ClientOSError()):
            return Category.CONNECTION_REFUSED, str(exc)
        case (_, aiohttp.ServerDisconnectedError()):
            return Category.OTHER_ERROR, str(exc)
        case (_, aiohttp.ClientConnectorError()):
            return Category.CONNECTION_ERROR, str(exc)
        case (_, BaseException()):
            print(exc.__class__.__name__)
            print(str(exc))
            return Category.OTHER_ERROR, str(exc)
        case (None, None):
            return Category.OTHER_ERROR, "no status and no exception"
        case (404, None):
            return Category.NOT_FOUND, None
        case (410, None):
            return Category.GONE, None
        case (429, None):
            return Category.TOO_MANY_REQUESTS, None
        case (int(s), None) if 200 <= s < 400:
            return Category.OK, None
        case (int(s), None) if 400 <= s < 500:
            return Category.OTHER_CLIENT_ERROR, None
        case (int(s), None) if 500 <= s < 600:
            return Category.SERVER_ERROR, None
        case _:
            print(f"Could not classify error {exc.__class__.__name__}")
            return Category.OTHER_ERROR, f"unexpected status {status_code}"

def get_resources_to_retry(csv_path):
    retry_resources = {}
    
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row["category"] == "OK":
                continue
            error_key = row["http-status"]
            if not error_key:
                error_key = row["category"]
            retry_resources[row["resource-id"]] = row
    return retry_resources

# Shared dictionary to store the rate limiters for each individual domain
host_limiters = {}

def get_limiter_for_url(url: str) -> AsyncLimiter:
    """Extracts the domain from the URL and gets/creates its specific limiter."""
    parsed_url = urlparse(url)
    host = parsed_url.netloc or "unknown"
    
    if host not in host_limiters:
        host_limiters[host] = AsyncLimiter(RATE_LIMIT_PER_HOST, RATE_LIMIT_PERIOD)
        
    return host_limiters[host]


async def fetch_url(session: aiohttp.ClientSession, url: str, resource_id: str) -> dict:
    """Fetches a single URL obeying per-host rate limits."""
    limiter = get_limiter_for_url(url)
    
    # Obey per-host rate limit (pauses if this specific host is hot)
    async with limiter:
        try:
            timeout = aiohttp.ClientTimeout(total=10) 
            async with session.get(url, timeout=timeout) as response:
                text = await response.text(errors="replace")
                return {
                    "url": url,
                    "status": response.status,
                    "error": None,
                    "resource_id": resource_id,
                }
                # Process your data here (e.g., save to a database or file)
        except Exception as e:
            return {
                "url": url,
                "status": None,
                "error": e,
                "resource_id": resource_id,
            }

processed_count = 0

async def worker(queue: asyncio.Queue, session: aiohttp.ClientSession, shared_results: list):
    """A persistent worker that pulls URLs from the queue and processes them."""
    global processed_count
    while True:
        url, resource_id = await queue.get()
        try:
            result = await fetch_url(session, url, resource_id)
            shared_results.append(result)
            processed_count += 1
            if processed_count % 100 == 0:
                print(".", end="")
                sys.stdout.flush()
        finally:
            # Notify the queue that the item is fully processed
            queue.task_done()


async def main(input_csv_file_path, output_csv_file_path, limit=None):
    # Initialize the queue and fill it up
    queue = asyncio.Queue()
    resources_to_retry = get_resources_to_retry(input_csv_file_path)
    retry_urls = set((resource["resource-url"].strip(), resource["resource-id"]) for resource in resources_to_retry.values())
    urls_to_retry = list(retry_urls)
    if not limit:
        limit = len(retry_urls)
    urls_to_retry = random.sample(urls_to_retry, limit)
    for url in urls_to_retry:
        await queue.put(url)

    shared_results = []

    async with aiohttp.ClientSession() as session:
        # Create a fixed pool of persistent worker tasks
        workers = []
        for _ in range(NUM_WORKERS):
            task = asyncio.create_task(worker(queue, session, shared_results))
            workers.append(task)
            
        # Wait until the queue is completely empty and all items are processed
        await queue.join()
        
        # Cancel our persistent workers since their work is done
        for worker_task in workers:
            worker_task.cancel()
            
        # Wait for all workers to gracefully acknowledge cancellation
        await asyncio.gather(*workers, return_exceptions=True)

    with open(output_csv_file_path, "w", newline="", encoding="utf-8") as f:
        REPORT_HEADERS = [
            "datagovuk-url",
            "package-id",
            "package-name",
            "package-metadata-created",
            "package-metadata-modified",
            "guid",
            "resource-id",
            "resource-url",
            "resource-created",
            "resource-last-modified",
            "resource-metadata-modified",
            "org-name",
            "org-id",
            "http-status",
            "category",
            "error-detail",
            "original-http-status",
            "original-category",
            "original-error-detail",
            "to-delete",
            "checked-at",
        ]
        writer = csv.DictWriter(f, fieldnames=REPORT_HEADERS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for result in shared_results:
            resource_id = result["resource_id"]
            original_row = resources_to_retry[resource_id]
            response_category, response_detail = classify_response(result["status"], result["error"])
            new_row = {
                **original_row,
                "http-status": result["status"] or "",
                "category": response_category.name,
                "error-detail": response_detail or "",
                "original-http-status": original_row["http-status"],
                "original-category": original_row["category"],
                "original-error-detail": original_row["error-detail"],
                "to-delete": "FALSE" if response_category == Category.OK else "TRUE",
            }
            writer.writerow(new_row)


def parse_args():
    parser = argparse.ArgumentParser(description="A script for retrying requests to broken links for data.gov.uk")
    parser.add_argument("input_csv_file_path", type=str, help="The CSV file of a previous link check/retry run")
    parser.add_argument("output_csv_file_path", type=str, help="Path for CSV file to save results to")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Maximum number of URLs to check")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    start = time.time()
    print(f"Starting worker pool to process URLs...")
    args = parse_args()
    asyncio.run(main(args.input_csv_file_path, args.output_csv_file_path, limit=args.limit))
    time_taken = time.time() - start
    print(f"All URLs processed successfully in {time_taken}S.")
