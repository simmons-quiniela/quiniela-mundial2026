"""
╔══════════════════════════════════════════════╗
║   QUINIELA MUNDIAL 2026 — App Principal      ║
║   Streamlit + Google Sheets                  ║
╚══════════════════════════════════════════════╝
Ejecutar:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json, re
from datos_mundial import GRUPOS, PARTIDOS, calcular_puntos

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
CLAVE_ADMIN = "mundial2026admin"
FECHA_LIMITE = datetime(2026, 6, 11, 3, 0)  # 11 Jun 2026 a las 3am UTC = medianoche Ecuador
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(
    page_title="Quiniela Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
  .titulo-principal {
    font-size: 2.2rem; font-weight: 700;
    text-align: center; color: #1a1a2e;
    padding: 1rem 0 0.2rem;
  }
  .subtitulo {
    text-align: center; color: #555; margin-bottom: 1.5rem;
  }
  .card-grupo {
    background: #f8f9fa; border-radius: 10px;
    padding: 0.8rem 1rem; margin-bottom: 0.5rem;
    border-left: 4px solid #d4a017;
  }
  .medalla-oro   { color: #d4a017; font-weight: 700; }
  .medalla-plata { color: #a8a8a8; font-weight: 700; }
  .medalla-bronce{ color: #cd7f32; font-weight: 700; }
  .tag-puntos {
    background: #1a1a2e; color: white;
    border-radius: 20px; padding: 2px 10px;
    font-size: 0.85rem; font-weight: 600;
  }
  .exito { color: #28a745; font-weight: 600; }
  .info  { color: #17a2b8; }
  div[data-testid="stMetricValue"] { font-size: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONEXIÓN GOOGLE SHEETS
# ──────────────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    """Conecta con Google Sheets usando las credenciales del secrets."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        cliente = gspread.authorize(creds)
        return cliente
    except Exception as e:
        st.error(f"❌ Error de conexión con Google Sheets: {e}")
        st.info("👉 Sigue las instrucciones en README.md para configurar las credenciales.")
        return None

def obtener_hoja(nombre_hoja: str):
    """Devuelve una hoja de cálculo por nombre; la crea si no existe."""
    cliente = conectar_sheets()
    if not cliente:
        return None
    try:
        spreadsheet = cliente.open(st.secrets["spreadsheet_name"])
        try:
            return spreadsheet.worksheet(nombre_hoja)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=nombre_hoja, rows=500, cols=20)
    except Exception as e:
        st.error(f"Error al abrir el spreadsheet: {e}")
        return None

# ──────────────────────────────────────────────
# FUNCIONES DE DATOS
# ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def cargar_predicciones():
    """Carga todas las predicciones desde Google Sheets."""
    hoja = obtener_hoja("predicciones")
    if not hoja:
        return pd.DataFrame()
    datos = hoja.get_all_records()
    return pd.DataFrame(datos) if datos else pd.DataFrame()

@st.cache_data(ttl=60)
def cargar_resultados():
    """Carga los resultados reales desde Google Sheets."""
    hoja = obtener_hoja("resultados")
    if not hoja:
        return {}
    datos = hoja.get_all_records()
    if not datos:
        return {}
    resultados = {}
    for fila in datos:
        partido_id = fila.get("partido_id", "")
        if partido_id:
            resultados[partido_id] = {
                "goles_local": fila.get("goles_local", ""),
                "goles_visita": fila.get("goles_visita", ""),
            }
    return resultados

