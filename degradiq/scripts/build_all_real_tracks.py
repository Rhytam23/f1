import fastf1
import numpy as np
import json

fastf1.Cache.enable_cache('data/cache')

TRACK_CONFIGS = [
    {
        "key": "silverstone",
        "cache": "data/cache",
        "event": "British Grand Prix",
        "name": "SILVERSTONE (BRITISH GP)",
        "fullName": "Silverstone Circuit — British Grand Prix",
        "lengthKm": "5.891 km",
        "highSpeedPct": "78%",
        "bankingAngle": "1.5°"
    },
    {
        "key": "suzuka",
        "cache": "data/cache",
        "event": "Japanese Grand Prix",
        "name": "SUZUKA (JAPANESE GP)",
        "fullName": "Suzuka Circuit — Japanese Grand Prix",
        "lengthKm": "5.807 km",
        "highSpeedPct": "80%",
        "bankingAngle": "2.5°"
    },
    {
        "key": "monza",
        "cache": "degradiq/data_cache",
        "event": "Italian Grand Prix",
        "name": "MONZA (ITALIAN GP)",
        "fullName": "Autodromo Nazionale Monza — Italian Grand Prix",
        "lengthKm": "5.793 km",
        "highSpeedPct": "85%",
        "bankingAngle": "1.0°"
    },
    {
        "key": "bahrain",
        "cache": "degradiq/data_cache",
        "event": "Bahrain Grand Prix",
        "name": "BAHRAIN (BAHRAIN GP)",
        "fullName": "Bahrain International Circuit — Sakhir",
        "lengthKm": "5.412 km",
        "highSpeedPct": "68%",
        "bankingAngle": "0.0°"
    },
    {
        "key": "spain",
        "cache": "degradiq/data_cache",
        "event": "Spanish Grand Prix",
        "name": "BARCELONA-CATALUNYA (SPANISH GP)",
        "fullName": "Circuit de Barcelona-Catalunya — Spanish Grand Prix",
        "lengthKm": "4.657 km",
        "highSpeedPct": "72%",
        "bankingAngle": "1.8°"
    }
]

# Corner names and telemetry defaults
CORNER_NAMES = {
    "silverstone": {
        1: "Turn 1 (Abbey)", 2: "Turn 2 (Farm)", 3: "Turn 3 (Village)", 4: "Turn 4 (The Loop)", 5: "Turn 5 (Aintree)",
        6: "Turn 6 (Brooklands)", 7: "Turn 7 (Luffield)", 8: "Turn 8 (Woodcote)", 9: "Turn 9 (Copse)", 10: "Turn 10 (Maggotts)",
        11: "Turn 11 (Becketts 1)", 12: "Turn 12 (Becketts 2)", 13: "Turn 13 (Chapel)", 14: "Turn 14 (Stowe)",
        15: "Turn 15 (Vale)", 16: "Turn 16 (Club 1)", 17: "Turn 17 (Club 2)", 18: "Turn 18 (Club Exit)"
    },
    "suzuka": {
        1: "Turn 1 (First Corner)", 2: "Turn 2", 3: "Turn 3 (S Curves)", 4: "Turn 4", 5: "Turn 5",
        6: "Turn 6", 7: "Turn 7 (Dunlop)", 8: "Turn 8 (Degner 1)", 9: "Turn 9 (Degner 2)", 10: "Turn 10",
        11: "Turn 11 (Hairpin)", 12: "Turn 12 (200R)", 13: "Turn 13 (Spoon 1)", 14: "Turn 14 (Spoon 2)",
        15: "Turn 15 (130R)", 16: "Turn 16 (Casio Chicane)", 17: "Turn 17", 18: "Turn 18 (Main Straight)"
    },
    "monza": {
        1: "Turn 1 (Prima Variante 1)", 2: "Turn 2 (Prima Variante 2)", 3: "Turn 3 (Curva Grande)",
        4: "Turn 4 (Variante della Roggia 1)", 5: "Turn 5 (Variante della Roggia 2)",
        6: "Turn 6 (Curva di Lesmo 1)", 7: "Turn 7 (Curva di Lesmo 2)", 8: "Turn 8 (Variante Ascari 1)",
        9: "Turn 9 (Variante Ascari 2)", 10: "Turn 10 (Variante Ascari 3)", 11: "Turn 11 (Curva Parabolica)"
    },
    "bahrain": {
        1: "Turn 1 (Michael Schumacher)", 2: "Turn 2", 3: "Turn 3", 4: "Turn 4", 5: "Turn 5",
        6: "Turn 6", 7: "Turn 7", 8: "Turn 8", 9: "Turn 9", 10: "Turn 10 (Tight Hairpin)",
        11: "Turn 11", 12: "Turn 12", 13: "Turn 13", 14: "Turn 14", 15: "Turn 15"
    },
    "spain": {
        1: "Turn 1 (Elf)", 2: "Turn 2", 3: "Turn 3 (Renault)", 4: "Turn 4 (Repsol)", 5: "Turn 5 (Seat)",
        6: "Turn 6", 7: "Turn 7", 8: "Turn 8", 9: "Turn 9 (Campsa)", 10: "Turn 10 (La Caixa)",
        11: "Turn 11", 12: "Turn 12 (Banc Sabadell)", 13: "Turn 13", 14: "Turn 14 (Catalunya Final)"
    }
}

