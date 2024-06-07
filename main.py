from fastapi import FastAPI,Depends,HTTPException
from sqlalchemy import text

from src.routes import contacts
from src.database.db import AsyncSession,get_db

app = FastAPI()

app.include_router(contacts.router, prefix="/api")

@app.get("/")
async def index():
    return {"message": "Hello World"}


@app.get("/api/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    try:
        # Make request
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
