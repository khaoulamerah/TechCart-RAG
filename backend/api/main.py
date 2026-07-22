from fastapi import FastAPI

app = FastAPI(
    title="TechCart API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "TechCart Backend is running!"}