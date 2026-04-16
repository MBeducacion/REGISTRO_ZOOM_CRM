import streamlit as st
from sqlalchemy import create_engine, text
import time
import pandas as pd
from streamlit_javascript import st_javascript

# --- 1. CONFIGURACIÓN DE LA BASE DE DATOS ---
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

# --- 2. CAPTURA DEL EVENTO DINÁMICO ---
slug_url = st.query_params.get("curso")

if not slug_url:
    st.error("⚠️ Enlace no válido. Por favor, utiliza el link oficial de MB Educación.")
    st.stop()

# --- 3. BUSCAR INFORMACIÓN DEL EVENTO ---
@st.cache_data(ttl=30) # Reducimos a 30 seg para mayor precisión en cupos
def obtener_datos_evento(slug):
    if not engine: return None
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM agenda_cursos WHERE slug = :s AND estado = 'activo'")
            return conn.execute(query, {"s": slug}).fetchone()
    except:
        return None

evento = obtener_datos_evento(slug_url)

if not evento:
    st.error("❌ El evento solicitado no existe o ya finalizó.")
    st.stop()

# Asignación de variables desde DB
ID_REUNION = evento.slug
NOMBRE_EVENTO = evento.titulo_curso
LINK_ZOOM = evento.link_zoom
# Si no hay link de Youtube, usamos el canal general por defecto
LINK_YOUTUBE = evento.link_youtube if evento.link_youtube else "https://www.youtube.com/@mbeducacion/live"
CUPO_MAXIMO = evento.capacidad_max if evento.capacidad_max else 100

# --- 4. VERIFICAR REGISTRO PREVIO Y CONTEO REAL ---
try:
    registro_previo = st_javascript(f"localStorage.getItem('mbeducacion_registro_{ID_REUNION}');")
except:
    registro_previo = None

