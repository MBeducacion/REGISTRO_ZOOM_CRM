import streamlit as st
from sqlalchemy import text
import time
import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy import create_engine, text
import pandas as pd
from streamlit_javascript import st_javascript



# --- 1. CAPTURAR EL CURSO DINÁMICAMENTE ---
# Esto lee el slug de la URL, ej: mbeducacion.app/?curso=clase-lunes
query_params = st.query_params
curso_slug = query_params.get("curso", "webinar-general")

# --- 2. CONFIGURACIÓN DE LA BASE DE DATOS ---
try:
    creds = st.secrets["db_credentials"]
    engine = create_engine(
        f"mysql+pymysql://{creds['user']}:{creds['pass']}@{creds['host']}/{creds['name']}",
        pool_pre_ping=True
    )
    conexion_db_exitosa = True
except Exception as e:
    st.error(f"Error de configuración de base de datos: {e}")
    conexion_db_exitosa = False
    engine = None

# --- 3. CARGAR DATOS DEL EVENTO DESDE EL CRM ---
ID_REUNION = curso_slug
NOMBRE_EVENTO = "Cargando evento..."
LINK_ZOOM = ""
LINK_YOUTUBE = ""
CUPO_MAXIMO = 100

if conexion_db_exitosa and engine:
    try:
        with engine.connect() as conn:
            # Buscamos los datos que guardó el CRM
            result = conn.execute(
                text("SELECT titulo_curso, link_zoom, link_youtube FROM agenda_cursos WHERE slug = :s"), 
                {"s": curso_slug}
            ).fetchone()
            
            if result:
                NOMBRE_EVENTO = result[0]
                LINK_ZOOM = result[1]
                LINK_YOUTUBE = result[2] if result[2] else "https://youtube.com/@mbeducacion/live"
            else:
                st.error("⚠️ El enlace del curso es inválido o el evento no existe.")
                st.stop()
    except Exception as e:
        st.error(f"Error al consultar la agenda: {e}")

# --- 4. VERIFICAR REGISTRO PREVIO (localStorage) ---
registro_previo = None
try:
    registro_previo = st_javascript(f"localStorage.getItem('mbeducacion_registro_{ID_REUNION}');")
except:
    pass

# --- 5. LÓGICA DE CUPOS ---
conteo_actual = 0
if conexion_db_exitosa and engine:
    try:
        with engine.connect() as conn:
            res_conteo = conn.execute(
                text("SELECT COUNT(*) FROM directorio_tratamiento WHERE canal_autorizacion LIKE :filtro"), 
                {"filtro": f"%{ID_REUNION}%"}
            )
            conteo_actual = res_conteo.scalar()
    except:
        conteo_actual = 0

if conteo_actual >= CUPO_MAXIMO:
    link_destino = LINK_YOUTUBE
    mensaje_cupo = "⚠️ ¡Sala de Zoom llena! Podrás ver la transmisión por YouTube."
else:
    link_destino = LINK_ZOOM
    mensaje_cupo = "✨ Tienes un cupo reservado en la sala de Zoom."

# --- VISTA USUARIOS REGISTRADOS ---
if registro_previo == "true":
    st.title(NOMBRE_EVENTO)
    st.success(f"✨ ¡Bienvenido de nuevo! Ya estás registrado.")
    st.info(mensaje_cupo)
    
    st.markdown(f"""
        <a href="{link_destino}" target="_blank" style="
            text-decoration: none; background-color: #2D8CFF; color: white;
            padding: 15px 25px; border-radius: 10px; font-weight: bold;
            display: inline-block; text-align: center; width: 100%;
        ">🚀 INGRESAR A LA SESIÓN</a>
    """, unsafe_allow_html=True)
    
    if st.button("No soy yo / Registrar nuevos datos"):
        st_javascript(f"localStorage.removeItem('mbeducacion_registro_{ID_REUNION}');")
        st.rerun()
    st.stop()

# --- FORMULARIO DE REGISTRO (HABEAS DATA) ---
st.title("Registro de Asistencia")
st.subheader(f"Bienvenido al {NOMBRE_EVENTO}")

