from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from database import engine, init_db
from models import User, Message
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

init_db()

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/init_user")
def init_user(username: str, role: str, session: Session = Depends(get_session)):
    user = User(username=username, role=role)
    session.add(user)
    session.commit()
    return {"message": f"Usuario {username} creado con rol {role}"}

@app.post("/ask")
def ask(username: str, message: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Eres un experto en {user.role}."},
                  {"role": "user", "content": message}]
    )

    answer = response["choices"][0]["message"]["content"]
    
    msg = Message(username=username, question=message, response=answer)
    session.add(msg)
    session.commit()
    
    return {"response": answer}

@app.get("/history/{username}")
def get_history(username: str, session: Session = Depends(get_session)):
    messages = session.exec(select(Message).where(Message.username == username)).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No hay historial para este usuario")
    return messages

@app.get("/health")
def health_check():
    return {"status": "OK"}