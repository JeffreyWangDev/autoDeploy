
import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
import secrets
import hashlib
import time 
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse
import requests
from fastapi.exceptions import HTTPException
from fastapi import FastAPI
from backend import *
create_database_table()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

TOKEN_SECRET = secrets.token_hex(32) 
TOKEN_EXPIRE_SECONDS = 30 * 60 

active_tokens = {} 

config = Config(".env")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
GITHUB_CLIENT_ID = config("GITHUB_CLIENT_ID") 
GITHUB_CLIENT_SECRET = config("GITHUB_CLIENT_SECRET") 


def create_token(username):
    """Creates a new token for the given username."""
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(f"{TOKEN_SECRET}{token}".encode()).hexdigest()
    active_tokens[hashed_token] = {
        "username": username,
        "expires_at": time.time() + TOKEN_EXPIRE_SECONDS,
    }
    return hashed_token


def validate_token(token):
    """Validates a token, checking if it's active and not expired."""
    if token in active_tokens:
        if active_tokens[token]["expires_at"] > time.time():
            return active_tokens[token]["username"]
        else:
            del active_tokens[token] 
    return None


def get_current_user(request: Request):
    """Gets the current user based on the token in the request."""
    token = request.cookies.get("access_token") 
    if token:
        username = validate_token(token)
        if username:
            return username
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authentication required")

@app.get("/auth/login")
async def github_login(request: Request):
    """Initiates the GitHub OAuth2 flow."""
    url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user"
    return RedirectResponse(url=url)


@app.get("/auth/callback")
async def github_callback(request: Request, code: str):
    """Handles the GitHub OAuth2 callback."""

    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }
    response = requests.post("https://github.com/login/oauth/access_token", data=data, headers={"Accept": "application/json"})

    if response.status_code == 200:
        access_token = response.json()["access_token"]

        headers = {"Authorization": f"token {access_token}"}
        user_response = requests.get("https://api.github.com/user", headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data["login"]

            token = create_token(username)

            response = RedirectResponse(url="/", status_code=303)
            response.set_cookie(key="access_token", value=token, httponly=True)
            return response
        else:
            raise HTTPException(status_code=400, detail="Error fetching user information")
    else:
        raise HTTPException(status_code=400, detail="Error exchanging code for access token")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    conn = sqlite3.connect("server_deployments.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deployments")
    deployments = cursor.fetchall()
    conn.close()
    user = None
    try:
        user = get_current_user(request)
        if user.lower() != "jeffreywangdev":
            user = None
    except:
        pass
    return templates.TemplateResponse("index.html", {"request": request, "deployments": deployments, "user": user})

@app.post("/deploy", response_class=JSONResponse)
async def deploy_server(request: Request, current_user: str = Depends(get_current_user)):
    allowed_users = ["jeffreywangdev"] 
    if current_user.lower() in allowed_users:
        form_data = await request.form()
        image_link = form_data.get("image_link")
        name = form_data.get("name")
        extra_flags = form_data.get("extra_flags")

        if deploy_new_server(image_link, name, extra_flags):
            return JSONResponse({"message": "Server deployed successfully!"})
        else:
            raise HTTPException(status_code=500, detail="Server deployment failed.")
    else:
        raise HTTPException(status_code=403, detail="You are not authorized to deploy servers")


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
    response.delete_cookie(key="access_token") 
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
