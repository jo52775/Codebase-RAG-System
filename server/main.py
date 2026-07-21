from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.CodeBlock import CodeBlock
app = FastAPI()

@app.get("/")
def read_root(db:Session = Depends(get_db)):
    print('DATABASE OBJECT: ', db)
    return {"Hello": "World?"}