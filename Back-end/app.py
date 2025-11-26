# app.py antonio
import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import date, time

from Modelo import Pacientes, Medicos, Consultas, Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET", "chave-top-secreta")
CORS(app, supports_credentials=True)

# SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

# ---------- Helpers ----------
def get_db():
    return SessionLocal()

def paciente_by_email(db, email):
    return db.query(Pacientes).filter_by(email=email).first()

def paciente_by_id(db, pid):
    return db.query(Pacientes).filter_by(id=pid).first()

# ---------------- HTML PAGES ----------------
def logged_context():
    return {"logado": "usuario" in session, "usuario": session.get("usuario")}

@app.get("/")
def pagina_home():
    return render_template("index.html", **logged_context())

@app.get("/page/cadastro")
def pagina_cadastro():
    return render_template("cadastro.html", **logged_context())

@app.get("/page/consultas")
def pagina_consultas():
    return render_template("consultas.html", **logged_context())

@app.get("/page/agendar")
def pagina_agendamento():
    return render_template("agendamento.html", **logged_context())

@app.get("/page/login")
def pagina_login():
    return render_template("login.html", **logged_context())

# ---------------- LOGIN (API) ----------------
@app.post("/login")
def fazer_login():
    data = request.get_json(silent=True) or request.form
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    with get_db() as db:
        user = db.query(Pacientes).filter_by(email=email).first()
        if not user or user.senha != senha:
            return jsonify({"erro": "Credenciais inválidas"}), 401

        session.permanent = True
        session["usuario"] = user.nome
        session["usuario_id"] = user.id

        return jsonify({"mensagem": "Login OK", "nome": user.nome}), 200

@app.post("/logout")
def fazer_logout():
    session.clear()
    return jsonify({"mensagem": "Logout OK"}), 200

# ---------------- PACIENTES ----------------
@app.post("/pacientes")
def criar_paciente():
    data = request.get_json(silent=True) or request.form
    required = ["nome", "email", "senha"]
    for k in required:
        if not data.get(k):
            return jsonify({"erro": f"{k} é obrigatório"}), 400

    with get_db() as db:
        if db.query(Pacientes).filter_by(email=data["email"]).first():
            return jsonify({"erro": "Email já cadastrado"}), 400

        # data_nascimento opcional
        data_nascimento = data.get("data_nascimento")
        if data_nascimento:
            try:
                data_nascimento = date.fromisoformat(data_nascimento)
            except:
                return jsonify({"erro": "data_nascimento inválida"}), 400
        else:
            data_nascimento = None

        novo = Pacientes(
            nome=data["nome"],
            data_nascimento=data_nascimento,
            telefone=data.get("telefone"),
            email=data["email"],
            senha=data["senha"]  # 🔥 sem hashing
        )

        db.add(novo)
        db.commit()
        db.refresh(novo)

        return jsonify({"mensagem": "Cadastro concluído!", "id": novo.id}), 201

# ---------------- CONSULTAS (API) ----------------
@app.get("/consultas")
def listar_consultas():
    with get_db() as db:
        if "usuario_id" in session:
            consultas = db.query(Consultas).filter(Consultas.id_paciente == session["usuario_id"]).all()
        else:
            consultas = db.query(Consultas).all()

        resultado = []
        for c in consultas:
            resultado.append({
                "id": c.id,
                "data": c.data.isoformat(),
                "horario": c.horario.isoformat(),
                "medico": c.medico.nome if c.medico else None,
                "paciente": c.paciente.nome if c.paciente else None,
                "id_medico": c.id_medico,
                "id_paciente": c.id_paciente,
                "mensagem": c.mensagem
            })
        return jsonify(resultado), 200

@app.post("/agendamento")
def criar_consulta():
    data = request.get_json(silent=True) or request.form
    if not data:
        return jsonify({"erro": "JSON inválido"}), 400

    try:
        id_medico = int(data.get("medico") or data.get("id_medico"))
    except:
        return jsonify({"erro": "id_medico inválido"}), 400

    with get_db() as db:
        paciente = None
        email = data.get("email")

        if email:
            paciente = paciente_by_email(db, email)
        if not paciente and "usuario_id" in session:
            paciente = paciente_by_id(db, session["usuario_id"])

        if not paciente:
            nome = data.get("nome") or "Paciente"
            novo = Pacientes(
                nome=nome,
                email=email or f"temp_{nome}_{id_medico}@local",
                senha="senha-temporaria"   # 🔥 sem hash também
            )
            db.add(novo)
            db.commit()
            db.refresh(novo)
            paciente = novo

        try:
            data_consulta = date.fromisoformat(data.get("data"))
        except:
            return jsonify({"erro": "data inválida"}), 400

        if data_consulta < date.today():
            return jsonify({"erro": "Não é permitido agendar no passado"}), 400

        try:
            horario_obj = time.fromisoformat(data.get("horario"))
        except:
            return jsonify({"erro": "horário inválido"}), 400

        conflito = db.query(Consultas).filter(
            and_(
                Consultas.id_medico == id_medico,
                Consultas.data == data_consulta,
                Consultas.horario == horario_obj
            )
        ).first()

        if conflito:
            return jsonify({"erro": "Horário ocupado!"}), 400

        nova = Consultas(
            id_medico=id_medico,
            id_paciente=paciente.id,
            data=data_consulta,
            horario=horario_obj,
            mensagem=data.get("mensagem")
        )
        db.add(nova)
        db.commit()
        db.refresh(nova)

        return jsonify({"id": nova.id}), 201

@app.delete("/agendamento/<int:id>")
def deletar_consulta(id):
    with get_db() as db:
        consulta = db.query(Consultas).filter_by(id=id).first()
        if not consulta:
            return jsonify({"erro": "Consulta não encontrada"}), 404

        if "usuario_id" in session and consulta.id_paciente != session["usuario_id"]:
            return jsonify({"erro": "Permissão negada"}), 403

        db.delete(consulta)
        db.commit()
        return jsonify({"mensagem": "Consulta cancelada"}), 200

@app.get("/medicos")
def listar_medicos():
    with get_db() as db:
        medicos = db.query(Medicos).all()
        return jsonify([{"id": m.id, "nome": m.nome, "especialidade": m.especialidade} for m in medicos]), 200

if __name__ == "__main__":
    with get_db() as db:
        if db.query(Medicos).count() == 0:
            db.add_all([
                Medicos(nome="Dra. Ana Silva", especialidade="Clínica Geral"),
                Medicos(nome="Dr. Carlos Mendes", especialidade="Cardiologia"),
                Medicos(nome="Dr. João Ribeiro", especialidade="Pediatria"),
            ])
            db.commit()

    app.run(debug=True)
