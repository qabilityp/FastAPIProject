import json
import string
import random
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from fastapi import FastAPI, HTTPException, Request, Form

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def shorten_url(long_url: str = Form(...)):
    short_url = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    try:
        with open('urls.json', "r", encoding="utf-8") as f:
            urls = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        urls = {}

    urls[short_url] = long_url

    with open('urls.json', "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=4)

    return {"short_url": f"http://localhost:8000/{short_url}"}


@app.get("/{short_url}")
async def redirect_url(short_url: str):
    with open('urls.json', "r", encoding="utf-8") as f:
        redirect_urls = json.loads(f.read()).get(short_url)
    if not redirect_urls:
        raise HTTPException(status_code=404)
    else:
        return RedirectResponse(redirect_urls)
