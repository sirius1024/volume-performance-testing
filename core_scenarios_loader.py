import os

def _parse_value(v):
    s = v.strip()
    if s.endswith("G") or s.endswith("M") or s.endswith("K"):
        return s
    try:
        return int(s)
    except:
        return s

def load_core_scenarios(path: str):
    if not os.path.exists(path):
        return {"fio": [], "dd": []}
    fio = []
    dd = []
    section = None
    current = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ln = line.strip()
            if not ln:
                continue
            if ln.startswith("fio:"):
                section = "fio"
                continue
            if ln.startswith("dd:"):
                section = "dd"
                continue
            if ln.startswith("-"):
                if section == "fio":
                    current = {}
                    fio.append(current)
                elif section == "dd":
                    current = {}
                    dd.append(current)
                ln = ln[1:].strip()
            if ":" in ln and current is not None:
                k, v = ln.split(":", 1)
                k = k.strip()
                v = v.strip()
                current[k] = _parse_value(v)
    return {"fio": fio, "dd": dd}

