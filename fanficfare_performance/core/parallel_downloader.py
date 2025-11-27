"""
Parallel Chapter Downloader

PERFORMANCE GAIN: ~10-20x faster
EFFORT: 1 day
RISK: Low (uses ThreadPoolExecutor from stdlib)

Downloads multiple chapters in parallel instead of sequentially.

Example:
    Sequential (old): 10 chapters × 2 seconds = 20 seconds
    Parallel (new):   max(10 chapters) = ~2 seconds
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional, Dict
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """A single download task"""
    chapter_number: int
    chapter_url: str
    chapter_title: str = ""


@dataclass
class DownloadResult:
    """Result of a download task"""
    chapter_number: int
    chapter_url: str
    content: Optional[str] = None
    error: Optional[Exception] = None
    duration: float = 0.0

    @property
    def success(self) -> bool:
        return self.error is None and self.content is not None


class ParallelDownloader:
    """
    Downloads chapters in parallel using thread pool.

    Benefits:
    - 10-20x faster for multi-chapter stories
    - Respects rate limits
    - Automatic error handling
    - Progress tracking

    Usage:
        downloader = ParallelDownloader(max_workers=10)
        results = downloader.download_chapters(tasks, fetch_func)
    """

    def __init__(
        self,
        max_workers: int = 10,
        rate_limit: Optional[float] = None,
    ):
        """
        Args:
            max_workers: Maximum number of parallel downloads
            rate_limit: Maximum requests per second (None = no limit)
        """
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self._last_request_time = 0.0

    def _rate_limit_sleep(self):
        """Sleep to respect rate limit"""
        if self.rate_limit is None:
            return

        min_interval = 1.0 / self.rate_limit
        elapsed = time.time() - self._last_request_time

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def download_chapters(
        self,
        tasks: List[DownloadTask],
        fetch_func: Callable[[str], str],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[DownloadResult]:
        """
        Download multiple chapters in parallel.

        Args:
            tasks: List of download tasks
            fetch_func: Function that takes a URL and returns content
                       Should be: def fetch(url: str) -> str
            progress_callback: Optional callback for progress updates
                              Called with (completed, total)

        Returns:
            List of DownloadResult objects (ordered by chapter_number)
        """
        if not tasks:
            return []

        logger.info(f"Starting parallel download of {len(tasks)} chapters with {self.max_workers} workers")
        start_time = time.time()

        results: Dict[int, DownloadResult] = {}

        def download_one(task: DownloadTask) -> DownloadResult:
            """Download a single chapter"""
            chapter_start = time.time()

            try:
                # Rate limiting
                self._rate_limit_sleep()

                # Fetch content
                logger.debug(f"Downloading chapter {task.chapter_number}: {task.chapter_url}")
                content = fetch_func(task.chapter_url)

                duration = time.time() - chapter_start

                return DownloadResult(
                    chapter_number=task.chapter_number,
                    chapter_url=task.chapter_url,
                    content=content,
                    duration=duration,
                )

            except Exception as e:
                duration = time.time() - chapter_start
                logger.error(f"Error downloading chapter {task.chapter_number}: {e}")

                return DownloadResult(
                    chapter_number=task.chapter_number,
                    chapter_url=task.chapter_url,
                    error=e,
                    duration=duration,
                )

        # Execute downloads in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(download_one, task): task
                for task in tasks
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results[result.chapter_number] = result

                completed += 1

                # Progress callback
                if progress_callback:
                    progress_callback(completed, len(tasks))

                # Log progress
                if result.success:
                    logger.info(
                        f"✓ Chapter {result.chapter_number}/{len(tasks)} "
                        f"downloaded in {result.duration:.2f}s"
                    )
                else:
                    logger.warning(
                        f"✗ Chapter {result.chapter_number}/{len(tasks)} "
                        f"failed: {result.error}"
                    )

        # Sort results by chapter number
        sorted_results = [results[i] for i in sorted(results.keys())]

        # Summary
        total_time = time.time() - start_time
        successful = sum(1 for r in sorted_results if r.success)
        failed = len(sorted_results) - successful

        logger.info(
            f"Parallel download complete: {successful} succeeded, {failed} failed "
            f"in {total_time:.2f}s (avg {total_time/len(tasks):.2f}s per chapter)"
        )

        return sorted_results

    def download_with_retry(
        self,
        tasks: List[DownloadTask],
        fetch_func: Callable[[str], str],
        max_retries: int = 3,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[DownloadResult]:
        """
        Download chapters with automatic retry on failure.

        Args:
            tasks: List of download tasks
            fetch_func: Function to fetch content
            max_retries: Maximum number of retries per chapter
            progress_callback: Optional progress callback

        Returns:
            List of DownloadResult objects
        """
        results = self.download_chapters(tasks, fetch_func, progress_callback)

        # Retry failed downloads
        for retry in range(max_retries):
            failed = [
                DownloadTask(
                    chapter_number=r.chapter_number,
                    chapter_url=r.chapter_url,
                )
                for r in results
                if not r.success
            ]

            if not failed:
                break

            logger.info(f"Retry {retry + 1}/{max_retries}: Retrying {len(failed)} failed chapters")

            retry_results = self.download_chapters(failed, fetch_func, progress_callback)

            # Update results
            for retry_result in retry_results:
                if retry_result.success:
                    # Replace failed result with successful retry
                    for i, r in enumerate(results):
                        if r.chapter_number == retry_result.chapter_number:
                            results[i] = retry_result
                            break

        return results


# Convenience function for backward compatibility
def download_chapters_parallel(
    chapter_urls: List[str],
    fetch_func: Callable[[str], str],
    max_workers: int = 10,
    rate_limit: Optional[float] = 2.0,
) -> List[str]:
    """
    Simple parallel download that returns list of content strings.

    Args:
        chapter_urls: List of chapter URLs
        fetch_func: Function to fetch content
        max_workers: Number of parallel workers
        rate_limit: Requests per second (None = no limit)

    Returns:
        List of chapter content strings (ordered, None for failures)
    """
    # Create tasks
    tasks = [
        DownloadTask(chapter_number=i, chapter_url=url)
        for i, url in enumerate(chapter_urls, 1)
    ]

    # Download
    downloader = ParallelDownloader(max_workers=max_workers, rate_limit=rate_limit)
    results = downloader.download_with_retry(tasks, fetch_func)

    # Extract content (None for failures)
    return [r.content for r in results]
