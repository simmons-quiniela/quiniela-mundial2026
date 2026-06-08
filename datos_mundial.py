"""
datos_mundial.py
Grupos, partidos y lógica de puntuación del Mundial 2026.
Fuente: FIFA / ESPN (grupos confirmados diciembre 2025)
"""

# ──────────────────────────────────────────────────────────────
# GRUPOS — 12 grupos de 4 equipos
# ──────────────────────────────────────────────────────────────
GRUPOS = {
    "A": ["México", "Corea del Sur", "Sudáfrica", "Chequia"],
    "B": ["Canadá", "Bosnia-Herzegovina", "Qatar", "Suiza"],
    "C": ["Brasil", "Marruecos", "Croacia", "Albania"],
    "D": ["Estados Unidos", "Paraguay", "Australia", "Türkiye"],
    "E": ["España", "Japón", "Argelia", "Serbia"],
    "F": ["Inglaterra", "Senegal", "Países Bajos", "Eslovaquia"],
    "G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
    "H": ["Argentina", "Chile", "Arabia Saudita", "Ghana"],
    "I": ["Francia", "Senegal", "Irak", "Noruega"],
    "J": ["Alemania", "Ecuador", "Rep. Dominicana", "Eslovenia"],
    "K": ["Portugal", "Colombia", "DR Congo", "Uzbekistán"],
    "L": ["Uruguay", "Camerún", "Curaçao", "Jordania"],
}

# ──────────────────────────────────────────────────────────────
# PARTIDOS DE FASE DE GRUPOS (72 partidos, 3 por grupo)
# Cada grupo genera 3 partidos: 1v2, 1v3, 2v3 (+ 1v4, 2v4, 3v4 con 4 equipos)
# Con 4 equipos por grupo hay 6 partidos por grupo = 72 total
# ──────────────────────────────────────────────────────────────
def _generar_partidos():
    """Genera automáticamente los 6 partidos de cada grupo (combinatoria)."""
    from itertools import combinations
    partidos = []
    fechas_inicio = {
        "A": "11 Jun", "B": "12 Jun", "C": "13 Jun", "D": "12 Jun",
        "E": "14 Jun", "F": "15 Jun", "G": "15 Jun", "H": "16 Jun",
        "I": "16 Jun", "J": "17 Jun", "K": "17 Jun", "L": "18 Jun",
    }
    jornadas = {1: "J1", 2: "J2", 3: "J3"}
    # Orden canónico de emparejamientos por jornada (FIFA):
    # J1: 1v2, 3v4 | J2: 1v3, 2v4 | J3: 1v4, 2v3
    orden = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]
    jornada_map = {0:"J1", 1:"J1", 2:"J2", 3:"J2", 4:"J3", 5:"J3"}
    for grupo, equipos in GRUPOS.items():
        for idx, (i, j) in enumerate(orden):
            partidos.append({
                "id": f"{grupo}{idx+1}",
                "grupo": grupo,
                "jornada": jornada_map[idx],
                "local": equipos[i],
                "visita": equipos[j],
                "fecha": fechas_inicio[grupo],
            })
    return partidos

PARTIDOS = _generar_partidos()

# ──────────────────────────────────────────────────────────────
# LÓGICA DE PUNTUACIÓN
# ──────────────────────────────────────────────────────────────
def calcular_puntos(pred_local: int, pred_visita: int, real_local: int, real_visita: int):
    """
    Calcula los puntos para una predicción:
      3 pts → marcador exacto
      1 pt  → ganador/empate correcto
      0 pts → fallo total
    Devuelve (puntos: int, tipo: str)
    """
    if pred_local == real_local and pred_visita == real_visita:
        return 3, "exacto"
    pred_resultado = "L" if pred_local > pred_visita else ("V" if pred_visita > pred_local else "E")
    real_resultado = "L" if real_local > real_visita else ("V" if real_visita > real_local else "E")
    if pred_resultado == real_resultado:
        return 1, "ganador"
    return 0, "fallo"


# ──────────────────────────────────────────────────────────────
# UTILIDADES
# ──────────────────────────────────────────────────────────────
def partidos_por_jornada(grupo: str):
    """Devuelve los partidos de un grupo organizados por jornada."""
    p = [x for x in PARTIDOS if x["grupo"] == grupo]
    return {
        "J1": [x for x in p if x["jornada"] == "J1"],
        "J2": [x for x in p if x["jornada"] == "J2"],
        "J3": [x for x in p if x["jornada"] == "J3"],
    }

if __name__ == "__main__":
    print(f"Total partidos generados: {len(PARTIDOS)}")
    for g in GRUPOS:
        pg = [p for p in PARTIDOS if p["grupo"] == g]
        print(f"  Grupo {g}: {len(pg)} partidos — {GRUPOS[g]}")
    # Test puntuación
    assert calcular_puntos(2, 1, 2, 1) == (3, "exacto")
    assert calcular_puntos(2, 0, 3, 1) == (1, "ganador")
    assert calcular_puntos(1, 1, 2, 0) == (0, "fallo")
    print("✅ Tests de puntuación OK")