def guardar_prediccion(nombre: str, predicciones: dict):
    """Guarda o actualiza las predicciones de un participante."""
    hoja = obtener_hoja("predicciones")
    if not hoja:
        return False
    nombre_limpio = nombre.strip().lower()
    fila_nueva = {"nombre": nombre.strip(), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
    fila_nueva.update({f"p_{pid}": f"{v['local']}-{v['visita']}" for pid, v in predicciones.items()})
    encabezados = hoja.row_values(1)
    if not encabezados:
        hoja.append_row(list(fila_nueva.keys()))
        hoja.append_row(list(fila_nueva.values()))
        cargar_predicciones.clear()
        return True
    try:
        todos = hoja.get_all_values()
        fila_existente = None
        for i, fila in enumerate(todos[1:], start=2):
            if fila and fila[0].strip().lower() == nombre_limpio:
                fila_existente = i
                break
    except Exception:
        fila_existente = None
    valores = [fila_nueva.get(col, "") for col in encabezados]
    if fila_existente:
        hoja.update(f"A{fila_existente}", [valores])
    else:
        hoja.append_row(valores)
    cargar_predicciones.clear()
    return True

def guardar_resultado(partido_id: str, goles_local: int, goles_visita: int):
    """Guarda o actualiza el resultado real de un partido."""
    hoja = obtener_hoja("resultados")
    if not hoja:
        return False
    datos = hoja.get_all_records()
    fila_existente = None
    for i, fila in enumerate(datos, start=2):
        if fila.get("partido_id") == partido_id:
            fila_existente = i
            break
    partido_info = next((p for p in PARTIDOS if p["id"] == partido_id), {})
    nueva_fila = [
        partido_id,
        partido_info.get("local", ""),
        partido_info.get("visita", ""),
        goles_local,
        goles_visita,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ]
    if fila_existente:
        hoja.update(f"A{fila_existente}", [nueva_fila])
    else:
        encabezados = hoja.row_values(1)
        if not encabezados:
            hoja.append_row(["partido_id", "local", "visita", "goles_local", "goles_visita", "timestamp"])
        hoja.append_row(nueva_fila)
    cargar_resultados.clear()
    return True

def calcular_tabla_posiciones():
    """Genera la tabla de posiciones con puntos de todos los participantes."""
    df_pred = cargar_predicciones()
    resultados = cargar_resultados()
    if df_pred.empty or not resultados:
        return pd.DataFrame()
    filas = []
    for _, fila in df_pred.iterrows():
        nombre = fila.get("nombre", "")
        pts_exacto = pts_ganador = pts_total = partidos_jugados = 0
        for partido_id, res in resultados.items():
            col = f"p_{partido_id}"
            pred_str = str(fila.get(col, ""))
            if re.match(r"^\d+-\d+$", pred_str):
                p_local, p_visita = map(int, pred_str.split("-"))
                r_local = int(res.get("goles_local", -1))
                r_visita = int(res.get("goles_visita", -1))
                if r_local >= 0 and r_visita >= 0:
                    puntos, tipo = calcular_puntos(p_local, p_visita, r_local, r_visita)
                    pts_total += puntos
                    partidos_jugados += 1
                    if tipo == "exacto":
                        pts_exacto += 1
                    elif tipo == "ganador":
                        pts_ganador += 1
        filas.append({
            "Participante": nombre,
            "Puntos": pts_total,
            "Exactos (3pts)": pts_exacto,
            "Ganador (1pt)": pts_ganador,
            "Partidos jugados": partidos_jugados,
        })
    if not filas:
        return pd.DataFrame()
    df = pd.DataFrame(filas)
    df = df.sort_values(["Puntos", "Exactos (3pts)"], ascending=False).reset_index(drop=True)
    df.index += 1
    return df

# ──────────────────────────────────────────────
# PÁGINAS
# ──────────────────────────────────────────────

def pagina_inicio():
    st.markdown('<div class="titulo-principal">⚽ Quiniela Mundial 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">🇺🇸 🇨🇦 🇲🇽 &nbsp; Fase de Grupos — 48 equipos, 72 partidos</div>', unsafe_allow_html=True)
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    df_pred = cargar_predicciones()
    resultados = cargar_resultados()
    col1.metric("👥 Participantes", len(df_pred))
    col2.metric("⚽ Partidos totales", len(PARTIDOS))
    col3.metric("✅ Resultados cargados", len(resultados))
    col4.metric("🏆 Grupos", 12)
    st.divider()
    st.subheader("📋 Los 12 Grupos del Mundial 2026")
    cols = st.columns(3)
    for i, (grupo, equipos) in enumerate(GRUPOS.items()):
        with cols[i % 3]:
            equipos_html = " &nbsp;·&nbsp; ".join(equipos)
            st.markdown(
                f'<div class="card-grupo"><strong>Grupo {grupo}</strong><br>'
                f'<span style="font-size:0.85rem;color:#444">{equipos_html}</span></div>',
                unsafe_allow_html=True,
            )

def pagina_predicciones():
    st.header("📝 Ingresar mis predicciones")
    st.info("💡 Ingresa el marcador que predices para cada partido. Puedes volver a guardar para actualizar tus predicciones.")
    nombre = st.text_input("Tus dos apellidos", placeholder="Ej: García López")
    ahora = datetime.now()
    if ahora > FECHA_LIMITE:
        st.error("⛔ El plazo para ingresar predicciones cerró el 11 de junio a medianoche.")
        st.info("Puedes ver la tabla de posiciones en el menú lateral.")
        return

    if not nombre:
        st.warning("⬆️ Escribe tu nombre para continuar.")
        return

    resultados_reales = cargar_resultados()
    df_pred = cargar_predicciones()
    pred_actuales = {}
    if not df_pred.empty:
        fila = df_pred[df_pred["nombre"].str.strip().str.lower() == nombre.strip().lower()]
        if not fila.empty:
            st.success(f"✅ Ya tienes predicciones guardadas. Puedes modificarlas abajo.")
            pred_actuales = fila.iloc[0].to_dict()

    predicciones_nuevas = {}
    grupos_list = list(GRUPOS.keys())
    grupo_sel = st.selectbox("Filtrar por grupo", ["Todos"] + [f"Grupo {g}" for g in grupos_list])

    for grupo, equipos in GRUPOS.items():
        if grupo_sel != "Todos" and grupo_sel != f"Grupo {grupo}":
            continue
        partidos_grupo = [p for p in PARTIDOS if p["grupo"] == grupo]
        with st.expander(f"🏴 Grupo {grupo} — {' · '.join(equipos)}", expanded=(grupo_sel != "Todos")):
            for partido in partidos_grupo:
                pid = partido["id"]
                val_actual = pred_actuales.get(f"p_{pid}", "")
                loc_def = vis_def = 0
                if re.match(r"^\d+-\d+$", str(val_actual)):
                    loc_def, vis_def = map(int, str(val_actual).split("-"))

                ya_jugado = pid in resultados_reales
                sufijo = " ✅" if ya_jugado else ""

                # Diseño amigable para móvil
                if sufijo:
                    st.markdown(
                        f"<div style='text-align:center;color:green;font-size:0.8rem;margin-bottom:4px'>{sufijo}</div>",
                        unsafe_allow_html=True)
                c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 2, 3])
                with c1:
                    st.markdown(f"<div style='text-align:center;font-weight:700;font-size:0.95rem;padding-top:8px'>{partido['local']}</div>", unsafe_allow_html=True)
                with c2:
                    gl = st.number_input(f"Goles {partido['local']}", min_value=0, max_value=20,
                                         value=loc_def, key=f"loc_{pid}", label_visibility="collapsed")
                with c3:
                    st.markdown("<div style='text-align:center;padding-top:8px;font-weight:700'>—</div>", unsafe_allow_html=True)
                with c4:
                    gv = st.number_input(f"Goles {partido['visita']}", min_value=0, max_value=20,
                                         value=vis_def, key=f"vis_{pid}", label_visibility="collapsed")
                with c5:
                    st.markdown(f"<div style='text-align:center;font-weight:700;font-size:0.95rem;padding-top:8px'>{partido['visita']}</div>", unsafe_allow_html=True)
                predicciones_nuevas[pid] = {"local": gl, "visita": gv}
                st.divider()

    if st.button("💾 Guardar todas mis predicciones", type="primary", use_container_width=True):
        with st.spinner("Guardando..."):
            ok = guardar_prediccion(nombre, predicciones_nuevas)
        if ok:
            st.success(f"✅ ¡Predicciones guardadas para **{nombre}**! ({len(predicciones_nuevas)} partidos)")
            st.balloons()
        else:
            st.error("❌ Error al guardar. Verifica la conexión con Google Sheets.")

