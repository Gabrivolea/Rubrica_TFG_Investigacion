import os
import sys
import streamlit as st
import pandas as pd
import base64
import PyPDF2
import io
import math
import json
from collections import Counter

st.set_page_config(page_title="Rúbrica TFG Investigación", page_icon="📝", layout="wide")

# ---------------- LÓGICA DE CARGA Y DESCARGA DE SESIÓN (PARA LA NUBE) ----------------
if 'rubrica_dinamica' not in st.session_state:
    rubrica_base = {
        "1. Título, abstract e índices": [
            "(1) El título está alineado con los objetivos y la metodología de estudio",
            "(2) Incluye un título corto (< 25 palabras) y no presenta errores en el título, en el nombre del departamento o del tutor/a",
            "(3) Incluye los resúmenes en español, inglés y catalán, en páginas independientes",
            "(4) Los resúmenes se ajustan como máximo a 500 palabras e incluyen la información más relevante",
            "(5) Incluye un índice general y un índice de figuras/tablas"
        ],
        "2. Resumen / Abstract (contenido)": [
            "Permite interpretar de manera muy adecuada el alcance del trabajo realizado, los objetivos y las conclusiones. Se ha realizado un gran esfuerzo para buscar la comprensión por parte del lector."
        ],
        "3. Introducción": [
            "Presenta con claridad el problema a resolver y/o la motivación del trabajo. Va de lo general a lo particular e incluye los antecedentes del tema estudiado. Resume bien el marco teórico."
        ],
        "4. Marco teórico": [
            "Identifica, clasifica y relaciona según un criterio adecuado todas las ideas y características relevantes del trabajo. Todas las referencias utilizadas son adecuadas y de calidad (bibliografía de referencia en la temática, artículos/documentos recientes y actuales). Su cantidad resulta muy adecuada para adquirir conocimientos en la temática."
        ],
        "5. Objetivos (aspectos formales)": [
            "(1) Los objetivos principales incluyen una o dos variables dependientes y una o dos variables independientes",
            "(2) El objetivo menciona la población diana",
            "(3) Se incluyen hipótesis que quedan bien justificadas con las referencias del marco teórico",
            "(4) Usa los verbos adecuados, en función del tipo de Investigación (de comparación, de correlación o de causalidad)",
            "(5) Los objetivos específicos/secundario son un desglose de los objetivos principales"
        ],
        "6. Objetivos (general)": [
            "Realiza una explicación clara, concisa y concreta de cada uno de los objetivos propuestos, expresada en términos que admiten una sola interpretación, y priorizando la secuencia de su realización. Propone un objetivo original."
        ],
        "7. Metodología (diseño, procedimientos e instrumentos)": [
            "(1) El diseño es adecuado para dar respuesta al objetivo de la investigación",
            "(2) Los procedimientos descritos son adecuados a los objetivos planteados y permiten alcanzarlos",
            "(3) Contiene la información necesaria para poder ser replicado",
            "(4) Se detallan las características de los instrumentos utilizados",
            "(5) Se incluyen referencias sobre el uso, fiabilidad y/o validez de los instrumentos en estudios similares"
        ],
        "8. Metodología (muestra)": [
            "(1) Incluye datos sociodemográficos y antropométricos de la muestra (edad, sexo, peso, altura, IMC, etc.)",
            "(2) Incluye datos de la muestra importantes para el estudio (nivel de juego, nivel socioeconómico, etc.)",
            "(3) Se menciona el proceso de selección de la muestra (por conveniencia, aleatorio, mediante cuestionario...)",
            "(4) Contiene cuestiones de tipo ético como la firma de un consentimiento informado o al Comité de Bioética",
            "(5) La muestra parece lo suficientemente grande en relación al objetivo"
        ],
        "9. Metodología (general)": [
            "Describe de forma completa, precisa y argumentada la metodología utilizada en el desarrollo del trabajo de tal manera que el trabajo puede ser replicado."
        ],
        "10. Resultados (estructura general)": [
            "Expone de forma excelente los resultados, que son correctos y provienen de forma natural del procedimiento seguido. Los presenta de manera clara y concisa mediante tablas y figuras adecuadas."
        ],
        "11. Resultados (tablas y figuras)": [
            "Las figuras y tablas son autoexplicativas, incluyen un pie y encabezado en formato tal y como pide el formato APA 7, los resultados están alineados con los objetivos de estudio, se incluyen las unidades de las variables y no aparecen pixeladas (mejor que sean vectoriales)."
        ],
        "12. Discusión": [
            "Explica e interpreta los resultados obtenidos de manera excelente y relacionándolos con estudios previos (se incluyen al menos 5 referencias de calidad). Se plantean posibles limitaciones, mejoras y/o líneas futuras de trabajo muy adecuadas y lógicas, que demuestran el gran dominio adquirido en la temática."
        ],
        "13. Conclusiones": [
            "Expone de forma sintética y ordenada lógicamente las aportaciones realizadas en el TFG. Las conclusiones son totalmente acordes con los objetivos planteados."
        ],
        "14. Formato y presentación": [
            "(1) Utiliza la plantilla de los Trabajos Fin de Grado del CESAG (criterio obligatorio para valorar el trabajo)",
            "(2) Incluye un mínimo de 3 epígrafes en el marco teórico",
            "(3) El trabajo presenta orden y claridad",
            "(4) Utiliza correctamente las herramientas de formato de Word (saltos de página, formatos de letra)",
            "(5) El trabajo se limita a un máximo de 60 páginas (sin incluir referencias y/o anexos)"
        ],
        "15. Referencias bibliográficas": [
            "(1) Proporciona referencias bibliográficas según la normativa APA 7 (sangría francesa, revistas en cursiva, etc).",
            "(2) Todas o casi todas las referencias están citadas en el texto",
            "(3) Todas las citas del texto están referenciadas en la lista de referencias bibliográficas",
            "(4) La mayor parte de las referencias son de los últimos 10 años",
            "(5) Las referencias bibliográficas aparecen en orden alfabético"
        ],
        "16. Redacción y uso del lenguaje": [
            "(1) Los párrafos tienen contenido suficiente e incluyen ideas bien diferenciadas",
            "(2) Redacta en la forma adecuada para un estudiante de 4º curso de un grado universitario, sin faltas de ortografía, errores morfosintácticos o semánticos relevantes y utilizando un estilo impersonal",
            "(3) Emplea frases cortas fáciles de comprender, simplificando el lenguaje y no abusando de las frases subordinadas",
            "(4) Es preciso con la terminología",
            "(5) Define las abreviaturas la primera vez que aparecen"
        ]
    }
    rubrica_dinamica = []
    for i, (sec_nombre, criterios) in enumerate(rubrica_base.items()):
        seccion = {"id": f"sec_{i}", "nombre": sec_nombre, "visible": True, "criterios": []}
        for j, crit_texto in enumerate(criterios):
            seccion["criterios"].append({"id": f"crit_{i}_{j}", "texto": crit_texto, "visible": True, "peso": 1})
        rubrica_dinamica.append(seccion)
    st.session_state.rubrica_dinamica = rubrica_dinamica

