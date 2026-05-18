from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import json
import psycopg2.extras
from groq import Groq

app = Flask(__name__)
CORS(app)

# ======================
# 🔐 AI CLIENT
# ======================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ======================
# 🗄️ POSTGRES CONNECT
# ======================
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port="5432",
    sslmode="require"
)

conn.autocommit = True
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ======================
# 🧱 INIT TABLE
# ======================
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY,
    name TEXT,
    surname TEXT,
    nickname TEXT,
    image TEXT,
    personality TEXT,
    style TEXT,
    moods JSONB
);
""")


# ======================
# 🔥 SEED DATA (ONLY ONCE)
# ======================
def seed_data():
    cur.execute("SELECT COUNT(*) FROM students")
    count = cur.fetchone()["count"]

    if count > 0:
        return

    students = [
        (1, "Adrian", "Červenka", "chilli peppers",
         "https://www.odzadu.sk/wp-content/uploads/2026/03/adrian-zo-sou-ruza-pre-nevestu.jpg",
         "sebavedomý frajer", "krátke správy 😎",
         {"neutral":"ego","flirt":"sexy ego","friendly":"fake friend","nahnevana":"arogantný"}),

        (2, "Janka", "Špenáová", "Špeňa",
         "https://www.stvr.sk/media/a501/image/file/1/1000/janka-pcs.jpg",
         "milá kuchárka", "emoji 😂❤️",
         {"neutral":"veselá","flirt":"cute","friendly":"ukecaná","nahnevana":"pasívna agresia"}),

        (3, "Markus", "Martiš", "cigga",
         "https://pbs.twimg.com/media/GYpgQMJXQAAtqkP.jpg",
         "model hráč", "flirt 😏",
         {"neutral":"ready","flirt":"extreme","friendly":"cool","nahnevana":"ignore"}),

        (4, "Elizabeth", "RolsRojs", "queen",
         "https://img.topky.sk/320px/1164133.jpg",
         "chaos party girl", "emoji 😂🔥",
         {"neutral":"random","flirt":"wild","friendly":"hyper","nahnevana":"toxic"}),

        (5, "Versace", "Klúčenka", "Gucci",
         "https://cdn.britannica.com/24/270724-050-ADD7DC96/donatella-versace-2024-vanity-fair-oscar-party-march-10-2024-beverly-hills-california.jpg",
         "luxus diva", "💅",
         {"neutral":"high class","flirt":"luxury","friendly":"fake nice","nahnevana":"elite rage"}),

        (6, "Ctibor", "Cyril", "Čvajgla",
         "https://www.asb.sk/wp-content/uploads/2023/01/ASB_05_10_2022_-6-of-9-min-e1669667094611.jpg",
         "starší muž", "pokojný",
         {"neutral":"serious","flirt":"secret","friendly":"wise","nahnevana":"closed"}),

        (7, "Lukáš", "Sfúkaš", "Bongo",
         "https://upload.wikimedia.org/wikipedia/commons/3/34/Luk%C3%A1%C5%A1_Latin%C3%A1k_2015.jpg",
         "vtipný chaos", "😂",
         {"neutral":"random","flirt":"weird","friendly":"funny","nahnevana":"sarkazmus"}),

        (8, "Roman", "Evka", "detičky krásne",
         "https://img.topky.sk/320px/1039568.jpg",
         "emocionálny", "😢",
         {"neutral":"smutný","flirt":"intense","friendly":"citlivý","nahnevana":"drama"}),

        (9, "Tomáš", "Maštalír", "herec",
         "https://image.smedata.sk/image/w625-h0/1ef88af3-e0d8-6470-9f8e-7b51221e482c.jpg",
         "normálny chill", "normálne",
         {"neutral":"ok","flirt":"light","friendly":"nice","nahnevana":"short"}),

        (10, "Patrik", "Vrbovský", "Rytmus",
         "https://i1.sndcdn.com/avatars-000003218454-hyqoka-t1080x1080.jpg",
         "troll rapper", "irónia 😂",
         {"neutral":"funny","flirt":"sarcasm","friendly":"troll","nahnevana":"attack"}),
    ]

    cur.executemany("""
        INSERT INTO students (id, name, surname, nickname, image, personality, style, moods)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, [
        (s[0], s[1], s[2], s[3], s[4], s[5], s[6], json.dumps(s[7]))
        for s in students
    ])


seed_data()


# ====================================================================
# 📈 VLASTNÝ BUBBLE SORT ALGORITMUS (Splnenie úlohy za 2 body)
# ====================================================================
def bubble_sort(data, key, reverse=False):
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            
            # Pre správne porovnávanie textov (Meno A-Z) zhodíme reťazce na malé písmená
            val_a = str(data[j][key]).lower() if isinstance(data[j][key], str) else data[j][key]
            val_b = str(data[j + 1][key]).lower() if isinstance(data[j + 1][key], str) else data[j + 1][key]

            swap = False
            if reverse:
                if val_a < val_b:
                    swap = True
            else:
                if val_a > val_b:
                    swap = True

            if swap:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data


# ====================================================================
# 📥 GET STUDENTS (S vlastným triedením na základe požiadavky z frontendu)
# ====================================================================
@app.route("/students", methods=["GET"])
def get_students():
    # Získanie parametra "sort" z URL (napr. /students?sort=name_asc)
    sort_by = request.args.get("sort", "id_asc").strip().lower()
    
    # Vytiahneme všetkých študentov z DB bez zoradenia v SQL
    cur.execute("SELECT * FROM students")
    rows = cur.fetchall()

    # Vlastný sorting na základe požiadavky z frontendu (Splnenie bonusu za 3 body)
    if sort_by == "name_asc":
        rows = bubble_sort(rows, key="name", reverse=False)
        
    elif sort_by == "name_desc":
        rows = bubble_sort(rows, key="name", reverse=True)
        
    elif sort_by == "age_asc":
        rows = bubble_sort(rows, key="age", reverse=False)
        
    elif sort_by == "age_desc":
        rows = bubble_sort(rows, key="age", reverse=True)
        
    else:  # Predvolené zoradenie (id_asc alebo akýkoľvek iný vstup)
        rows = bubble_sort(rows, key="id", reverse=False)

    return jsonify({"students": rows})


# ======================
# 💬 CHAT AI
# ======================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_message = data.get("message")
    character = data.get("character")
    mood = data.get("mood", "neutral")

    if not character:
        return jsonify({"reply": "Chýba postava 💀"})

    mood_description = character.get("moods", {}).get(mood, "normal")

    system_prompt = f"""
    Si {character["name"]} {character["surname"]} ({character["nickname"]}).

    Osobnosť: {character["personality"]}
    Štýl: {character["style"]}
    Nálada: {mood_description}

    PRAVIDLÁ:
    - krátke odpovede (1–2 vety)
    - emoji 😎
    - roleplay
    - nikdy nevychádzaj z role
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_completion_tokens=200
        )

        return jsonify({"reply": completion.choices[0].message.content})

    except Exception as e:
        return jsonify({"reply": str(e)})


# ======================
# 🚀 RUN (RENDER SAFE)
# ======================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )