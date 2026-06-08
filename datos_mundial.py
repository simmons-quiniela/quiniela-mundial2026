"""
datos_mundial.py
Grupos y partidos OFICIALES del Mundial 2026.
Fuente: FIFA.com / worldcuppass.com (grupos confirmados diciembre 2025)
"""

# ──────────────────────────────────────────────────────────────
# GRUPOS OFICIALES — 12 grupos de 4 equipos
# ──────────────────────────────────────────────────────────────
GRUPOS = {
    "A": ["México", "Corea del Sur", "Sudáfrica", "Chequia"],
    "B": ["Canadá", "Suiza", "Qatar", "Bosnia-Herzegovina"],
    "C": ["Brasil", "Marruecos", "Escocia", "Haití"],
    "D": ["Estados Unidos", "Australia", "Paraguay", "Türkiye"],
    "E": ["Alemania", "Ecuador", "Costa de Marfil", "Curaçao"],
    "F": ["Países Bajos", "Japón", "Túnez", "Suecia"],
    "G": ["Bélgica", "Irán", "Egipto", "Nueva Zelanda"],
    "H": ["España", "Uruguay", "Arabia Saudita", "Cabo Verde"],
    "I": ["Francia", "Senegal", "Noruega", "Irak"],
    "J": ["Argentina", "Austria", "Argelia", "Jordania"],
    "K": ["Portugal", "Colombia", "Uzbekistán", "DR Congo"],
    "L": ["Inglaterra", "Croacia", "Panamá", "Ghana"],
}

# ──────────────────────────────────────────────────────────────
# PARTIDOS DE FASE DE GRUPOS (72 partidos, 6 por grupo)
# ──────────────────────────────────────────────────────────────
def _generar_partidos():
    partidos = []
    fechas_inicio = {
        "A": "11 Jun", "B": "12 Jun", "C": "13 Jun", "D": "12 Jun",
        "E": "14 Jun", "F": "15 Jun", "G": "15 Jun", "H": "16 Jun",
        "I": "16 Jun", "J": "17 Jun", "K": "17 Jun", "L": "18 Jun",
    }
    # Orden canónico FIFA: J1: 1v2, 3v4 | J2: 1v3, 2v4 | J3: 1v4, 2v3
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
def calcular_puntos(pred_local, pred_visita, real_local, real_visita):
    if pred_local == real_local and pred_visita == real_visita:
        return 3, "exacto"
    pred_res = "L" if pred_local > pred_visita else ("V" if pred_visita > pred_local else "E")
    real_res = "L" if real_local > real_visita else ("V" if real_visita > real_local else "E")
    if pred_res == real_res:
        return 1, "ganador"
    return 0, "fallo"

if __name__ == "__main__":
    print(f"Total partidos: {len(PARTIDOS)}")
    for g in GRUPOS:
        pg = [p for p in PARTIDOS if p["grupo"] == g]
        print(f"  Grupo {g}: {GRUPOS[g]}")
    assert calcular_puntos(2,1,2,1) == (3,"exacto")
    assert calcular_puntos(2,0,3,1) == (1,"ganador")
    assert calcular_puntos(1,1,2,0) == (0,"fallo")
    print("✅ Tests OK")