def obtener_conteo_real():
    if conexion_db_exitosa:
        try:
            with engine.connect() as conn:
                # Contamos exactamente cuántos registros tienen este SLUG en el canal de autorización
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM directorio_tratamiento 
                    WHERE canal_autorizacion LIKE :filtro
                """), {"filtro": f"%{ID_REUNION}%"})
                return result.scalar()
        except:
            return 0
    return 0

conteo_actual = obtener_conteo_real()

# Lógica de Semáforo (Zoom o Youtube)
if conteo_actual >= CUPO_MAXIMO:
    link_destino = LINK_YOUTUBE
    mensaje_cupo = "🚀 ¡Sala de Zoom llena! Accede a la transmisión oficial en YouTube Live."
    color_alerta = "orange"
else:
    link_destino = LINK_ZOOM
    mensaje_cupo = "✅ ¡Cupo disponible en Zoom! Podrás interactuar en vivo."
    color_alerta = "green"

# --- 5. VISTA PARA USUARIOS YA REGISTRADOS ---
if registro_previo == "true":
    st.title(NOMBRE_EVENTO)
    st.success("✨ ¡Hola de nuevo! Ya estás registrado para este evento.")
    st.info(mensaje_cupo)
    
    st.markdown(f"""
        <a href="{link_destino}" target="_blank" style="
            text-decoration: none; background-color: #2D8CFF; color: white;
            padding: 18px 25px; border-radius: 12px; font-weight: bold;
            display: inline-block; text-align: center; width: 100%;
            font-size: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        ">ENTRAR A LA CLASE AHORA</a>
    """, unsafe_allow_html=True)
    
    if st.button("Actualizar mis datos / No soy yo"):
        st_javascript(f"localStorage.removeItem('mbeducacion_registro_{ID_REUNION}');")
        st.rerun()
    st.stop()

# --- 6. FORMULARIO DE REGISTRO ---
st.title("Registro de Asistencia")
st.subheader(f"Evento: {NOMBRE_EVENTO}")

with st.form("registro_publico", clear_on_submit=True):
    nombre = st.text_input("Nombre Completo *")
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        tipo_doc = st.selectbox("Tipo Doc *", ["C.C.", "NIT", "C.E.", "Pasaporte", "T.I.", "Otro"])
    with col_d2:
        doc_identidad = st.text_input("Número de Documento *")

    institucion = st.text_input("Institución / Empresa *")
    rol_cargo = st.text_input("Cargo *")
    email = st.text_input("Correo Electrónico *")
    
    st.markdown("---")
    st.write("🔒 **Tratamiento de Datos Personales**")
    with st.expander("Leer Autorización de Tratamiento de Datos"):
        st.markdown("""
        ### prueba con correo MB EDUCACIÓN - AUTORIZACIÓN PARA EL TRATAMIENTO DE DATOS PERSONALES
        
        De conformidad con la legislación legal vigente y la Política de Tratamiento de Datos Personales de MB Educación, el tratamiento de los datos que se reportan en este Formulario se regirá por las siguientes condiciones:
        a) Yo, al diligenciar este Formulario, concedo autorización previa, expresa e informada a MB Educación, para el tratamiento de los datos que suministro, sabiendo que he sido informado que la finalidad de dichos datos es adquirir un producto o solicitar un servicio que ella ofrece ahora o en el futuro, de tal manera que puedan tramitar mi solicitud adecuadamente, contactarme en caso de que se requiera y adelantar todas las acciones para el logro del particular.
        b) Conozco y acepto que esta información será tratada de acuerdo con la Política de Tratamiento de Datos Personales de MB Educación disponible en su página Web, que declaro haber leído y conocer, en especial en lo referente a mis derechos y a los procedimientos con que la Entidad cuenta, para hacerlos efectivos ante sus autoridades.
        c) Se que los siguientes son los derechos básicos que tengo como titular de los datos que se han diligenciado en este Formulario: 1) Todos los datos registrados en este Formulario sólo serán empleados por MB Educación para cumplir la finalidad expuesta en el punto (a) del presente Aviso; 2) En cualquier momento, puedo solicitar una consulta de la información con que MB Educación cuenta sobre mí, dirigiéndome al Oficial de Protección de Datos Personales de la Entidad; 3) MB Educación velará por la confidencialidad y privacidad de los datos personales de los titulares que están siendo reportados, según las disposiciones legales vigentes; 4) En cualquier momento puedo solicitar una prueba de esta autorización.
        d) El Oficial de Protección de Datos Personales de la Entidad, ante quien puedo ejercer mis derechos, de forma gratuita, lo contactar en la siguiente dirección electrónica: usodedatos@mbeducacion.com.co")
         """)

    acepta = st.checkbox("He leído y acepto la política de Habeas Data *")
    acepta_promos = st.checkbox("Deseo recibir información de futuros cursos y productos de MB")
    
    boton_registro = st.form_submit_button("REGISTRARME E INGRESAR")

# --- 7. PROCESO DE REGISTRO Y REDIRECCIÓN ---
if boton_registro:
    if not nombre or not doc_identidad or not email or not acepta:
        st.error("⚠️ Completa los campos obligatorios (*) para continuar.")
    else:
        try:
            # Volvemos a contar justo antes de guardar para evitar errores de último segundo
            conteo_final = obtener_conteo_real()
            url_final = LINK_ZOOM if conteo_final < CUPO_MAXIMO else LINK_YOUTUBE
            
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO directorio_tratamiento 
                    (contacto_nombre, tipo_documento, documento_identidad, institucion, rol_cargo, email, habeas_data, autoriza_env_info, canal_autorizacion) 
                    VALUES (:nom, :tdoc, :doc, :inst, :rol, :mail, 1, :env, :cnal)
                """), {
                    "nom": nombre, "tdoc": tipo_doc, "doc": doc_identidad,
                    "inst": institucion, "rol": rol_cargo, "mail": email,
                    "env": 1 if acepta_promos else 0,
                    "cnal": f"Registro Zoom - {ID_REUNION} - {time.strftime('%Y-%m-%d %H:%M')}"
                })

            # Guardamos persistencia en el navegador
            st_javascript(f"localStorage.setItem('mbeducacion_registro_{ID_REUNION}', 'true');")
            
            st.success("✅ ¡Registro completado con éxito!")
            st.write("Redirigiendo a la transmisión...")
            
            # Redirección automática por JavaScript (más confiable)
            js_redir = f'window.location.href = "{url_final}";'
            st_javascript(js_redir)
            
            # Respaldo por si JS falla
            st.markdown(f'<meta http-equiv="refresh" content="1; url={url_final}">', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error al procesar registro: {e}")

 
