from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.database import create_tables
from backend.routes import router
from backend.auth import get_current_user_optional

app = FastAPI(title="Leitura Bíblica", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Include API routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


# ── PAGE ROUTES ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/app")
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/cadastro", response_class=HTMLResponse)
def cadastro(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/app")
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})


@app.get("/app", response_class=HTMLResponse)
def app_page(request: Request, user=Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("app.html", {"request": request, "user": user})
