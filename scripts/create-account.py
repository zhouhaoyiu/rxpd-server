"""Generate a private JSON account entry; append it to the APP_USERS_FILE array."""
import argparse
import getpass
import hashlib
import base64
import secrets
import json
parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("--role", choices=["staff", "admin"], default="staff")
args = parser.parse_args()
password = getpass.getpass("Password (12+ characters): ")
if len(password) < 12 or password != getpass.getpass("Repeat password: "):
    parser.error("Passwords must match and contain at least 12 characters")
salt = secrets.token_bytes(16)
print(json.dumps({"username": args.username, "id": args.username, "role": args.role,
 "salt": base64.b64encode(salt).decode(),
 "hash": base64.b64encode(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)).decode()}))
