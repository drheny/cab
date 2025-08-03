from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Medical Cabinet Backend Test",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "mongo_url_set": bool(os.environ.get("MONGO_URL")),
            "emergent_key_set": bool(os.environ.get("EMERGENT_LLM_KEY"))
        }
    }

@app.get("/api/test")
def api_test():
    return {"api": "working", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
