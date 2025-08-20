from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

@app.get("/")
def index():
    return FileResponse("web/index.html")

@app.get("/{file_path}")
def static_files(file_path: str):
    return FileResponse(f"web/{file_path}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
