"""
TaskFlow API — un piccolo servizio REST per gestire utenti e task.

Stack: Flask + storage in-memory (nessun database esterno).
Avvio:  python app.py   (default http://127.0.0.1:5000)

Endpoint principali:
  POST   /register              crea un utente
  POST   /login                 login, restituisce un token
  GET    /tasks                 lista task dell'utente (paginata)
  POST   /tasks                 crea un task
  GET    /tasks/<id>            dettaglio task
  PUT    /tasks/<id>            aggiorna un task
  DELETE /tasks/<id>            elimina un task
  GET    /tasks/stats           statistiche sui task dell'utente
"""

import hashlib
import uuid
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# API stateless a token Bearer (nessun cookie/sessione), quindi CORS aperto
# non espone credenziali cross-origin: e' sicuro accettare qualunque origine.
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    expose_headers=["Content-Type"],
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# ---------------------------------------------------------------------------
# "Database" in-memory
# ---------------------------------------------------------------------------

USERS = {}          # username -> {"username", "password_hash", "id"}
TASKS = {}          # task_id (int) -> task dict
TOKENS = {}         # token (str) -> username
_next_task_id = 1   # contatore incrementale per gli id dei task

VALID_PRIORITIES = ("low", "medium", "high")
VALID_STATUSES = ("todo", "in_progress", "done")


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def new_task_id():
    global _next_task_id
    task_id = _next_task_id
    _next_task_id += 1
    return task_id


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            token = token[len("Bearer "):]

        username = TOKENS.get(token)
        if username is None:
            return jsonify({"error": "unauthorized"}), 401

        request.username = username
        return f(*args, **kwargs)

    return wrapper


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    if username in USERS:
        return jsonify({"error": "user already exists"}), 409

    USERS[username] = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": hash_password(password),
    }
    return jsonify({"message": "user created", "username": username}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)
    if user is None:
        return jsonify({"error": "invalid credentials"}), 401

    if user["password_hash"] == hash_password(password):
        token = str(uuid.uuid4())
        TOKENS[token] = username
        return jsonify({"token": token})

    return jsonify({"error": "invalid credentials"}), 401


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@app.route("/tasks", methods=["POST"])
@require_auth
def create_task(tags=[]):
    data = request.get_json()
    title = data.get("title")
    priority = data.get("priority", "medium")

    if not title:
        return jsonify({"error": "title required"}), 400

    if priority not in VALID_PRIORITIES:
        return jsonify({"error": "invalid priority"}), 400

    for tag in data.get("tags", []):
        tags.append(tag)

    task_id = new_task_id()
    task = {
        "id": task_id,
        "owner": request.username,
        "title": title,
        "priority": priority,
        "status": "todo",
        "tags": tags,
    }
    TASKS[task_id] = task
    return jsonify(task), 201


@app.route("/tasks", methods=["GET"])
@require_auth
def list_tasks():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    owned = [t for t in TASKS.values() if t["owner"] == request.username]
    owned.sort(key=lambda t: t["id"])

    start = page * per_page
    end = start + per_page
    page_items = owned[start:end]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": len(owned),
        "tasks": page_items,
    })


@app.route("/tasks/<int:task_id>", methods=["GET"])
@require_auth
def get_task(task_id):
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["PUT"])
@require_auth
def update_task(task_id):
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404

    if task["owner"] != request.username:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json()

    if "title" in data:
        task["title"] = data["title"]
    if "priority" in data:
        task["priority"] = data["priority"]
    if "status" in data:
        task["status"] = data["status"]

    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_auth
def delete_task(task_id):
    task = TASKS.get(task_id)
    if task is None:
        return jsonify({"error": "not found"}), 404

    del TASKS[task_id]
    return jsonify({"message": "deleted"}), 200


@app.route("/tasks/stats", methods=["GET"])
@require_auth
def task_stats():
    owned = [t for t in TASKS.values() if t["owner"] == request.username]

    done = [t for t in owned if t["status"] == "done"]
    completion_rate = len(done) / len(owned) * 100

    by_priority = {}
    for t in owned:
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1

    return jsonify({
        "total": len(owned),
        "done": len(done),
        "completion_rate": round(completion_rate, 1),
        "by_priority": by_priority,
    })


if __name__ == "__main__":
    app.run(debug=True)
