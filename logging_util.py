from fastapi import HTTPException
from typing import cast, TypeVar, Callable, Any
import time
import logging
import functools
import datetime

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

def get_request_logger():
    """Get a logger that will output to Uvicorn's error stream"""
    return logging.getLogger("uvicorn.error")

# Decorator to add consistent time logging to all endpoints
def time_logging(endpoint_name: str = None):
    """
    Decorator to add consistent time logging to all endpoints.
    Automatically logs start, completion, and errors with timing information.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get a fresh logger for each request
            logger = get_request_logger()
            func_name = endpoint_name or func.__name__
            start_time = time.time()
            request_id = f"req_started_at_{datetime.datetime.now(datetime.UTC).isoformat()}"
            
            # Log the start of the request
            logger.info(f"[{request_id}] Starting {func_name}")
            
            try:
                # Log the start of the function execution with debug info
                logger.debug(f"[{request_id}] Executing {func_name} with args: {args}")
                
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Calculate and log the execution time
                total_time = time.time() - start_time
                logger.info(f"[{request_id}] {func_name} completed in {total_time:.2f}s")
                
                return result
                
            except HTTPException as e:
                # Log HTTP exceptions with timing info
                error_time = time.time() - start_time
                logger.error(
                    f"[{request_id}] HTTP error in {func_name} after {error_time:.2f}s: {str(e)}",
                    exc_info=logger.isEnabledFor(logging.DEBUG)
                )
                raise
                
            except Exception as e:
                # Log any other exceptions with full traceback if debug is enabled
                error_time = time.time() - start_time
                logger.error(
                    f"[{request_id}] Error in {func_name} after {error_time:.2f}s: {str(e)}",
                    exc_info=logger.isEnabledFor(logging.DEBUG)
                )
                raise
                
        return cast(F, wrapper)
    return decorator