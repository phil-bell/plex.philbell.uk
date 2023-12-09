import os
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from qbittorrent import Client
from the_python_bay import tpb

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
QB_USERNAME = os.environ.get("QB_USERNAME")
QB_PASSWORD = os.environ.get("QB_PASSWORD")
QB_URL = os.environ.get("QB_URL")

app = FastAPI()

security = HTTPBasic()

templates = Jinja2Templates(directory="templates")


def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = USERNAME.encode()
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = PASSWORD.encode()
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def qb_client() -> Client:
    qb = Client(QB_URL)
    qb.login(QB_USERNAME, QB_PASSWORD)
    return qb


@app.get("/")
def root(request: Request, username: Annotated[str, Depends(get_current_username)]):
    return templates.TemplateResponse(
        "index.html", {"request": request, "username": username}
    )


@app.post("/search/")
def search(
    request: Request,
    username: Annotated[str, Depends(get_current_username)],
    search: str = Form(),
):
    torrents = tpb.search(search)

    return templates.TemplateResponse(
        "results.html", {"request": request, "torrents": torrents, username: username}
    )


@app.post("/add/")
def add(
    request: Request,
    username: Annotated[str, Depends(get_current_username)],
    magnet: str = Form(),
    location: str = Form(),
):
    qb = qb_client()
    qb.download_from_link(
        magnet,
        savepath=location,
    )
    return templates.TemplateResponse(
        "success.html", {"request": request, username: username}
    )
