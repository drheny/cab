#!/usr/bin/env python3

import uvicorn
from server import app

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=False,  # Disable reload to avoid file watching issues
        access_log=True
    )