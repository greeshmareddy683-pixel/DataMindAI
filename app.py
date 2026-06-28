import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.io as pio
import json, os, tempfile, datetime, io, re, zipfile
from groq import Groq
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── MASTER CSS — ChatGPT-grade polish ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.stApp { background: #212121; color: #ececec; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #171717 !important;
    border-right: 1px solid #2f2f2f !important;
    width: 260px !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebar"] * { color: #ececec !important; }
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #c5c5c5 !important;
    border: none !important;
    text-align: left !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    width: 100% !important;
    transition: background 0.15s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2a2a2a !important;
    color: #ececec !important;
}

/* ── Hide Streamlit chrome ── */
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { display: none; }
.stDeployButton { display: none; }
div[data-testid="stToolbar"] { display: none; }

/* ── Chat container ── */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
}
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 0;
    scroll-behavior: smooth;
}

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    padding: 12px 20px;
    animation: fadeUp 0.2s ease;
}
.msg-user .bubble {
    background: #2f2f2f;
    color: #ececec;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 70%;
    font-size: 0.92rem;
    line-height: 1.6;
    white-space: pre-wrap;
}
.msg-ai {
    display: flex;
    justify-content: flex-start;
    padding: 12px 20px;
    gap: 12px;
    animation: fadeUp 0.2s ease;
}
.ai-avatar {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #10a37f, #0d8a6c);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0; margin-top: 2px;
}
.msg-ai .bubble {
    background: transparent;
    color: #ececec;
    max-width: 80%;
    font-size: 0.92rem;
    line-height: 1.7;
}

