class LoginFailedException(Exception):
    """Exception raised when login fails.

    This exception is raised when the login attempt to a financial institution fails.
    It is typically raised when the user credentials are incorrect or the service is unavailable.
    """
