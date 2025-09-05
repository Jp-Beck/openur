"""
Custom exceptions for OpenUR.
"""

class OpenURError(Exception):
    """Base exception for OpenUR."""
    pass

class ConnectionError(OpenURError):
    """Raised when connection to robot fails."""
    pass

class ConfigurationError(OpenURError):
    """Raised when configuration is invalid."""
    pass

class RTDEError(OpenURError):
    """Raised when RTDE operation fails."""
    pass

class DashboardError(OpenURError):
    """Raised when Dashboard operation fails."""
    pass

class URScriptError(OpenURError):
    """Raised when URScript operation fails."""
    pass

class SafetyError(OpenURError):
    """Raised when safety-related operation fails."""
    pass

class ValidationError(OpenURError):
    """Raised when input validation fails."""
    pass