def pagina_tabla():
    st.header("🏆 Tabla de Posiciones")
    if st.button("🔄 Actualizar tabla"):
        cargar_predicciones.clear()
        cargar_resultados.clear()
        st.rerun()

    with st.spinner("Calculando puntos..."):
        df = calcular_tabla_posiciones()

    if df.empty:
        st.info("Aún no hay suficientes datos para mostrar la tabla. Se necesitan predicciones y al menos un resultado cargado.")
        return

    # Top 3
    st.subheader("🥇 Podio")
    cols = st.columns(3)
    medallas = ["🥇", "🥈", "🥉"]
    colores  = ["#d4a017", "#a8a8a8", "#cd7f32"]
    for i, (col, med, color) in enumerate(zip(cols, medallas, colores)):
        if i < len(df):
            fila = df.iloc[i]
            with col:
                st.markdown(
                    f"<div style='background:{color}22;border:2px solid {color};border-radius:12px;"
                    f"padding:1rem;text-align:center'>"
                    f"<div style='font-size:2rem'>{med}</div>"
                    f"<div style='font-weight:700;font-size:1.1rem'>{fila['Participante']}</div>"
                    f"<div style='font-size:1.8rem;font-weight:700;color:{color}'>{fila['Puntos']} pts</div>"
                    f"<div style='font-size:0.8rem;color:#555'>⭐{fila['Exactos (3pts)']} exactos &nbsp; "
                    f"✓{fila['Ganador (1pt)']} ganador</div></div>",
                    unsafe_allow_html=True,
                )
    st.divider()

    # Tabla completa
    st.subheader(f"📊 Clasificación completa — {len(df)} participantes")
    def color_fila(row):
        if row.name <= 3:
            return ["background-color: #fff9e6"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(color_fila, axis=1).format({"Puntos": "{:.0f}"}),
        use_container_width=True,
        height=min(50 + len(df) * 35, 600),
    )

    # Explicación puntos
    with st.expander("ℹ️ ¿Cómo se calculan los puntos?"):
        st.markdown("""
| Acierto | Puntos |
|---------|--------|
| ⭐ Marcador exacto (ej: 2-1 = 2-1) | **3 puntos** |
| ✅ Ganador/empate correcto (ej: 2-0 predice cualquier victoria local) | **1 punto** |
| ❌ Fallo total | **0 puntos** |

**Desempate:** Mayor cantidad de resultados exactos.
        """)