if 'evaluaciones' not in st.session_state:
    st.session_state.evaluaciones = [{"alumno": "Trabajo 1", "observaciones": "", "respuestas": {}, "comentarios_items": {}, "plagio": 0, "ia": 0}]

if 'idx' not in st.session_state: st.session_state.idx = 0
if 'pdf_actual' not in st.session_state: st.session_state.pdf_actual = None
if 'texto_extraido' not in st.session_state: st.session_state.texto_extraido = ""

idx = st.session_state.idx
if idx >= len(st.session_state.evaluaciones):
    idx = len(st.session_state.evaluaciones) - 1
    st.session_state.idx = idx

eval_actual = st.session_state.evaluaciones[idx]
if "comentarios_items" not in eval_actual: eval_actual["comentarios_items"] = {}
if "respuestas" not in eval_actual: eval_actual["respuestas"] = {}

rubrica_dinamica = st.session_state.rubrica_dinamica

# --- MENÚ LATERAL: CONTROL DE COPIAS DE SEGURIDAD ---
st.sidebar.header("📁 Gestión de Evaluaciones")
archivo_cargado = st.sidebar.file_uploader("Subir archivo de progreso (.json)", type=["json"], help="Sube un archivo .json guardado previamente para recuperar tus alumnos y notas.")

