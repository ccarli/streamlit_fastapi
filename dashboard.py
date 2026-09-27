"""Streamlit dashboard served by FastAPI (see main.py).

Shows two ways to reach the same data:
- directly, by importing the shared `store` module (same process);
- over HTTP, by calling the FastAPI routes with an async client, using the
  async caching added in Streamlit 1.64.
"""

import asyncio
import time

import httpx
import streamlit as st

import store

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Tasks", page_icon="✅")
st.title("Tasks dashboard")
st.caption("Streamlit mounted inside FastAPI at `/dashboard`, API at `/api`.")

# --- Direct access: same process, same objects -----------------------------

st.subheader("Tasks (read directly from the shared store)")

with st.form("new_task", clear_on_submit=True):
    title = st.text_input("New task")
    if st.form_submit_button("Add") and title.strip():
        store.add_task(title.strip())

for task in store.list_tasks():
    checked = st.checkbox(task.title, value=task.done, key=f"task-{task.id}")
    if checked != task.done:
        store.set_done(task.id, checked)

st.info(
    "Tasks created with `POST /api/tasks` (try it from `/docs`) show up here "
    "on the next rerun, since the API and the dashboard share the store."
)

# --- Over HTTP: async client + cached coroutines (Streamlit 1.64) ----------

st.subheader("Same data, fetched over HTTP with async caching")


@st.cache_data(ttl="10s")
async def fetch(_client: httpx.AsyncClient, path: str) -> dict | list:
    # The leading underscore tells Streamlit not to hash the client, so the
    # cache key is just `path`. On a cache hit this body never runs.
    await asyncio.sleep(0.5)  # simulate a slow endpoint
    response = await _client.get(path)
    response.raise_for_status()
    return response.json()


async def fetch_all() -> list:
    # A new client per run: st.cache_resource is shared across sessions, while
    # each session has its own event loop, so a cached async client would stay
    # bound to the loop of whichever session created it.
    async with httpx.AsyncClient(base_url=API_URL, timeout=5) as client:
        return await asyncio.gather(fetch(client, "/api/health"), fetch(client, "/api/tasks"))


if st.button("Fetch from API"):
    start = time.perf_counter()
    health, tasks = asyncio.run(fetch_all())
    elapsed = time.perf_counter() - start
    st.write(f"Health: `{health['status']}` in {elapsed:.2f}s")
    st.caption(
        "About 0.5s on a cold cache (the two calls run concurrently), "
        "near 0s when served from the cache within 10s."
    )
    st.dataframe(tasks, width="stretch")