/* ── Welcome screen ── */
.welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
    padding: 40px 20px;
}
.welcome-logo {
    width: 56px; height: 56px;
    background: linear-gradient(135deg, #10a37f, #0d8a6c);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; margin-bottom: 20px;
}
.welcome-title {
    font-size: 1.8rem; font-weight: 600;
    color: #ececec; margin-bottom: 8px; text-align: center;
}
.welcome-sub {
    font-size: 0.9rem; color: #888; margin-bottom: 36px; text-align: center;
}
.chip-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    max-width: 560px;
    width: 100%;
}
.chip {
    background: #2f2f2f;
    border: 1px solid #3f3f3f;
    border-radius: 12px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
}
.chip:hover { background: #3a3a3a; border-color: #555; }
.chip-icon { font-size: 1rem; margin-bottom: 6px; }
.chip-text { font-size: 0.82rem; color: #c5c5c5; line-height: 1.4; }

/* ── SQL pill ── */
.sql-block {
    background: #1a1a1a;
    border: 1px solid #3f3f3f;
    border-left: 3px solid #10a37f;
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'Menlo', 'Monaco', monospace;
    font-size: 0.78rem;
    color: #7dd3a8;
    margin: 8px 0;
    white-space: pre-wrap;
    word-break: break-all;
}
.sql-label {
    font-size: 0.7rem;
    color: #10a37f;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
}

/* ── Tool badge ── */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #1e2e28;
    border: 1px solid #10a37f33;
    color: #10a37f;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 4px 4px 8px 0;
}

/* ── Error / info ── */
.err-box {
    background: #2d1a1a;
    border: 1px solid #ef444433;
    border-radius: 8px;
    padding: 10px 14px;
    color: #f87171;
    font-size: 0.84rem;
    margin: 6px 0;
}
.info-box {
    background: #1a2a25;
    border: 1px solid #10a37f33;
    border-radius: 8px;
    padding: 10px 14px;
    color: #6ee7b7;
    font-size: 0.84rem;
    margin: 6px 0;
}

/* ── Input bar ── */
.input-bar-wrap {
    padding: 16px 20px 24px;
    background: #212121;
    border-top: 1px solid #2f2f2f;
}
.input-row {
    display: flex;
    align-items: center;
    background: #2f2f2f;
    border: 1px solid #3f3f3f;
    border-radius: 14px;
    padding: 4px 8px 4px 16px;
    gap: 8px;
    transition: border-color 0.2s;
    max-width: 800px;
    margin: 0 auto;
}
.input-row:focus-within { border-color: #10a37f55; }

/* ── Streamlit chat_input override ── */
[data-testid="stChatInput"] {
    background: #2f2f2f !important;
    border: 1px solid #3f3f3f !important;
    border-radius: 14px !important;
    max-width: 800px !important;
    margin: 0 auto !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #ececec !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #10a37f55 !important;
    box-shadow: 0 0 0 3px #10a37f11 !important;
}
[data-testid="stChatInputSubmitButton"] svg { fill: #10a37f !important; }

/* ── Plotly charts ── */
.js-plotly-plot { border-radius: 12px; overflow: hidden; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2f2f2f;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background: #2f2f2f !important;
    color: #c5c5c5 !important;
    border: 1px solid #3f3f3f !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 5px 12px !important;
    transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
    background: #3a3a3a !important;
    border-color: #10a37f55 !important;
    color: #ececec !important;
}

/* ── Sidebar section headers ── */
.sb-section {
    padding: 8px 14px 4px;
    font-size: 0.68rem;
    font-weight: 600;
    color: #666 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── New chat button ── */
.new-chat-btn > button {
    background: transparent !important;
    border: 1px solid #3f3f3f !important;
    color: #c5c5c5 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    padding: 7px 12px !important;
    width: 100% !important;
    margin-bottom: 4px !important;
    transition: all 0.15s !important;
}
.new-chat-btn > button:hover {
    background: #2a2a2a !important;
    border-color: #555 !important;
    color: #ececec !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1a1a;
    border-radius: 10px;
    padding: 3px;
    border: 1px solid #2f2f2f;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    color: #888 !important;
    background: transparent !important;
    border-radius: 7px !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    background: #2f2f2f !important;
    color: #ececec !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #1a1a1a;
    border: 1px solid #2f2f2f;
    border-radius: 8px;
}
[data-testid="stExpander"] summary { color: #888 !important; font-size: 0.8rem !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #10a37f !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3f3f3f; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #555; }

/* ── Animations ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
    40%            { transform: scale(1); opacity: 1; }
}
.typing-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: #10a37f;
    border-radius: 50%;
    animation: pulse 1.2s infinite ease-in-out;
    margin: 0 2px;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

/* ── Dashboard card ── */
.dash-card {
    background: #1a1a1a;
    border: 1px solid #2f2f2f;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
}
.dash-title { font-size: 0.82rem; color: #888; margin-bottom: 10px; font-weight: 500; }

/* ── History item ── */
.hist-row {
    background: #1a1a1a;
    border: 1px solid #2f2f2f;
    border-radius: 8px;
    padding: 9px 12px;
    margin: 4px 0;
    cursor: pointer;
    transition: all 0.15s;
}
.hist-row:hover { border-color: #10a37f55; background: #1e2a25; }
.hist-q { font-size: 0.82rem; color: #c5c5c5; }
.hist-meta { font-size: 0.7rem; color: #555; margin-top: 2px; }

/* ── Select box ── */
[data-testid="stSelectbox"] > div > div {
    background: #2f2f2f !important;
    border: 1px solid #3f3f3f !important;
    border-radius: 8px !important;
    color: #ececec !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label { font-size: 0.82rem !important; color: #c5c5c5 !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION DEFAULTS ───────────────────────────────────────────────────────────
DEFAULTS = {
    "messages": [],
    "chat_history": [],
    "auto_send": None,
    "db_path": "ecommerce.db",
    "extra_dbs": {},
    "active_db": "ecommerce.db",
    "query_history": [],
    "favorites": [],
    "dashboard_pins": [],
    "sidebar_view": "chat",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── GROQ CLIENT ───────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ── DATABASE HELPERS ──────────────────────────────────────────────────────────
def find_any_db():
    """Auto-detect any .db file in the current working directory."""
    for f in os.listdir("."):
        if f.endswith((".db", ".sqlite", ".sqlite3")):
            return f
    return None

def current_db():
    """Always return a valid, existing db path. Fall back to auto-detect."""
    path = st.session_state.active_db
    if os.path.exists(path):
        return path
    # Try to find any .db file nearby
    found = find_any_db()
    if found:
        st.session_state.active_db = found
        return found
    return path  # return original so error message is meaningful

def get_schema(db_path=None):
    db_path = db_path or current_db()
    if not os.path.exists(db_path):
        return {"schema": {}, "error": f"Database not found: {db_path}"}
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    schema = {}
    for t in tables:
        c.execute(f"PRAGMA table_info({t})")
        schema[t] = [{"col": r[1], "type": r[2]} for r in c.fetchall()]
    conn.close()
    return {"schema": schema, "db": db_path}

def execute_query(sql, db_path=None):
    db_path = db_path or current_db()
    sql = sql.strip().rstrip(";")
    if not sql.upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}
    if not os.path.exists(db_path):
        return {"error": f"Database file not found: {db_path}"}
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return {"columns": list(df.columns), "rows": df.values.tolist()[:100],
                "count": len(df), "df": df, "sql": sql}
    except Exception as e:
        return {"error": str(e)}

def sanitize_col(col, df):
    """If col not in df, try to find the closest real column name."""
    if col in df.columns:
        return col
    # Try case-insensitive match
    for c in df.columns:
        if c.lower() == col.lower():
            return c
    # Try stripping common SQL expressions: COUNT(id) -> count, SUM(total) -> total
    import re as _re
    stripped = _re.sub(r'\w+\((\w+)\)', r'\1', col).lower()
    for c in df.columns:
        if c.lower() == stripped or stripped in c.lower():
            return c
    # Last resort: pick last column for y, first for x
    if len(df.columns) >= 2:
        return df.columns[-1] if col == col else df.columns[0]
    return col

def generate_chart(chart_type, sql, x_col, y_col, title="Chart", db_path=None):
    result = execute_query(sql, db_path)
    if "error" in result:
        return result
    df = result["df"]
    # Auto-fix column names if model used raw expressions instead of aliases
    x_col = sanitize_col(x_col, df)
    y_col = sanitize_col(y_col, df)
    try:
        kw = dict(template="plotly_dark", title=title)
        if chart_type == "bar":
            fig = px.bar(df, x=x_col, y=y_col, color=x_col, **kw)
        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=y_col, markers=True, **kw)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_col, **kw)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_col, y=y_col, **kw)
        else:
            return {"error": f"Unknown chart type: {chart_type}"}
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ececec",
            margin=dict(l=16, r=16, t=40, b=16),
        )
        fig.update_traces(marker_line_width=0)
        return {"fig": fig, "type": "chart", "df": df, "sql": sql, "chart_title": title}
    except Exception as e:
        return {"error": str(e)}

def generate_flowchart(diagram_type, description, db_path=None):
    schema = get_schema(db_path)["schema"]
    if diagram_type == "er":
        lines = ["erDiagram"]
        for t, cols in schema.items():
            col_lines = "\n    ".join(f'{c["type"] or "TEXT"} {c["col"]}' for c in cols)
            lines.append(f'  {t.upper()} {{\n    {col_lines}\n  }}')
        lines += [
            '  ORDERS ||--o{ CUSTOMERS : "placed by"',
            '  ORDERS ||--o{ PRODUCTS : "contains"',
            '  INVENTORY ||--o{ PRODUCTS : "tracks"',
        ]
        return {"mermaid": "\n".join(lines), "type": "flowchart"}
    mermaid = """flowchart TD
    A([Customer Places Order]) --> B[Order Created - PENDING]
    B --> C{Payment Verified?}
    C -->|Yes| D[Order SHIPPED]
    C -->|No| E[Order CANCELLED]
    D --> F[Order DELIVERED]
    F --> G([Inventory Updated])"""
    return {"mermaid": mermaid, "type": "flowchart"}

def explain_data(sql, question, db_path=None):
    result = execute_query(sql, db_path)
    if "error" in result:
        return result
    return {"context": f"Q: {question} | Rows: {result['count']}", "df": result["df"], "sql": sql}

# ── TOOL DEFINITIONS ──────────────────────────────────────────────────────────
DISPATCH = {
    # db_path intentionally NEVER passed from AI — always use current_db()
    "get_schema":         lambda a: get_schema(),
    "execute_query":      lambda a: execute_query(a["sql"]),
    "generate_chart":     lambda a: generate_chart(a["chart_type"], a["sql"], a["x_col"], a["y_col"], a.get("title", "Chart")),
    "generate_flowchart": lambda a: generate_flowchart(a["diagram_type"], a["description"]),
    "explain_data":       lambda a: explain_data(a["sql"], a["question"]),
}

# db_path removed from ALL tool schemas so the model can NEVER hallucinate a path
TOOL_DEFS = [
    {"type": "function", "function": {"name": "get_schema", "description": "Get full database schema — all tables and column names.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "execute_query", "description": "Run a SELECT SQL query and return rows.", "parameters": {"type": "object", "properties": {"sql": {"type": "string", "description": "Valid SQLite SELECT statement"}}, "required": ["sql"]}}},
    {"type": "function", "function": {"name": "generate_chart", "description": "Generate a bar/line/pie/scatter chart. Use whenever user asks for a chart, graph, visual, or plot.", "parameters": {"type": "object", "properties": {"chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"]}, "sql": {"type": "string"}, "x_col": {"type": "string"}, "y_col": {"type": "string"}, "title": {"type": "string"}}, "required": ["chart_type", "sql", "x_col", "y_col"]}}},
    {"type": "function", "function": {"name": "generate_flowchart", "description": "Generate ER diagram or process flowchart using Mermaid.", "parameters": {"type": "object", "properties": {"diagram_type": {"type": "string", "enum": ["er", "flow"]}, "description": {"type": "string"}}, "required": ["diagram_type", "description"]}}},
    {"type": "function", "function": {"name": "explain_data", "description": "Fetch data and provide plain-English insights and summary statistics.", "parameters": {"type": "object", "properties": {"sql": {"type": "string"}, "question": {"type": "string"}}, "required": ["sql", "question"]}}},
]

SYSTEM_PROMPT = """You are DataMind AI — a sharp, friendly database analyst. You speak plain English and give concise, useful answers.

SQLite e-commerce database — EXACT tables and columns (never invent others):
  customers : id, name, email, city, created_at
  products  : id, name, category, price, stock
  orders    : id, customer_id, product_id, quantity, total, status, order_date
  inventory : id, product_id, restock_date, quantity_added

STRICT RULES:
1. NEVER pass a db_path argument to any tool. The database path is handled automatically.
2. Use ONLY the exact column names listed above. Never guess or invent column names.
3. Revenue = orders.total. Join orders to products: products.id = orders.product_id.
4. ALWAYS use simple aliases in SQL. NEVER use raw expressions like COUNT(id) or SUM(total) as column names.
   CORRECT:   SELECT status, COUNT(id) AS count FROM orders GROUP BY status
   CORRECT:   SELECT name, SUM(total) AS revenue FROM ...
   WRONG:     COUNT(id) or SUM(orders.total) used directly as x_col or y_col
5. x_col and y_col in generate_chart must EXACTLY match the alias used in the SQL SELECT.
6. User asks for chart/graph/visual → call generate_chart.
7. User asks for diagram/ER/flowchart → call generate_flowchart.
8. Data questions → execute_query or explain_data.
9. After results give a short (2-3 sentence) plain-English insight.
10. If a query fails, explain exactly what went wrong. NEVER say 'try rephrasing'."""

# ── AGENT ─────────────────────────────────────────────────────────────────────
def run_agent(user_input):
    if not client:
        return "⚠️ Set GROQ_API_KEY in your .env file to enable responses.", []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in st.session_state.chat_history[-14:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_input})

    tool_results = []
    for _ in range(10):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=TOOL_DEFS,
                tool_choice="auto",
                max_tokens=2048,
            )
        except Exception as e:
            return f"⚠️ Groq API error: {str(e)}", tool_results

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                fn = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                    result = DISPATCH[fn](args)
                except Exception as e:
                    result = {"error": str(e)}
                tool_results.append({"tool": fn, "result": result})
                safe = {k: v for k, v in result.items() if k not in ("df", "fig")}
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(safe)})
        else:
            reply = msg.content or ""
            # Log SQL to history
            sql_match = re.search(r"```sql\s*(.*?)```", reply, re.DOTALL | re.IGNORECASE)
            if sql_match:
                st.session_state.query_history.append({
                    "query": user_input[:55],
                    "sql": sql_match.group(1).strip(),
                    "ts": datetime.datetime.now().strftime("%H:%M · %d %b"),
                })
            return reply, tool_results

    return "Analysis complete — see results above.", tool_results

# ── RENDER HELPERS ────────────────────────────────────────────────────────────
TOOL_ICONS = {
    "get_schema":         "🗂 Schema",
    "execute_query":      "⚡ Query",
    "generate_chart":     "📊 Chart",
    "generate_flowchart": "🔀 Diagram",
    "explain_data":       "🧠 Analysis",
}

def export_df(df, label="data"):
    csv = df.to_csv(index=False).encode()
    st.download_button("⬇ CSV", csv, f"{label}.csv", "text/csv",
                       key=f"csv_{label}_{id(df)}", use_container_width=False)

def export_png(fig, title="chart"):
    try:
        img = pio.to_image(fig, format="png", width=1000, height=520)
        st.download_button("⬇ PNG", img, f"{title}.png", "image/png",
                           key=f"png_{title}_{id(fig)}", use_container_width=False)
    except Exception:
        st.caption("`pip install kaleido` for PNG export")

def pin_chart(fig, df, title):
    st.session_state.dashboard_pins.append({
        "title": title,
        "fig_json": fig.to_json(),
        "df_csv": df.to_csv(index=False),
    })
    st.toast(f"📌 Pinned '{title}' to Dashboard", icon="✅")

def render_tool(tr, uid=""):
    tool = tr["tool"]
    result = tr["result"]

    st.markdown(f'<span class="tool-badge">{TOOL_ICONS.get(tool, tool)}</span>', unsafe_allow_html=True)

    if "error" in result:
        st.markdown(f'<div class="err-box">❌ {result["error"]}</div>', unsafe_allow_html=True)
        return

    # SQL preview
    if "sql" in result:
        st.markdown(f'<div class="sql-block"><div class="sql-label">SQL</div>{result["sql"]}</div>',
                    unsafe_allow_html=True)

    # Chart
    if "fig" in result:
        st.plotly_chart(result["fig"], use_container_width=True, config={"displayModeBar": False})
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            export_png(result["fig"], result.get("chart_title", "chart"))
        with c2:
            if "df" in result:
                export_df(result["df"], "chart_data")
        with c3:
            if st.button("📌 Pin to Dashboard", key=f"pin_{uid}_{id(result)}"):
                pin_chart(result["fig"], result.get("df", pd.DataFrame()), result.get("chart_title", "Chart"))

    # Mermaid diagram
    if "mermaid" in result:
        mermaid_html = f"""
        <div class="mermaid" style="background:#1a1a1a;padding:24px;border-radius:12px;text-align:center;">
        {result['mermaid']}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true,theme:'dark',securityLevel:'loose'}});</script>
        """
        components.html(mermaid_html, height=440, scrolling=True)
        with st.expander("Mermaid source"):
            st.code(result["mermaid"], language="text")

    # Data table
    if "df" in result and "fig" not in result:
        df = result["df"]
        st.dataframe(df.head(25), use_container_width=True, hide_index=True)
        export_df(df, "result")

    # Schema
    if "schema" in result:
        for table, cols in result["schema"].items():
            with st.expander(f"📋 {table}"):
                for c in cols:
                    st.caption(f"`{c['col']}` — {c['type'] or 'TEXT'}")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + new chat
    st.markdown('<div style="padding:16px 14px 8px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:1rem;font-weight:600;color:#ececec;margin-bottom:12px;">🧠 DataMind AI</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
        if st.button("✏️  New chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Nav tabs
    view = st.radio("", ["💬 Chat", "📁 Databases", "🕑 History", "⭐ Favorites", "📌 Dashboard"],
                    label_visibility="collapsed", key="sidebar_view_radio")
    st.markdown("---")

    # ── Chat tab ──
    if view == "💬 Chat":
        st.markdown('<div class="sb-section">Suggested</div>', unsafe_allow_html=True)
        suggestions = [
            "Top 5 products by revenue",
            "Sales by category — pie chart",
            "Monthly orders trend",
            "Customers by city — bar chart",
            "Cancelled vs delivered orders",
            "ER diagram",
            "Order process flowchart",
            "Low stock products",
            "Average order value",
            "Best selling categories",
        ]
        for q in suggestions:
            if st.button(q, key=f"sug_{q}", use_container_width=True):
                st.session_state.auto_send = q
                st.rerun()

    # ── Databases tab ──
    elif view == "📁 Databases":
        db_exists = os.path.exists(current_db())

        st.markdown('<div class="sb-section">Upload Your Database</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload .db / .sqlite file", type=["db", "sqlite", "sqlite3"], label_visibility="collapsed")
        if uploaded:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            tmp.write(uploaded.read())
            tmp.close()
            st.session_state.extra_dbs[uploaded.name] = tmp.name
            st.session_state.active_db = tmp.name
            st.toast(f"Connected: {uploaded.name}", icon="✅")
            st.rerun()

        st.markdown('<div class="sb-section" style="margin-top:12px;">Active Database</div>', unsafe_allow_html=True)
        all_dbs = {"ecommerce.db (default)": "ecommerce.db", **st.session_state.extra_dbs}
        sel = st.selectbox("Switch", list(all_dbs.keys()), label_visibility="collapsed")
        if all_dbs[sel] != st.session_state.active_db:
            st.session_state.active_db = all_dbs[sel]
            st.rerun()

        db_path_now = current_db()
        if os.path.exists(db_path_now):
            st.markdown(f'<div style="background:#1e2a25;border:1px solid #10a37f33;border-radius:8px;padding:8px 12px;margin:6px 0;font-size:0.78rem;color:#6ee7b7;">✅ Connected: <code>{os.path.basename(db_path_now)}</code></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="background:#2d1a1a;border:1px solid #ef444433;border-radius:8px;padding:8px 12px;margin:6px 0;font-size:0.78rem;color:#f87171;">❌ Not found: <code>{os.path.basename(db_path_now)}</code><br>Place your .db file in the same folder as app.py, or upload it above.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-section" style="margin-top:12px;">Schema</div>', unsafe_allow_html=True)
        info = get_schema()
        if "schema" in info and info["schema"]:
            for table, cols in info["schema"].items():
                with st.expander(f"📋 {table}"):
                    for c in cols:
                        st.caption(f"`{c['col']}` {c['type'] or 'TEXT'}")
        elif not os.path.exists(db_path_now):
            st.caption("Upload a database to see its schema.")

    # ── History tab ──
    elif view == "🕑 History":
        st.markdown('<div class="sb-section">Recent Queries</div>', unsafe_allow_html=True)
        if not st.session_state.query_history:
            st.caption("No queries yet.")
        else:
            for i, h in enumerate(reversed(st.session_state.query_history[-20:])):
                with st.expander(f"🕑 {h['ts']} — {h['query'][:35]}"):
                    st.code(h["sql"], language="sql")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("▶ Re-run", key=f"rerun_{i}"):
                            st.session_state.auto_send = h["query"]
                            st.rerun()
                    with c2:
                        if st.button("⭐ Save", key=f"savefav_{i}"):
                            if h["query"] not in st.session_state.favorites:
                                st.session_state.favorites.append(h["query"])
                                st.toast("Saved to favorites!", icon="⭐")

    # ── Favorites tab ──
    elif view == "⭐ Favorites":
        st.markdown('<div class="sb-section">Saved Queries</div>', unsafe_allow_html=True)
        if not st.session_state.favorites:
            st.caption("Save queries from History to see them here.")
        else:
            for i, fav in enumerate(st.session_state.favorites):
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(fav[:42], key=f"favrun_{i}", use_container_width=True):
                        st.session_state.auto_send = fav
                        st.rerun()
                with col2:
                    if st.button("✕", key=f"favrm_{i}"):
                        st.session_state.favorites.pop(i)
                        st.rerun()

    # ── Dashboard tab ──
    elif view == "📌 Dashboard":
        st.markdown('<div class="sb-section">Pinned Charts</div>', unsafe_allow_html=True)
        if not st.session_state.dashboard_pins:
            st.caption("Pin charts from chat with 📌.")
        else:
            for i, p in enumerate(st.session_state.dashboard_pins):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.caption(f"📊 {p['title']}")
                with col2:
                    if st.button("✕", key=f"sbrm_{i}"):
                        st.session_state.dashboard_pins.pop(i)
                        st.rerun()

    st.markdown("---")
    st.caption(f"🟢 {os.path.basename(current_db())}  ·  LLaMA 3.3 70b  ·  Groq")

# ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
chat_tab, dash_tab = st.tabs(["💬 Chat", "📌 Dashboard"])

# ════════════════════════════════════════════════════════════════════
#  CHAT TAB
# ════════════════════════════════════════════════════════════════════
with chat_tab:

    # ── DB missing warning ─────────────────────────────────────────
    if not os.path.exists(current_db()):
        st.markdown(f"""
        <div style="background:#2d1a1a;border:1px solid #ef444433;border-radius:10px;
             padding:14px 18px;margin:12px 20px;display:flex;align-items:center;gap:12px;">
          <span style="font-size:1.2rem;">⚠️</span>
          <div>
            <div style="color:#f87171;font-size:0.88rem;font-weight:500;">Database not connected</div>
            <div style="color:#888;font-size:0.78rem;margin-top:2px;">
              Place <code style="color:#fca5a5;">ecommerce.db</code> in the same folder as <code style="color:#fca5a5;">app.py</code>,
              or go to <b>📁 Databases</b> in the sidebar to upload your own .db file.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Welcome screen ─────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-wrap">
          <div class="welcome-logo">🧠</div>
          <div class="welcome-title">What do you want to know?</div>
          <div class="welcome-sub">Ask anything about your database in plain English.</div>
        </div>
        """, unsafe_allow_html=True)

        chips = [
            ("📊", "Top 5 products by revenue"),
            ("🥧", "Sales by category — pie chart"),
            ("📈", "Monthly orders trend"),
            ("🔀", "Draw the ER diagram"),
            ("📦", "Low stock products"),
            ("💰", "Average order value"),
        ]
        st.markdown("""
        <style>
        div[data-testid="column"] .stButton > button {
            background: #2a2a2a !important;
            border: 1px solid #3f3f3f !important;
            border-radius: 12px !important;
            color: #c5c5c5 !important;
            font-size: 0.85rem !important;
            padding: 14px 16px !important;
            text-align: left !important;
            height: auto !important;
            line-height: 1.5 !important;
            transition: all 0.15s !important;
        }
        div[data-testid="column"] .stButton > button:hover {
            background: #333 !important;
            border-color: #10a37f55 !important;
            color: #ececec !important;
        }
        </style>
        """, unsafe_allow_html=True)

        cols = st.columns(2)
        for i, (icon, label) in enumerate(chips):
            if cols[i % 2].button(f"{icon}  {label}", key=f"chip_{i}", use_container_width=True):
                st.session_state.auto_send = label

    # ── Auto-send ──────────────────────────────────────────────────
    if st.session_state.auto_send:
        query = st.session_state.auto_send
        st.session_state.auto_send = None
        st.session_state.messages.append({"role": "user", "content": query})
        with st.spinner(""):
            reply, tool_results = run_agent(query)
        st.session_state.messages.append({"role": "assistant", "content": reply, "tool_results": tool_results})
        st.session_state.chat_history.append({"role": "user", "content": query})
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    # ── Render messages ────────────────────────────────────────────
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user">
              <div class="bubble">{msg['content']}</div>
            </div>""", unsafe_allow_html=True)
        else:
            # AI avatar + content
            col_av, col_msg = st.columns([1, 20])
            with col_av:
                st.markdown('<div class="ai-avatar">🧠</div>', unsafe_allow_html=True)
            with col_msg:
                for tri, tr in enumerate(msg.get("tool_results", [])):
                    render_tool(tr, uid=f"{idx}_{tri}")
                if msg.get("content"):
                    # Strip trailing ```sql block from display (shown in SQL pill already)
                    display_text = re.sub(r"```sql[\s\S]*?```", "", msg["content"]).strip()
                    if display_text:
                        st.markdown(display_text)

            # Favourite button per user message (matching pair)
            if idx > 0 and st.session_state.messages[idx - 1]["role"] == "user":
                pass  # kept clean

    # ── Voice + Chat input bar (pinned at bottom) ──────────────────
    # Voice widget sits just above the chat input, inline style
    # Voice: opens a popup window (bypasses iframe mic block)
    voice_bar = """
    <div style="display:flex;align-items:center;gap:10px;
                max-width:800px;margin:0 auto 6px auto;padding:0 4px;">

      <button id="vBtn" onclick="openVoicePopup()" style="
          flex-shrink:0;background:#2f2f2f;border:1px solid #3f3f3f;
          color:#c5c5c5;border-radius:10px;padding:8px 16px;cursor:pointer;
          font-size:0.82rem;font-family:Inter,sans-serif;transition:all .15s;
          white-space:nowrap;">
        🎙️ Voice
      </button>

      <span id="vStatus" style="color:#666;font-size:0.76rem;flex:1;
            overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
        Speak your query — it will appear in the chat box automatically
      </span>
    </div>

    <script>
    // Listen for the transcript sent back from the popup
    window.addEventListener('message', function(e) {
      if (e.data && e.data.type === 'VOICE_TRANSCRIPT') {
        var txt  = e.data.text;
        var stat = document.getElementById('vStatus');
        stat.textContent  = '✅ Got: "' + txt + '"';
        stat.style.color  = '#6ee7b7';

        // Try to inject into Streamlit chat textarea in parent frame
        try {
          var selectors = [
            'textarea[data-testid="stChatInputTextArea"]',
            '.stChatInput textarea',
            'textarea'
          ];
          var ta = null;
          for (var s of selectors) {
            ta = window.parent.document.querySelector(s);
            if (ta) break;
          }
          if (ta) {
            var setter = Object.getOwnPropertyDescriptor(
              window.parent.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(ta, txt);
            ta.dispatchEvent(new Event('input', { bubbles: true }));
            ta.focus();
            stat.textContent = '✅ Ready — press Enter to send';
          } else {
            // fallback: clipboard
            navigator.clipboard.writeText(txt).catch(function(){});
            stat.textContent = '📋 Copied! Paste in chat box (Ctrl+V / ⌘V)';
          }
        } catch(err) {
          navigator.clipboard.writeText(txt).catch(function(){});
          stat.textContent = '📋 Copied! Paste in chat box (Ctrl+V / ⌘V)';
        }

        document.getElementById('vBtn').textContent  = '🎙️ Voice';
        document.getElementById('vBtn').style.color  = '#c5c5c5';
        document.getElementById('vBtn').style.borderColor = '#3f3f3f';
      }
    });

    function openVoicePopup() {
      var btn  = document.getElementById('vBtn');
      var stat = document.getElementById('vStatus');

      // Popup HTML — runs in its OWN window so no iframe mic restriction
      var html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Voice Input</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #1a1a1a; color: #ececec;
    font-family: Inter, -apple-system, sans-serif;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh; gap: 20px; padding: 24px;
  }
  #ring {
    width: 90px; height: 90px; border-radius: 50%;
    background: #2f2f2f; border: 3px solid #3f3f3f;
    display: flex; align-items: center; justify-content: center;
    font-size: 2.2rem; cursor: pointer;
    transition: all .2s; user-select: none;
  }
  #ring.listening {
    background: #10a37f22; border-color: #10a37f;
    animation: pulse 1.2s infinite;
  }
  @keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 #10a37f44; }
    50%      { box-shadow: 0 0 0 14px #10a37f00; }
  }
  #status {
    font-size: 0.88rem; color: #888; text-align: center;
    min-height: 40px; line-height: 1.5;
  }
  #transcript {
    background: #2f2f2f; border: 1px solid #3f3f3f;
    border-radius: 10px; padding: 12px 16px;
    font-size: 0.9rem; color: #ececec;
    width: 100%; min-height: 60px; line-height: 1.6;
    word-break: break-word;
  }
  #sendBtn {
    background: #10a37f; color: #fff; border: none;
    border-radius: 10px; padding: 10px 28px;
    font-size: 0.9rem; cursor: pointer;
    display: none; transition: background .15s;
  }
  #sendBtn:hover { background: #0d8a6c; }
</style>
</head>
<body>
<div id="ring" onclick="toggle()">🎙️</div>
<div id="status">Tap the mic to start speaking</div>
<div id="transcript"></div>
<button id="sendBtn" onclick="sendText()">Send to chat ↗</button>

<script>
var rec = null;
var finalText = '';

function toggle() {
  if (rec) { rec.stop(); return; }
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    document.getElementById('status').textContent = 'Not supported. Use Chrome or Edge.';
    return;
  }
  finalText = '';
  document.getElementById('transcript').textContent = '';
  document.getElementById('sendBtn').style.display = 'none';

  rec = new SR();
  rec.lang = 'en-US';
  rec.interimResults = true;
  rec.continuous = false;

  document.getElementById('ring').classList.add('listening');
  document.getElementById('ring').textContent = '⏹️';
  document.getElementById('status').textContent = 'Listening… speak now';

  rec.onresult = function(e) {
    var interim = '', final = '';
    for (var i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
      else interim += e.results[i][0].transcript;
    }
    document.getElementById('transcript').textContent = final || interim;
    if (final) finalText = final;
  };

  rec.onerror = function(e) {
    var m = { 'not-allowed':'🚫 Allow microphone access in your browser.',
              'no-speech':'🔇 No speech heard — try again.',
              'audio-capture':'🎤 No microphone found.' };
    document.getElementById('status').textContent = m[e.error] || ('Error: ' + e.error);
    reset();
  };

  rec.onend = function() {
    reset();
    if (finalText) {
      document.getElementById('status').textContent = '✅ Got it! Hit Send or close.';
      document.getElementById('sendBtn').style.display = 'inline-block';
    } else {
      document.getElementById('status').textContent = 'Nothing heard — tap mic to retry.';
    }
  };

  rec.start();
}

