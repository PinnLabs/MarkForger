from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello_world():
    return "Hey, everyone!"
