"""Initialize the app package."""
from fastapi import FastAPI
from .dependencies import get_db, oauth2_scheme
from .auth_utils import get_password_hash, verify_password

# Create the FastAPI application
app = FastAPI()

# Re-export the main components
__all__ = [
    'app',
    'get_db',
    'oauth2_scheme',
    'get_password_hash',
    'verify_password'
]
