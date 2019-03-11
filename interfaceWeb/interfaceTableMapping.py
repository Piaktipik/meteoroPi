from sqlalchemy import Column, Integer, create_engine, Text, String, Boolean, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Objetos(Base):
    __tablename__ = 'Objetos'
    id =                        Column(Integer, primary_key=True)
    NombreObjeto =              Column(String(50), nullable=False)
    NombreObjetoPadreObjeto =   Column(String(50), nullable=False)
    Activo =                    Column(Boolean, nullable=False)
    DireccionTx =               Column(String(20), nullable=True)
    DireccionRx =               Column(String(20), nullable=True)
    FormaObjetoJson =           Column(Text, nullable=True)


class Funciones(Base):
    __tablename__ = 'Funciones'
    id =                        Column(Integer, primary_key=True)
    NombreFuncion =             Column(String(50), nullable=False)
    NombreObjetoPadreFuncion =  Column(Integer, ForeignKey("Objetos.id"), nullable=False)


class Variables(Base):
    __tablename__ = "Variables"
    id =                        Column(Integer, primary_key=True)
    NombreVariable =            Column(String(50), nullable=False)
    NombreObjetoPadreVariable = Column(Integer, ForeignKey("Objetos.id"), nullable=False)
    EstadoVariable =            Column(Boolean, nullable=False)

engine = create_engine('sqlite:///Interface.db')


Base.metadata.create_all(engine)
