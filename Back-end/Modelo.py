from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, Date, Time,ForeignKey, create_engine
import os
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, fast_executemany=True)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# MODELS --------------------------------------------------

class Medicos(Base):
    __tablename__ = "medicos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    especialidade = Column(String(100), nullable=False)
    telefone = Column(String(20))
    email = Column(String(100))
    consultas = relationship("Consultas", back_populates="medico")

class Pacientes(Base):
    __tablename__ = "pacientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    telefone = Column(String(20))
    email = Column(String(100), unique=True)
    consultas = relationship("Consultas", back_populates="paciente")
    senha = Column(String(255), nullable=False)
class Consultas(Base):
    __tablename__ = "consultas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    horario = Column(Time, nullable=False)
    mensagem = Column(String(255))
    id_medico = Column(Integer, ForeignKey("medicos.id"))
    id_paciente = Column(Integer, ForeignKey("pacientes.id"))

    medico = relationship("Medicos", back_populates="consultas")
    paciente = relationship("Pacientes", back_populates="consultas")

Base.metadata.create_all(engine)

with Session(engine) as session:
    medicos = [
        Medicos(nome="Dra. Ana Silva", especialidade="Clínica Geral", telefone="(11) 98765-1234", email="ana.silva@hospital.com"),
        Medicos(nome="Dr. Carlos Mendes", especialidade="Cardiologia", telefone="(21) 98877-2233", email="carlos.mendes@hospital.com"),
        Medicos(nome="Dr. João Ribeiro", especialidade="Pediatria", telefone="(31) 97766-3344", email="joao.ribeiro@hospital.com"),
        Medicos(nome="Dra. Fernanda Costa", especialidade="Dermatologia", telefone="(41) 96655-4455", email="fernanda.costa@hospital.com"),
        Medicos(nome="Dr. Ricardo Lima", especialidade="Ortopedia", telefone="(51) 95544-5566", email="ricardo.lima@hospital.com"),
        Medicos(nome="Dra. Mariana Alves", especialidade="Ginecologia", telefone="(61) 94433-6677", email="mariana.alves@hospital.com"),
        Medicos(nome="Dr. Pedro Santos", especialidade="Neurologia", telefone="(71) 93322-7788", email="pedro.santos@hospital.com"),
        Medicos(nome="Dra. Luiza Martins", especialidade="Endocrinologia", telefone="(81) 92211-8899", email="luiza.martins@hospital.com"),
        Medicos(nome="Dr. Felipe Torres", especialidade="Urologia", telefone="(91) 91100-9900", email="felipe.torres@hospital.com"),
        Medicos(nome="Dra. Beatriz Rocha", especialidade="Oftalmologia", telefone="(85) 90099-1122", email="beatriz.rocha@hospital.com"),
    ]
    session.add_all(medicos)
    session.commit()
    print("✅ 10 médicos inseridos com sucesso!")