out_tracks = {}

for cfg in TRACK_CONFIGS:
    key = cfg["key"]
    fastf1.Cache.enable_cache(cfg["cache"])
    session = fastf1.get_session(2023, cfg["event"], 'R')
    session.load(telemetry=True, laps=True, weather=False)
    circuit_info = session.get_circuit_info()
    fastest_lap = session.laps.pick_fastest()
    
    # Telemetry
    pos = fastest_lap.get_pos_data()
    pos = pos[(pos['X'] != 0) | (pos['Y'] != 0)]
    
    angle = np.radians(circuit_info.rotation)
    rot_mat = np.array([
        [np.cos(angle), np.sin(angle)],
        [-np.sin(angle), np.cos(angle)]
    ])
    
    xy = pos[['X', 'Y']].to_numpy()
    xy_rot = np.matmul(xy, rot_mat)
    xy_svg = xy_rot.copy()
    xy_svg[:, 1] = -xy_svg[:, 1]
    
    corners_xy = circuit_info.corners[['X', 'Y']].to_numpy()
    corners_rot = np.matmul(corners_xy, rot_mat)
    corners_svg = corners_rot.copy()
    corners_svg[:, 1] = -corners_svg[:, 1]
    
    # Scale to canvas 1000x450 with padding 50
    padding = 50
    min_x, max_x = xy_svg[:, 0].min(), xy_svg[:, 0].max()
    min_y, max_y = xy_svg[:, 1].min(), xy_svg[:, 1].max()
    w = max_x - min_x
    h = max_y - min_y
    
    scale = min((1000 - 2 * padding) / w, (450 - 2 * padding) / h)
    off_x = padding + ((1000 - 2 * padding) - w * scale) / 2 - min_x * scale
    off_y = padding + ((450 - 2 * padding) - h * scale) / 2 - min_y * scale
    
    pts_scaled = xy_svg * scale + np.array([off_x, off_y])
    c_pts_scaled = corners_svg * scale + np.array([off_x, off_y])
    
    # Sample points for SVG path
    step = max(1, len(pts_scaled) // 180)
    pts_sub = pts_scaled[::step]
    path_d = f"M {pts_sub[0,0]:.1f} {pts_sub[0,1]:.1f} " + " ".join([f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_sub[1:]]) + " Z"
    
    # Format corners
    corners_list = []
    names_dict = CORNER_NAMES.get(key, {})
    for i, (_, row) in enumerate(circuit_info.corners.iterrows()):
        num = int(row['Number'])
        cx = round(float(c_pts_scaled[i, 0]), 1)
        cy = round(float(c_pts_scaled[i, 1]), 1)
        cname = names_dict.get(num, f"Turn {num}")
        
        # Determine speed category
        if "Hairpin" in cname or "Chicane" in cname or num in [1, 4, 10]:
            ctype = "Heavy Braking"
            braking = 120
            entry = 280
            apex = 95
            exit_spd = 160
        elif "High Speed" in cname or "130R" in cname or "Curva Grande" in cname:
            ctype = "High Speed Sweeper"
            braking = 0
            entry = 300
            apex = 270
            exit_spd = 295
        else:
            ctype = "Medium Speed"
            braking = 70
            entry = 240
            apex = 160
            exit_spd = 210
            
        corners_list.append({
            "id": num,
            "name": cname,
            "x": cx,
            "y": cy,
            "type": ctype,
            "braking": braking,
            "entry": entry,
            "apex": apex,
            "exit": exit_spd
        })
        
    out_tracks[key] = {
        "name": cfg["name"],
        "fullName": cfg["fullName"],
        "lengthKm": cfg["lengthKm"],
        "cornerCount": len(corners_list),
        "highSpeedPct": cfg["highSpeedPct"],
        "bankingAngle": cfg["bankingAngle"],
        "path": path_d,
        "corners": corners_list
    }
    print(f"Processed {key}: {len(corners_list)} corners, {len(pts_sub)} path nodes.")

with open("frontend/real_tracks.js", "w", encoding="utf-8") as f:
    f.write("// Autogenerated authentic F1 circuit geometries from FastF1 telemetry\n")
    f.write("const TRACK_DEFINITIONS = ")
    json.dump(out_tracks, f, indent=2)
    f.write(";\n")

print("Generated frontend/real_tracks.js successfully!")
