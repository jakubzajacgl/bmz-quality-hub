import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from groq import Groq

app = Flask(__name__)

# === BEZPIECZNA KONFIGURACJA API GROQ ===
# os.environ.get pobierze klucz z ustawień serwera Render lub Twojego komputera
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Jeśli klucza nie ma w systemie (np. podczas testów lokalnych),
# możesz zostawić warunek, ale NIE wpisuj tu prawdziwego klucza przed wysyłką na GitHub!
if not GROQ_API_KEY:
    # Możesz tu zostawić pusty string lub podnieść błąd
    GROQ_API_KEY = ""

client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"


def clean_json_response(text):
    """Wyciąga czysty JSON z odpowiedzi AI, usuwając markdown ```json ... ```"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# === LISTA MODUŁÓW ===
MODULES = [
    {"id": "8d", "title": "8D Report", "icon": "fa-tools", "desc": "Reklamacje i rozwiązywanie problemów."},
    {"id": "a3", "title": "Raport A3", "icon": "fa-file-alt", "desc": "Lean Problem Solving."},
    {"id": "spc", "title": "SPC", "icon": "fa-chart-line", "desc": "Statystyczne Sterowanie Procesem."},
    {"id": "msa", "title": "MSA", "icon": "fa-ruler-combined", "desc": "Analiza Systemów Pomiarowych."},
    {"id": "pareto", "title": "Diagram Pareto", "icon": "fa-chart-bar", "desc": "Analiza 80/20."},
    {"id": "control_plan", "title": "Control Plan", "icon": "fa-clipboard-list",
     "desc": "Plan Kontroli zintegrowany z FMEA."},
    {"id": "vda", "title": "VDA 6.3 Audit", "icon": "fa-clipboard-check", "desc": "Zarządzanie audytami procesu."},
    {"id": "fmea", "title": "PFMEA", "icon": "fa-exclamation-triangle", "desc": "Analiza Przyczyn i Skutków Wad."},
    {"id": "ishikawa", "title": "Ishikawa 6M", "icon": "fa-fish", "desc": "Analiza przyczyn 6M."}
]


# === ŚCIEŻKI WIDOKÓW ===
@app.route('/')
def index():
    return render_template('index.html', modules1=MODULES[:5], modules2=MODULES[5:])


@app.route('/module/<module_id>')
def render_module(module_id):
    mapping = {
        "8d": "module_8D.html", "a3": "a3.html", "spc": "spc.html",
        "msa": "msa.html", "pareto": "pareto.html", "control_plan": "control_plan.html",
        "vda": "vda.html", "fmea": "fmea.html", "ishikawa": "ishikawa.html"
    }
    return render_template(mapping.get(module_id, "index.html"))


# --- BRAKUJĄCE ŚCIEŻKI BAZY WIEDZY I KONTAKTU ---
@app.route('/baza-wiedzy')
def knowledge_base():
    return render_template('knowledge_base.html', modules=MODULES)


@app.route('/kontakt')
def kontakt():
    return render_template('kontakt.html')


# --- BRAKUJĄCA ŚCIEŻKA DLA PREZENTACJI PDF ---
@app.route('/presentation/<module_id>')
def serve_presentation(module_id):
    presentations_dir = os.path.join(app.static_folder, 'presentations')
    filename = f"{module_id}.pdf"
    filepath = os.path.join(presentations_dir, filename)

    if os.path.exists(filepath):
        return send_from_directory(presentations_dir, filename)
    else:
        return f"""
        <div style="font-family: 'Inter', sans-serif; padding: 50px; text-align: center; color: white; background: #0b1120; height: 100vh;">
            <h2 style="color: #ef4444; font-size: 2.5rem; margin-bottom: 20px;">Brak pliku prezentacji</h2>
            <p style="font-size: 1.2rem; color: #94a3b8; margin-bottom: 10px;">Plik szkoleniowy <b>{filename}</b> nie został jeszcze załączony do platformy.</p>
            <p style="font-size: 1rem; color: #cbd5e1; margin-bottom: 30px;">Aby to naprawić, wyeksportuj prezentację jako PDF i wrzuć ją do folderu <code>static/presentations/</code></p>
            <button onclick="window.history.back()" style="padding: 12px 30px; cursor: pointer; background: #00AEEF; border: none; border-radius: 8px; color: black; font-weight: bold; font-size: 1.1rem; transition: 0.2s;">&laquo; Wróć do Bazy Wiedzy</button>
        </div>
        """, 404


# === REWIZJA API 8D ===
@app.route('/api/generate_8d', methods=['POST'])
def generate_8d():
    data = request.json or {}
    try:
        sys_prompt = """Jesteś Ekspertem IATF 16949. Wygeneruj profesjonalny raport 8D w JSON. 
