import json
import string
import random
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
import motor.motor_asyncio
from fastapi import FastAPI, HTTPException, Request, Form

app = FastAPI()
db_client = motor.motor_asyncio.AsyncIOMotorClient('localhost', 27017, username="root", password="example")
app_db = db_client["url_shortener"]
collection = app_db["url_shortener"]
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def shorten_url(long_url: str = Form(...)):
    short_url = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    await collection.insert_one({
        "short_url": short_url,
        "long_url": long_url,
        "clicks": 0
    })
    return {"short_url": f"http://localhost:8000/{short_url}"}


@app.get("/{short_url}")
async def redirect_url(short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    if collection_data is None:
        raise HTTPException(status_code=404, detail="URL not found")

    long_url = collection_data.get("long_url")
    if not long_url:
        raise HTTPException(status_code=404, detail="Long URL not found")

    await collection.update_one({"short_url": short_url}, {"$inc": {"clicks": 1}})

    return RedirectResponse(long_url)


@app.get("/{short_url}/edit")
async def edit_url(request: Request, short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    if collection_data is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return templates.TemplateResponse(request=request, name="edit.html", context={"url_data": collection_data})


@app.post("/{short_url}/edit")
async def edit_url(request: Request, short_url: str, long_url: str = Form(...)):
    result = await collection.update_one(
        {"short_url": short_url},
        {"$set": {"long_url": long_url}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="URL not found or no changes made")
    return RedirectResponse(url=f"/{short_url}/edit", status_code=303)
