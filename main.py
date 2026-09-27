"""FastAPI app with a Streamlit dashboard mounted at /dashboard.

Run with:
    uvicorn main:app --reload

Then open:
    http://127.0.0.1:8000/dashboard/   Streamlit UI
    http://127.0.0.1:8000/docs         FastAPI Swagger UI
    http://127.0.0.1:8000/api/tasks    JSON API
"""

import streamlit as st
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

import store

# st.App is the ASGI entry point added in Streamlit 1.53 (experimental).
streamlit_app = st.App("dashboard.py")

# Hand the Streamlit runtime lifecycle to FastAPI. Mounted sub-apps don't
# receive ASGI lifespan events, so without this Streamlit would start lazily
# on the first request.
app = FastAPI(title="Tasks API", lifespan=streamlit_app.lifespan())


class TaskIn(BaseModel):
    title: str


class TaskPatch(BaseModel):
    done: bool


@app.get("/api/tasks", response_model=list[store.Task])
async def get_tasks():
    return store.list_tasks()


@app.post("/api/tasks", response_model=store.Task, status_code=201)
async def create_task(body: TaskIn):
    return store.add_task(body.title)


@app.patch("/api/tasks/{task_id}", response_model=store.Task)
async def update_task(task_id: int, body: TaskPatch):
    task = store.set_done(task_id, body.done)
    if task is None:
        raise HTTPException(404, "Task not found")
    return task


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/dashboard/")


# Mount last so the /api routes above take precedence.
app.mount("/dashboard", streamlit_app)