function reset() {
  rec = null;
  document.getElementById('ring').classList.remove('listening');
  document.getElementById('ring').textContent = '🎙️';
}

function sendText() {
  if (!finalText) return;
  window.opener.postMessage({ type: 'VOICE_TRANSCRIPT', text: finalText }, '*');
  window.close();
}
<\/script>
</body>
</html>`;

      var popup = window.open('', 'VoiceInput',
        'width=360,height=380,resizable=no,scrollbars=no,toolbar=no,menubar=no,location=no');
      if (!popup) {
        stat.textContent = '⚠️ Allow popups for this site, then try again.';
        stat.style.color = '#f87171';
        return;
      }
      popup.document.open();
      popup.document.write(html);
      popup.document.close();

      btn.textContent       = '🎙️ Voice';
      btn.style.color       = '#10a37f';
      btn.style.borderColor = '#10a37f';
      stat.textContent      = '🎙️ Voice popup open — speak there…';
      stat.style.color      = '#6ee7b7';
    }
    </script>
    """
    components.html(voice_bar, height=52)

    user_input = st.chat_input("Message DataMind AI…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner(""):
            reply, tool_results = run_agent(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply, "tool_results": tool_results})
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

# ════════════════════════════════════════════════════════════════════
#  DASHBOARD TAB
# ════════════════════════════════════════════════════════════════════
with dash_tab:
    st.markdown('<div style="padding:24px 8px 8px;"><span style="font-size:1rem;font-weight:600;color:#ececec;">📌 Dashboard</span><span style="color:#555;font-size:0.82rem;margin-left:10px;">Pin charts from chat to build your view</span></div>', unsafe_allow_html=True)

    if not st.session_state.dashboard_pins:
        st.markdown('<div class="info-box" style="max-width:500px;margin:32px auto;text-align:center;">No charts pinned yet.<br><span style="color:#666;font-size:0.78rem;">Click 📌 Pin to Dashboard on any chart in the Chat tab.</span></div>', unsafe_allow_html=True)
    else:
        # Export all
        if st.button("⬇ Export All as ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for p in st.session_state.dashboard_pins:
                    zf.writestr(f"{p['title']}.csv", p["df_csv"])
            buf.seek(0)
            st.download_button("Download ZIP", buf, "dashboard.zip", "application/zip")

        # 2-col grid
        cols = st.columns(2)
        for i, pin in enumerate(st.session_state.dashboard_pins):
            with cols[i % 2]:
                st.markdown('<div class="dash-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="dash-title">{pin["title"]}</div>', unsafe_allow_html=True)
                try:
                    fig = pio.from_json(pin["fig_json"])
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                except Exception as e:
                    st.error(f"Render error: {e}")
                df_pin = pd.read_csv(io.StringIO(pin["df_csv"]))
                c1, c2 = st.columns(2)
                with c1:
                    export_df(df_pin, pin["title"])
                with c2:
                    if st.button("🗑 Remove", key=f"dashrem_{i}"):
                        st.session_state.dashboard_pins.pop(i)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)