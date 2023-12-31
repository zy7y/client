from typing import List

from fastapi import FastAPI, Form, UploadFile, File
from pydantic import BaseModel

app = FastAPI()


@app.get("/get-params")
def get_params(name: str):
    """GET 请求查询参数"""
    return name


@app.get("/get-form")
def get_form(name: str = Form(...)):
    """GET 请求表单"""
    return name


class Info(BaseModel):
    name: str


@app.post("/post-json")
def post_json(data: Info):
    return data


@app.post("/post-form")
def post_form(name: str = Form(...), ages: List[str] = Form(...)):
    return ages


@app.post("/post-file")
def post_file(name: UploadFile = File(...)):
    return name.filename


@app.post("/post-files")
def post_files(files: List[UploadFile] = File(...)):
    return len(files)


@app.post("/post-form-file")
def post_form_file(name: str = Form(...), ages: List[str] = Form(...), file: UploadFile = File(...)):
    return file.filename


"""
gunicorn server:app  --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002 -D 
"""