with st.form("registro_publico", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo *")
    col1, col2 = st.columns([1, 2])
    with col1: tipo_doc = st.selectbox("Tipo Doc *", ["C.C.", "NIT", "C.E.", "Otro"])
    with col2: doc_identidad = st.text_input("Número de Documento *")
    
    institucion = st.text_input("Institución / Empresa *")
    rol_cargo = st.text_input("Cargo *")
    email = st.text_input("Correo Electrónico *")
    
    st.markdown("---")
    st.write("🔒 **Autorización de Tratamiento de Datos**")
    with st.expander("Leer Autorización de Tratamiento de Datos"):
        st.write("MB EDUCACIÓN - AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES
        
        De conformidad con la legislación legal vigente y la Política de Tratamiento de Datos Personales de MB Educación, el tratamiento de los datos que se reportan en este Formulario se regirá por las siguientes condiciones:
        a) Yo, al diligenciar este Formulario, concedo autorización previa, expresa e informada a MB Educación, para el tratamiento de los datos que suministro, sabiendo que he sido informado que la finalidad de dichos datos es adquirir un producto o solicitar un servicio que ella ofrece ahora o en el futuro, de tal manera que puedan tramitar mi solicitud adecuadamente, contactarme en caso de que se requiera y adelantar todas las acciones para el logro del particular.
        b) Conozco y acepto que esta información será tratada de acuerdo con la Política de Tratamiento de Datos Personales de MB Educación disponible en su página Web, que declaro haber leído y conocer, en especial en lo referente a mis derechos y a los procedimientos con que la Entidad cuenta, para hacerlos efectivos ante sus autoridades.
        c) Se que los siguientes son los derechos básicos que tengo como titular de los datos que se han diligenciado en este Formulario: 1) Todos los datos registrados en este Formulario sólo serán empleados por MB Educación para cumplir la finalidad expuesta en el punto (a) del presente Aviso; 2) En cualquier momento, puedo solicitar una consulta de la información con que MB Educación cuenta sobre mí, dirigiéndome al Oficial de Protección de Datos Personales de la Entidad; 3) MB Educación velará por la confidencialidad y privacidad de los datos personales de los titulares que están siendo reportados, según las disposiciones legales vigentes; 4) En cualquier momento puedo solicitar una prueba de esta autorización.
        d) El Oficial de Protección de Datos Personales de la Entidad, ante quien puedo ejercer mis derechos, de forma gratuita, lo contactar en la siguiente dirección electrónica: usodedatos@mbeducacion.com.co")

    acepta = st.checkbox("He leído y autorizo el tratamiento de mis datos personales *")
    acepta_promos = st.checkbox("Acepto recibir información de Cursos y promociones de MB Educación")
    
    boton_registro = st.form_submit_button("REGISTRARME E INGRESAR")

# --- LÓGICA DE GUARDADO ---
if boton_registro:
    if not all([nombre, doc_identidad, institucion, rol_cargo, email, acepta]):
        st.error("⚠️ Por favor completa todos los campos obligatorios.")
    else:
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO directorio_tratamiento 
                    (contacto_nombre, tipo_documento, documento_identidad, institucion, rol_cargo, email, habeas_data, autoriza_env_info, canal_autorizacion) 
                    VALUES (:nom, :tdoc, :doc, :inst, :rol, :mail, :hab, :env_info, :cnal)
                """), {
                    "nom": nombre, "tdoc": tipo_doc, "doc": doc_identidad, 
                    "inst": institucion, "rol": rol_cargo, "mail": email,
                    "hab": 1, "env_info": 1 if acepta_promos else 0,
                    "cnal": f"CRM - {ID_REUNION} - {time.strftime('%d/%m/%Y')}"
                })
            
            st_javascript(f"localStorage.setItem('mbeducacion_registro_{ID_REUNION}', 'true');")
            st.success("✅ ¡Registro exitoso!")
            time.sleep(2)
            st.markdown(f'<meta http-equiv="refresh" content="0; url={link_destino}">', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
