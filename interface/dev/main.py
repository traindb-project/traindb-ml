from typing import Union
from fastapi import FastAPI

app = FastAPI()

@app.post("/train/{model}")
def aqp_create(model: str):
    return {"Created": model, "Status": "OK"}

@app.get("/estimate/{sql}")
def aqp_read(sql: str):
    value = 100
    return {"Query": sql, "Estimated Value": value}

@app.put("/update/{sql}")
def aqp_update(sql: str):
    return {"Query": sql, "Updated" : "OK"}

@app.post("/delete/{model}")
def aqp_create(model: str):
    return {"Deleted": model, "Status": "OK"}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

"""
@app.on_event("shutdown")
def shutdown_event():
    with open("log.txt", mode="a") as log:
        log.write("Application shutdown")
    return 

@app.on_event("startup")
def startup_event():
    with open("log.txt", mode="a") as log:
        log.write("Application startup")
"""
