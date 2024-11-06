import subprocess
import re
import sqlite3
import docker
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
from typing import List, Optional
import secrets
import hashlib  # For hashing tokens
import time  # For token expiration
from fastapi.security import HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security import OAuth2
from fastapi.templating import Jinja2Templates
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse
from typing import Optional
import requests
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, Form
from backend import *
# ... (Your existing functions: create_database_table, get_open_port, 
#      register_subdomain, run_docker_container, deploy_new_server,
#      remove_server, stop_server, start_server) ...

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Create a 'templates' directory

# Token settings
TOKEN_SECRET = secrets.token_hex(32)  # Replace with a strong secret key
TOKEN_EXPIRE_SECONDS = 30 * 60  # 30 minutes

# Store active tokens in a dictionary (replace with a database in a real app)
active_tokens = {} 

# Github OAuth2 settings
config = Config(".env")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID")  # Replace with your GitHub Client ID
GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET")  # Replace with your GitHub Client Secret

# --- User Authentication ---
def authenticate_user(credentials: HTTPBasicCredentials):
    """Verifies username/password (replace with database check in a real app)."""
    correct_username = "admin"  # Replace with actual admin username
    correct_password = "password"  # Replace with actual admin password

    if credentials.username == correct_username and credentials.password == correct_password:
        return True
    return False


def create_token(username):
    """Creates a new token for the given username."""
    token = secrets.token_urlsafe(32)  # Generate a random token
    hashed_token = hashlib.sha256(f"{TOKEN_SECRET}{token}".encode()).hexdigest()
    active_tokens[hashed_token] = {
        "username": username,
        "expires_at": time.time() + TOKEN_EXPIRE_SECONDS,  # Set expiration time
    }
    return hashed_token


def validate_token(token):
    """Validates a token, checking if it's active and not expired."""
    if token in active_tokens:
        if active_tokens[token]["expires_at"] > time.time():
            return active_tokens[token]["username"]
        else:
            del active_tokens[token]  # Remove expired token
    return None


def get_current_user(request: Request):
    """Gets the current user based on the token in the request."""
    token = request.cookies.get("access_token")  # Read from cookie
    if token:
        username = validate_token(token)
        if username:
            return username
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authentication required")

# --- End User Authentication ---

# --- Github OAuth2 ---
@app.get("/auth/login")
async def github_login(request: Request):
    """Initiates the GitHub OAuth2 flow."""
    url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return RedirectResponse(url=url)


@app.get("/auth/callback")
async def github_callback(request: Request, code: str):
    """Handles the GitHub OAuth2 callback."""

    # Exchange the code for an access token
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }
    response = requests.post("https://github.com/login/oauth/access_token", data=data, headers={"Accept": "application/json"})

    if response.status_code == 200:
        access_token = response.json()["access_token"]

        # Get user information using the access token
        headers = {"Authorization": f"token {access_token}"}
        user_response = requests.get("https://api.github.com/user", headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data["login"]  # You can use other user data as needed
            if username.lower() !="jeffreywangdev":
                raise HTTPException(status_code=401, detail="You are not authorized to access this page")
            # Generate a custom token (replace with a secure token generation strategy)
            token = create_token(username)

            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="access_token", value=token, httponly=True)
            return response
        else:
            raise HTTPException(status_code=400, detail="Error fetching user information")
    else:
        raise HTTPException(status_code=400, detail="Error exchanging code for access token")

# --- End Github OAuth2 ---

# --- FastAPI Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, current_user: str = Depends(get_current_user)):
    conn = sqlite3.connect("server_deployments.db")  # Replace with your DB path if needed
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deployments")
    deployments = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "deployments": deployments, "user": current_user})

@app.post("/deploy", response_class=JSONResponse)
async def deploy_server(request: Request, current_user: str = Depends(get_current_user)):
    form_data = await request.form()
    image_link = form_data.get("image_link")
    main_domain = form_data.get("main_domain") 
    name = form_data.get("name")
    extra_flags = form_data.get("extra_flags").split() # Split flags into a list

    if deploy_new_server(image_link, main_domain, name, extra_flags):
        return JSONResponse({"message": "Server deployed successfully!"})
    else:
        raise HTTPException(status_code=500, detail="Server deployment failed.")


@app.post("/remove/{name}", response_class=RedirectResponse)
async def remove_server_route(name: str, request: Request, current_user: str = Depends(get_current_user)):
    if remove_server(name):
        return RedirectResponse(url="/", status_code=303)
    else:
        raise HTTPException(status_code=500, detail=f"Failed to remove server '{name}'.")


@app.post("/stop/{name}", response_class=RedirectResponse)
async def stop_server_route(name: str,  request: Request, current_user: str = Depends(get_current_user)):
    if stop_server(name):
        return RedirectResponse(url="/", status_code=303)
    else:
        raise HTTPException(status_code=500, detail=f"Failed to stop server '{name}'.")


@app.post("/start/{name}", response_class=RedirectResponse)
async def start_server_route(name: str, request: Request, current_user: str = Depends(get_current_user)):
    if start_server(name):
         return RedirectResponse(url="/", status_code=303)
    else:
        raise HTTPException(status_code=500, detail=f"Failed to start server '{name}'.")

@app.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")  # Delete the cookie
    return response

# --- End FastAPI Routes ---

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)