if archivo_cargado is not None:
    try:
        datos_importados = json.load(archivo_cargado)
        if "evaluaciones" in datos_importados and "rubrica_dinamica" in datos_importados:
            st.session_state.evaluaciones = datos_importados["evaluaciones"]
            st.session_state.rubrica_dinamica = datos_importados["rubrica_dinamica"]
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo: {e}")

progreso_actual = {
    "evaluaciones": st.session_state.evaluaciones,
    "rubrica_dinamica": st.session_state.rubrica_dinamica
}
st.sidebar.download_button(
    label="📥 Guardar Todo el Progreso (.json)",
    data=json.dumps(progreso_actual, ensure_ascii=False, indent=4),
    file_name="progreso_rubrica_investigacion.json",
    mime="application/json",
    use_container_width=True,
    help="Descarga este archivo para guardar tus correcciones y bocadillos de comentarios en tu ordenador."
)

# ---------------- LÓGICA MATEMÁTICA DE PLAGIO LOCAL (COSENO) ----------------
def text_to_vector(text):
    words = [w for w in text.lower().split() if len(w) > 3]
    return Counter(words)

def calcular_similitud_coseno(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator: return 0.0
    else: return float(numerator) / denominator

def extraer_texto_pdf(archivo_bytes):
    try:
        lector = PyPDF2.PdfReader(io.BytesIO(archivo_bytes))
        texto = ""
        for pagina in lector.pages:
            texto += pagina.extract_text() + "\n"
        return texto
    except:
        return ""

def insertar_comentario_bocadillo(item_key, texto_bocadillo, i):
    com_key = f"com_{i}_{item_key}"
    actual = st.session_state.get(com_key, "")
    nuevo_texto = f"{actual} | {texto_bocadillo}".strip(" |") if actual else texto_bocadillo
    st.session_state[com_key] = nuevo_texto

# ---------------- GENERADOR DE BOLETÍN HTML ----------------
def generar_html_alumno(eval_actual, rubrica_dinamica, nota_final, total_puntos_max, puntos_obtenidos):
    color_nota = "#27AE60" if nota_final >= 5 else "#E74C3C" 
    color_map = {1: "#E74C3C", 2: "#E67E22", 3: "#F1C40F", 4: "#3498DB", 5: "#27AE60"}
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Informe de Evaluación - {eval_actual['alumno']}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F4F7F6; color: #333; line-height: 1.6; padding: 30px 10px; }}
            .container {{ max-width: 800px; margin: auto; background: #FFFFFF; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); }}
            .header {{ border-bottom: 3px solid #2980B9; padding-bottom: 20px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ margin: 0; color: #2C3E50; font-size: 28px; }}
            .header h2 {{ margin: 10px 0 0 0; color: #7F8C8D; font-weight: normal; font-size: 20px; }}
            .score-box {{ display: flex; justify-content: space-around; background: #F8F9FA; padding: 20px; border-radius: 8px; margin-bottom: 30px; border: 1px solid #E9ECEF; }}
            .score-item {{ text-align: center; }}
            .score-value {{ font-size: 36px; font-weight: bold; color: {color_nota}; }}
            .score-label {{ font-size: 14px; color: #7F8C8D; text-transform: uppercase; letter-spacing: 1px; }}
            .section {{ margin-bottom: 25px; }}
            .section h3 {{ background: #ECF0F1; color: #2980B9; padding: 10px 15px; border-radius: 6px; font-size: 16px; margin-bottom: 15px; }}
            .item {{ margin-bottom: 8px; font-size: 14.5px; display: flex; align-items: flex-start; }}
            .score-badge {{ padding: 3px 8px; border-radius: 4px; font-weight: bold; color: white; margin-right: 12px; font-size: 13px; min-width: 35px; text-align: center; display: inline-block; }}
            .weight-text {{ font-size: 12px; color: #7F8C8D; font-weight: bold; margin-left: 6px; text-transform: uppercase; }}
            .comentario-item {{ margin-top: 4px; margin-bottom: 12px; margin-left: 45px; padding: 6px 12px; background-color: #F8F9F9; border-left: 3px solid #BDC3C7; font-style: italic; color: #5D6D7E; font-size: 13.5px; }}
            .obs-final {{ margin-top: 40px; background: #FEF9E7; padding: 25px; border-radius: 8px; border: 1px solid #F4D03F; }}
            .obs-final h3 {{ margin-top: 0; color: #D4AC0D; font-size: 18px; border-bottom: 1px solid #F1C40F; padding-bottom: 10px; }}
            .obs-text {{ font-size: 15px; color: #555; white-space: pre-line; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>INFORME DE EVALUACIÓN - CESAG</h1>
                <h2>Alumno / Grupo: <strong>{eval_actual['alumno']}</strong></h2>
            </div>
            
            <div class="score-box">
                <div class="score-item">
                    <div class="score-value">{nota_final:.2f} / 10</div>
                    <div class="score-label">Calificación Final</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#34495E;">{puntos_obtenidos}/{total_puntos_max}</div>
                    <div class="score-label">Puntos Ponderados</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#E67E22;">{eval_actual.get('plagio', 0)}%</div>
                    <div class="score-label">Similitud (Plagio)</div>
                </div>
                <div class="score-item">
                    <div class="score-value" style="color:#9B59B6;">{eval_actual.get('ia', 0)}%</div>
                    <div class="score-label">Uso de IA</div>
                </div>
            </div>
    """
    for sec in rubrica_dinamica:
        if not sec["visible"]: continue
        criterios_visibles = [c for c in sec["criterios"] if c["visible"]]
        if not criterios_visibles: continue
        
        html += f'<div class="section"><h3>{sec["nombre"]}</h3>'
        for crit in criterios_visibles:
            key = crit["id"]
            texto_criterio = crit["texto"]
            peso = crit.get("peso", 1)
            
            valor_num = eval_actual["respuestas"].get(key, "No evaluado")
            if isinstance(valor_num, bool): valor_num = 5 if valor_num else 1
            
            txt_peso = f"<span class='weight-text'>(Peso: x{peso})</span>" if peso != 1 else ""
            
            if valor_num == "No evaluado":
                html += f'<div class="item"><span class="score-badge" style="background-color: #95A5A6;">N/E</span><span class="text" style="color: #7F8C8D;">{texto_criterio} {txt_peso}</span></div>'
            else:
                badge_color = color_map.get(valor_num, "#7F8C8D")
                html += f'<div class="item"><span class="score-badge" style="background-color: {badge_color};">{valor_num} / 5</span><span class="text">{texto_criterio} {txt_peso}</span></div>'
            
            com_item = eval_actual.get("comentarios_items", {}).get(key, "").strip()
            if com_item:
                html += f'<div class="comentario-item">↳ {com_item}</div>'
        html += '</div>'
        
    obs_finales = eval_actual.get("observaciones", "").strip()
    if obs_finales:
        html += f"""
            <div class="obs-final">
                <h3>Observaciones Finales y Conclusión</h3>
                <div class="obs-text">{obs_finales}</div>
            </div>
        """
    html += "</div></body></html>"
    return html

def aplicar_historial_obs(i):
    sel_key = f"sel_obs_{i}"
    com_key = f"obs_{i}"
    sel = st.session_state.get(sel_key)
    if sel and sel not in ["--- Vacío ---", "Autocompletar..."]:
        actual = st.session_state.get(com_key, "")
        nuevo_texto = f"{actual}\n• {sel}".strip() if actual else f"• {sel}"
        st.session_state[com_key] = nuevo_texto
        st.session_state[sel_key] = "Autocompletar..."

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    .seccion-titulo { font-size: 16px; font-weight: bold; color: #2E86C1; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 3px; }
    .caja-nota { border: 2px solid #888888; padding: 10px; text-align: center; border-radius: 8px; margin-top: 10px; }
    div[data-testid="InputInstructions"] { display: none !important; visibility: hidden !important; }
    div[data-testid="stTextInput"] input { padding: 4px 10px !important; font-size: 13px !important; }
    .edit-row { background-color: #f8f9f9; padding: 8px; border-radius: 6px; margin-bottom: 4px; border: 1px solid #e5e7e9; }
    .edit-section { background-color: #ebf5fb; padding: 10px; border-radius: 6px; margin-top: 15px; margin-bottom: 5px; border-left: 4px solid #3498db; }
    div[data-testid="stTextInput"] + div div[data-testid="stHorizontalBlock"] button {
        border-radius: 16px !important; background-color: #EBF5FB !important; color: #2E86C1 !important;
        border: 1px solid #AED6F1 !important; font-size: 11.5px !important; padding: 2px 8px !important; margin-top: 2px !important;
    }
    div[data-testid="stTextInput"] + div div[data-testid="stHorizontalBlock"] button:hover { background-color: #2E86C1 !important; color: white !important; border-color: #2E86C1 !important; }
    </style>
""", unsafe_allow_html=True)

tab_evaluacion, tab_plagio_cross = st.tabs(["📝 Corrección Individual", "🔍 Matriz Cruzada de Plagio"])

with tab_evaluacion:
    activar_visor = st.toggle("🖥️ Activar Visor de PDF (Doble Pantalla)", value=False)
    
    if activar_visor: col_rubrica, col_visor = st.columns([0.95, 2.05])
    else: col_rubrica = st.container()

    if activar_visor:
        with col_visor:
            if st.session_state.pdf_actual is None:
                st.subheader("Visor del Trabajo (PDF)")
                archivo_pdf = st.file_uploader("Sube el PDF del alumno para leerlo aquí", type=["pdf"], key="single_pdf_uploader")
                if archivo_pdf is not None:
                    bytes_pdf = archivo_pdf.read()
                    st.session_state.pdf_actual = base64.b64encode(bytes_pdf).decode('utf-8')
                    st.session_state.texto_extraido = extraer_texto_pdf(bytes_pdf)
                    st.rerun()
            else:
                col_btn, col_exp = st.columns([1, 2])
                with col_btn:
                    if st.button("🔄 Cambiar PDF (Subir otro)"):
                        st.session_state.pdf_actual = None
                        st.session_state.texto_extraido = ""
                        st.rerun()
                with col_exp:
                    with st.expander("📋 Copiar texto"):
                        st.text_area("Texto extraído:", st.session_state.texto_extraido, height=150, label_visibility="collapsed")
                pdf_display = f'<iframe src="data:application/pdf;base64,{st.session_state.pdf_actual}#toolbar=1&navpanes=0&view=FitH" width="100%" height="850" style="border: 1px solid #ccc; border-radius: 5px;" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

    with col_rubrica:
        modo_edicion = st.toggle("⚙️ Configurar Rúbrica (Modificar textos, Ocultar y Cambiar Pesos)", value=False)
        
        if modo_edicion:
            st.warning("⚠️ Modo Configuración activo.")
            with st.container(height=650):
                for i, sec in enumerate(rubrica_dinamica):
                    st.markdown(f"<div class='edit-section'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([0.05, 0.95])
                    sec["visible"] = c1.checkbox("👁️", value=sec["visible"], key=f"edit_vis_sec_{sec['id']}")
                    sec["nombre"] = c2.text_input("Título", value=sec["nombre"], key=f"edit_nom_sec_{sec['id']}", label_visibility="collapsed")
                    if sec["visible"]:
                        for j, crit in enumerate(sec["criterios"]):
                            st.markdown(f"<div class='edit-row'>", unsafe_allow_html=True)
                            cc1, cc2, cc3 = st.columns([0.05, 0.80, 0.15])
                            crit["visible"] = cc1.checkbox("👁️", value=crit.get("visible", True), key=f"edit_vis_crit_{crit['id']}")
                            crit["texto"] = cc2.text_input("Ítem", value=crit["texto"], key=f"edit_nom_crit_{crit['id']}", label_visibility="collapsed")
                            crit["peso"] = cc3.number_input("Peso", min_value=0, max_value=10, value=int(crit.get("peso", 1)), key=f"edit_p_crit_{crit['id']}", step=1)
                            st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("### Hoja de Evaluación")
            eval_actual["alumno"] = st.text_input("Nombre del Alumno / Grupo", value=eval_actual["alumno"])
            
            # FILTRO OPTIMIZADO PARA LA NUBE: EVITA EL COLAPSO DEL NAVEGADOR
            secciones_visibles = [sec for sec in rubrica_dinamica if sec["visible"]]
            nombres_secciones = [sec["nombre"] for sec in secciones_visibles]
            
            if nombres_secciones:
                sec_elegida_nombre = st.selectbox("📁 Selecciona el apartado a evaluar:", options=nombres_secciones)
                sec_actual = next(sec for sec in secciones_visibles if sec["nombre"] == sec_elegida_nombre)
                criterios_visibles = [c for c in sec_actual["criterios"] if c["visible"]]
                
                st.markdown(f"<div class='seccion-titulo'>🔹 {sec_actual['nombre']}</div>", unsafe_allow_html=True)
                
                with st.container(height=500):
                    if not criterios_visibles:
                        st.info("No hay criterios visibles en este apartado.")
                    
                    for crit in criterios_visibles:
                        key = crit["id"]
                        texto_criterio = crit["texto"]
                        peso = int(crit.get("peso", 1))
                        sel_key = f"sel_{idx}_{key}"
                        com_key = f"com_{idx}_{key}"
                        
                        val_previo = eval_actual["respuestas"].get(key, "No evaluado")
                        if isinstance(val_previo, bool): val_previo = 5 if val_previo else 1
                        if sel_key not in st.session_state: st.session_state[sel_key] = val_previo
                        val_actual = st.session_state.get(sel_key, "No evaluado")
                        
                        if com_key not in st.session_state: st.session_state[com_key] = eval_actual["comentarios_items"].get(key, "")
                        
                        historial_item = set()
                        for ev in st.session_state.evaluaciones:
                            com_previo = ev.get("comentarios_items", {}).get(key, "").strip()
                            if com_previo:
                                for linea in com_previo.split('|'):
                                    linea_limpia = linea.strip()
                                    if linea_limpia: historial_item.add(linea_limpia)
                        
                        ancho_izq = 8.5 if not activar_visor else 5.5
                        col_txt, col_val = st.columns([ancho_izq, 1.5])
                        txt_peso = f" (Peso: x{peso})" if peso != 1 else ""
                        texto_nota = f"[{val_actual}/5]{txt_peso}" if val_actual != "No evaluado" else f"[N/E]{txt_peso}"
                        color_etiqueta = "#2E86C1" if val_actual != "No evaluado" else "#95A5A6"
                        
                        with col_txt:
                            st.markdown(f"<div style='display:flex; align-items:flex-start; margin-bottom: 2px;'><span style='color: {color_etiqueta}; font-weight: bold; margin-right: 8px; font-size: 14px;'>{texto_nota}</span><p style='font-size: 13.5px; margin-top: 0px; margin-bottom: 0px; line-height: 1.2;'>{texto_criterio}</p></div>", unsafe_allow_html=True)
                            st.text_input("Comentario", key=com_key, placeholder="📝 Nota...", label_visibility="collapsed")
                            eval_actual["comentarios_items"][key] = st.session_state[com_key]
                            
                            if historial_item:
                                lista_pills = sorted(list(historial_item))
                                chunks = [lista_pills[x:x+3] for x in range(0, len(lista_pills), 3)]
                                for c_idx, chunk in enumerate(chunks):
                                    cols_bocadillos = st.columns(len(chunk))
                                    for idx_pill, texto_pill in enumerate(chunk):
                                        with cols_bocadillos[idx_pill]:
                                            st.button(f"💬 {texto_pill}", key=f"pill_{idx}_{key}_{texto_pill}_{c_idx}_{idx_pill}", on_click=insertar_comentario_bocadillo, args=(key, texto_pill, idx), use_container_width=True)
                                
                        with col_val:
                            st.selectbox("Nota", options=["No evaluado", 1, 2, 3, 4, 5], key=sel_key, label_visibility="collapsed")
                            eval_actual["respuestas"][key] = st.session_state[sel_key]
                        
                        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
                            
            # SECCIONES GLOBALES (SIEMPRE VISIBLES ABAJO)
            st.markdown("<div class='seccion-titulo'>🔹 Originalidad e IA</div>", unsafe_allow_html=True)
            p_key = f"plagio_{idx}"
            ia_key = f"ia_{idx}"
            if p_key not in st.session_state: st.session_state[p_key] = int(eval_actual.get("plagio", 0))
            if ia_key not in st.session_state: st.session_state[ia_key] = int(eval_actual.get("ia", 0))
            col_p, col_ia = st.columns(2)
            with col_p: st.number_input("% Plagio", min_value=0, max_value=100, key=p_key, step=1)
            with col_ia: st.number_input("% IA", min_value=0, max_value=100, key=ia_key, step=1)
            eval_actual["plagio"] = st.session_state[p_key]
            eval_actual["ia"] = st.session_state[ia_key]

            obs_key = f"obs_{idx}"
            if obs_key not in st.session_state: st.session_state[obs_key] = eval_actual.get("observaciones", "")
            historial_obs = set()
            for ev in st.session_state.evaluaciones:
                obs_previa = ev.get("observaciones", "").strip()
                if obs_previa: 
                    for linea in obs_previa.split('\n'):
                        linea_limpia = linea.replace('•', '').strip()
                        if linea_limpia: historial_obs.add(linea_limpia)
            col_título, col_hist_obs = st.columns([3, 1.5])
            with col_título: st.markdown("<div class='seccion-titulo'>🔹 Observaciones Finales</div>", unsafe_allow_html=True)
            with col_hist_obs:
                opciones_obs = ["Autocompletar..."] + sorted(list(historial_obs)) if historial_obs else ["--- Vacío ---"]
                st.selectbox("🕒 Hist", options=opciones_obs, key=f"sel_obs_{idx}", on_change=aplicar_historial_obs, args=(idx,), label_visibility="collapsed")
            st.text_area("Conclusiones:", key=obs_key, height=120, label_visibility="collapsed")
            eval_actual["observaciones"] = st.session_state[obs_key]

    if not modo_edicion:
        # CÁLCULO DE NOTA DINÁMICO RECORRIENDO TODA LA BASE DE DATOS INTERNA
        total_puntos_max = 0
        puntos_obtenidos = 0
        for s in rubrica_dinamica:
            if not s["visible"]: continue
            for c in s["criterios"]:
                if not c["visible"]: continue
                v_final = eval_actual["respuestas"].get(c["id"], "No evaluado")
                p_criterio = int(c.get("peso", 1))
                if v_final != "No evaluado":
                    total_puntos_max += (5 * p_criterio)
                    puntos_obtenidos += (int(v_final) * p_criterio)
        
        st.divider()
        nota_final = (puntos_obtenidos / total_puntos_max) * 10 if total_puntos_max > 0 else 0
        html_boletin = generar_html_alumno(eval_actual, rubrica_dinamica, nota_final, total_puntos_max, puntos_obtenidos)
        
        st.download_button(label="📥 Descargar Boletín HTML", data=html_boletin.encode('utf-8'), file_name=f"Boletin_{eval_actual['alumno'].replace(' ', '_')}.html", mime="text/html", use_container_width=True, type="primary")
        st.markdown(f"<div class='caja-nota'><h2>Nota Final: {nota_final:.2f} / 10</h2><p>Puntos totales acumulados: {puntos_obtenidos} de {total_puntos_max}</p></div>", unsafe_allow_html=True)

        col_prev, col_cent, col_next = st.columns([1, 1, 1])
        with col_prev:
            if st.button("⬅️ Anterior", use_container_width=True) and idx > 0:
                st.session_state.idx -= 1
                st.rerun()
        with col_cent:
            if st.button("➕ Nuevo Alumno", use_container_width=True):
                nuevo_id = len(st.session_state.evaluaciones) + 1
                st.session_state.evaluaciones.append({"alumno": f"Trabajo {nuevo_id}", "observaciones": "", "respuestas": {}, "comentarios_items": {}, "plagio": 0, "ia": 0})
                st.session_state.idx = len(st.session_state.evaluaciones) - 1
                st.session_state.pdf_actual = None 
                st.session_state.texto_extraido = ""
                st.rerun()
        with col_next:
            if st.button("Siguiente ➡️", use_container_width=True) and idx < len(st.session_state.evaluaciones) - 1:
                st.session_state.idx += 1
                st.rerun()
        st.write(f"Trabajo {idx + 1} de {len(st.session_state.evaluaciones)}")
        st.divider()
        
        datos_csv = []
        for ev in st.session_state.evaluaciones:
            fila = {"Alumno": ev["alumno"], "% Plagio": f"{ev.get('plagio', 0)}%", "% Uso IA": f"{ev.get('ia', 0)}%", "Observaciones Finales": ev["observaciones"]}
            tot_max, cump = 0, 0
            for s in rubrica_dinamica:
                if not s["visible"]: continue
                for c in s["criterios"]:
                    if not c["visible"]: continue
                    k = c["id"]
                    texto = c["texto"]
                    p_crit = int(c.get("peso", 1))
                    sec_nombre = s["nombre"]
                    valor_num = ev["respuestas"].get(k, "No evaluado")
                    if isinstance(valor_num, bool): valor_num = 5 if valor_num else 1
                    fila[f"[{sec_nombre[:12]}...] {texto[:40]}"] = valor_num
                    if valor_num != "No evaluado":
                        tot_max += (5 * p_crit)
                        cump += (int(valor_num) * p_crit)
            fila["NOTA FINAL"] = round((cump / tot_max) * 10, 2) if tot_max > 0 else 0
            datos_csv.append(fila)
            
        df_excel = pd.DataFrame(datos_csv)
        st.download_button(label="📊 Descargar Excel (Resultados)", data=df_excel.to_csv(index=False, sep=';').encode('utf-8-sig'), file_name="Evaluaciones.csv", mime="text/csv", use_container_width=True)

with tab_plagio_cross:
    st.header("🔍 Detector de Copia (Matriz Cruzada)")
    archivos_multiples = st.file_uploader("Sube TODOS los PDFs de la clase juntos", type=["pdf"], accept_multiple_files=True, key="cross_plag")
    if archivos_multiples:
        if len(archivos_multiples) < 2: st.info("Sube al menos 2 archivos.")
        else:
            with st.spinner("Analizando..."):
                textos_completos = {}
                vectores_completos = {}
                for f in archivos_multiples:
                    nombre_corto = f.name.replace(".pdf", "")
                    texto = extraer_texto_pdf(f.read())
                    textos_completos[nombre_corto] = texto
                    vectores_completos[nombre_corto] = text_to_vector(texto)
                nombres = list(textos_completos.keys())
                matriz_datos = []
                for fila_nom in nombres:
                    fila_resultado = {"Trabajo / Alumno": fila_nom}
                    for col_nom in nombres:
                        if fila_nom == col_nom: fila_resultado[col_nom] = "100.0%"
                        else:
                            sim = calcular_similitud_coseno(vectores_completos[fila_nom], vectores_completos[col_nom])
                            fila_resultado[col_nom] = f"{sim * 100:.1f}%"
                    matriz_datos.append(fila_resultado)
                df_matriz = pd.DataFrame(matriz_datos)
                df_matriz.set_index("Trabajo / Alumno", inplace=True)
                st.dataframe(df_matriz, use_container_width=True)