def pagina_admin():
    st.header("🔧 Panel de Administración")
    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        pwd = st.text_input("Contraseña de administrador", type="password")
        if st.button("Ingresar"):
            if pwd == CLAVE_ADMIN:
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        return

    st.success("✅ Acceso de administrador")
    tab_res, tab_part, tab_export = st.tabs(["⚽ Cargar resultados", "👥 Ver participantes", "📤 Exportar"])

    with tab_res:
        st.subheader("Cargar resultado de partido")
        resultados_act = cargar_resultados()
        grupos_list = list(GRUPOS.keys())
        grupo_sel = st.selectbox("Grupo", grupos_list, key="admin_grupo")
        partidos_grupo = [p for p in PARTIDOS if p["grupo"] == grupo_sel]
        opciones = [f"{p['local']} vs {p['visita']} ({p['fecha']})" for p in partidos_grupo]
        sel_idx = st.selectbox("Partido", range(len(opciones)), format_func=lambda i: opciones[i])
        partido = partidos_grupo[sel_idx]
        pid = partido["id"]

        # Mostrar resultado actual si existe
        if pid in resultados_act:
            r = resultados_act[pid]
            st.info(f"Resultado actual: {partido['local']} {r['goles_local']} — {r['goles_visita']} {partido['visita']}")

        c1, c2 = st.columns(2)
        with c1:
            gl = st.number_input(f"Goles {partido['local']}", min_value=0, max_value=20, value=0, key="admin_gl")
        with c2:
            gv = st.number_input(f"Goles {partido['visita']}", min_value=0, max_value=20, value=0, key="admin_gv")

        if st.button("💾 Guardar resultado", type="primary"):
            with st.spinner("Guardando..."):
                ok = guardar_resultado(pid, gl, gv)
            if ok:
                st.success(f"✅ Resultado guardado: {partido['local']} {gl} — {gv} {partido['visita']}")
                cargar_resultados.clear()
            else:
                st.error("Error al guardar.")

        # Tabla resumen de resultados cargados
        st.divider()
        st.subheader(f"Resultados cargados ({len(resultados_act)}/{len(PARTIDOS)})")
        if resultados_act:
            filas_res = []
            for pid_r, res in resultados_act.items():
                info = next((p for p in PARTIDOS if p["id"] == pid_r), {})
                filas_res.append({
                    "Partido": f"{info.get('local','')} vs {info.get('visita','')}",
                    "Grupo": info.get("grupo", ""),
                    "Fecha": info.get("fecha", ""),
                    "Resultado": f"{res['goles_local']} - {res['goles_visita']}",
                })
            st.dataframe(pd.DataFrame(filas_res), use_container_width=True)

    with tab_part:
        st.subheader("Participantes registrados")
        df_pred = cargar_predicciones()
        if df_pred.empty:
            st.info("Aún no hay predicciones.")
        else:
            st.metric("Total participantes", len(df_pred))
            cols_mostrar = ["nombre", "timestamp"] if "timestamp" in df_pred.columns else ["nombre"]
            st.dataframe(df_pred[cols_mostrar], use_container_width=True)
            if st.button("🔄 Recargar"):
                cargar_predicciones.clear()
                st.rerun()

    with tab_export:
        st.subheader("Exportar datos")
        df_tabla = calcular_tabla_posiciones()
        if not df_tabla.empty:
            csv = df_tabla.to_csv(index=True).encode("utf-8")
            st.download_button(
                "⬇️ Descargar tabla de posiciones (CSV)",
                data=csv,
                file_name="tabla_posiciones_mundial2026.csv",
                mime="text/csv",
            )
        df_pred = cargar_predicciones()
        if not df_pred.empty:
            csv2 = df_pred.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Descargar todas las predicciones (CSV)",
                data=csv2,
                file_name="predicciones_mundial2026.csv",
                mime="text/csv",
            )

# ──────────────────────────────────────────────
# NAVEGACIÓN PRINCIPAL
# ──────────────────────────────────────────────
def main():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/e/e3/2026_FIFA_World_Cup.svg/200px-2026_FIFA_World_Cup.svg.png", width=120)
        st.title("Mundial 2026")
        st.caption("Quiniela fase de grupos")
        st.divider()
        pagina = st.radio(
            "Navegar",
            ["🏠 Inicio", "📝 Mis predicciones", "🏆 Tabla de posiciones", "🔧 Admin"],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("⭐ Exacto = 3pts\n✅ Ganador = 1pt\n❌ Fallo = 0pts")

    if pagina == "🏠 Inicio":
        pagina_inicio()
    elif pagina == "📝 Mis predicciones":
        pagina_predicciones()
    elif pagina == "🏆 Tabla de posiciones":
        pagina_tabla()
    elif pagina == "🔧 Admin":
        pagina_admin()

if __name__ == "__main__":
    main()
