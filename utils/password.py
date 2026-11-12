from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


def hash_password(password):
    """
    Convert plain password into hashed password
    """
    return generate_password_hash(password)


def verify_password(stored_password, entered_password):
    """
    Compare stored password with entered password
    """
    return check_password_hash(stored_password, entered_password)