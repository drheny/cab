from fastapi import FastAPI

# Initialize FastAPI app
app = FastAPI(title="Test API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Test API working"}

@app.get("/api/test")
async def test():
    return {"message": "Test endpoint working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)