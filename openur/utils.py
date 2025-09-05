"""
Utility functions for OpenUR.
"""
import logging
import time
from typing import List, Union, Optional
import numpy as np

def validate_ip_address(ip: str) -> bool:
    """Validate IP address format."""
    import socket
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def validate_joint_positions(positions: Union[List[float], np.ndarray],
                           num_joints: int = 6) -> bool:
    """Validate joint positions."""
    if len(positions) != num_joints:
        return False

    # Check for NaN or infinite values
    if isinstance(positions, np.ndarray):
        return not (np.isnan(positions).any() or np.isinf(positions).any())
    else:
        return all(isinstance(p, (int, float)) and not (p != p or p == float('inf'))
                  for p in positions)

def validate_pose(pose: Union[List[float], np.ndarray]) -> bool:
    """Validate 6D pose (position + orientation)."""
    if len(pose) != 6:
        return False

    if isinstance(pose, np.ndarray):
        return not (np.isnan(pose).any() or np.isinf(pose).any())
    else:
        return all(isinstance(p, (int, float)) and not (p != p or p == float('inf'))
                  for p in pose)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))

def rad_to_deg(radians: Union[float, List[float], np.ndarray]) -> Union[float, List[float], np.ndarray]:
    """Convert radians to degrees."""
    if isinstance(radians, (list, np.ndarray)):
        return [r * 180.0 / np.pi for r in radians]
    return radians * 180.0 / np.pi

def deg_to_rad(degrees: Union[float, List[float], np.ndarray]) -> Union[float, List[float], np.ndarray]:
    """Convert degrees to radians."""
    if isinstance(degrees, (list, np.ndarray)):
        return [d * np.pi / 180.0 for d in degrees]
    return degrees * np.pi / 180.0

def retry_on_failure(max_retries: int = 3, delay: float = 1.0,
                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying functions on failure."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logging.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    logging.warning(f"Function {func.__name__} failed (attempt {retries}/{max_retries}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