Wymagane klucze:
"d3": [{"action": "Tytuł akcji", "owner": "Rola", "date": "Termin"}],
"d4": "Szczegółowa analiza 5Why prowadząca do przyczyny źródłowej",
"d5": [{"action": "Opis działania korygującego", "owner": "Rola", "date": "Termin"}],
"d6": [{"action": "Opis walidacji", "signature": "Data/Podpis"}],
"d7": "Działania zapobiegawcze systemowe",
"d8": "Gratulacje dla zespołu"
Zwróć TYLKO czysty obiekt JSON."""

        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, temperature=0.2, response_format={"type": "json_object"}
        )
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === API SPC (REKOMENDACJA) ===
@app.route('/api/generate_spc_ai', methods=['POST'])
def generate_spc_ai():
    data = request.json or {}
    try:
        prompt = f"Zanalizuj wyniki SPC dla procesu {data.get('char')}: Cp={data.get('cp')}, Cpk={data.get('cpk')}. Co inżynier powinien zrobić? Max 3 zdania."
        chat = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME)
        return jsonify({"recommendation": chat.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === API FMEA & CONTROL PLAN ===
@app.route('/api/generate_fmea', methods=['POST'])
def generate_fmea():
    data = request.json or {}
    try:
        sys_prompt = "Ekspert PFMEA. Zwróć JSON: failure_mode, effect, sev, cause, occ, controls, det, ap (H/M/L)."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user",
                                                                  "content": f"Operacja: {data.get('operation')}, Wymaganie: {data.get('requirement')}"}],
            model=MODEL_NAME, response_format={"type": "json_object"}
        )
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_control_plan', methods=['POST'])
def generate_control_plan():
    data = request.json or {}
    try:
        # Ten endpoint bierze wiersz z FMEA i zwraca pełne kolumny do Control Planu
        sys_prompt = "Ekspert Control Plan. Na podstawie wiersza PFMEA zaproponuj: product_char, process_char, spec, technique, sample, frequency, method, reaction. Zwróć JSON."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, response_format={"type": "json_object"}
        )
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- BRAKUJĄCE ENDPOINTY AI DLA RESZTY MODUŁÓW (ŻEBY NIE RZUCAŁY BŁĘDÓW) ---
@app.route('/api/generate_a3', methods=['POST'])
def generate_a3():
    data = request.json or {}
    try:
        sys_prompt = "Generate A3 report JSON with keys: current_condition, goals, analysis, countermeasures, plan, followup. Language: Polish."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, temperature=0.3)
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_msa_ai', methods=['POST'])
def generate_msa_ai():
    data = request.json or {}
    try:
        prompt = f"Zanalizuj wskaźniki MSA: %GRR={data.get('grr')}%, ndc={data.get('ndc')}. Oceń system."
        chat = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME)
        return jsonify({"recommendation": chat.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_pareto_ai', methods=['POST'])
def generate_pareto_ai():
    data = request.json or {}
    try:
        prompt = f"Oceń te dane Pareto i wskaż nieliczne ważne problemy (Vital Few do 80%). Dane: {data.get('pareto_data')}"
        chat = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=MODEL_NAME)
        return jsonify({"recommendation": chat.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/vda_global_analysis', methods=['POST'])
def vda_global_analysis():
    data = request.json or {}
    try:
        sys_prompt = "You are a VDA 6.3 Auditor. Respond in JSON with keys: 'verdict', 'summary', 'top_actions'. Language: Polish."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, temperature=0.3)
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/generate_ishikawa', methods=['POST'])
def generate_ishikawa():
    data = request.json or {}
    try:
        sys_prompt = "Generate Ishikawa 6M JSON. Keys: 'man', 'machine', 'material', 'method', 'measurement', 'environment'. Language: Polish."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, temperature=0.3)
        return jsonify(json.loads(clean_json_response(chat.choices[0].message.content)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze_fmea', methods=['POST'])
def analyze_fmea_table():
    data = request.json or {}
    try:
        sys_prompt = "You are a Senior Quality Manager. Analyze FMEA rows. Output pure text only."
        chat = client.chat.completions.create(
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": str(data)}],
            model=MODEL_NAME, temperature=0.3)
        return jsonify({"recommendation": chat.choices[0].message.content.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)