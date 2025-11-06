import os
import json
import hashlib
import re
import smtplib
from collections import deque
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import quote

from flask import (
    Flask,
    jsonify,
    redirect,
    request,
    send_from_directory,
)
from werkzeug.exceptions import RequestEntityTooLarge

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = BASE_DIR / "public"
CREDENTIALS_PATH = DATA_DIR / "adminCredentials.json"
CONTENT_PATH = DATA_DIR / "content.json"

DEFAULT_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
DEFAULT_REQUEST_EMAIL = os.getenv("REQUEST_TARGET_EMAIL", "etl@elektrokonstruktiv.ru")
MAIL_FROM = os.getenv("REQUEST_FROM_EMAIL", "no-reply@elektrokonstruktiv.ru")
MAX_ATTACHMENT_SIZE = int(os.getenv("MAX_ATTACHMENT_SIZE_BYTES", 20 * 1024 * 1024))
COOKIE_TTL_SECONDS = 24 * 60 * 60
COOKIE_SECURE = os.getenv("COOKIE_SECURE") in {"true", "1"}
PORT = int(os.getenv("PORT", "9090"))
EXTERNAL_REVIEWS_URL = os.getenv(
    "EXTERNAL_REVIEWS_URL",
    "https://2gis.ru/norilsk/firm/70000001047366044/tab/reviews",
)
EXTERNAL_REVIEWS_TIMEOUT = float(os.getenv("EXTERNAL_REVIEWS_TIMEOUT", "10"))
EXTERNAL_REVIEWS_LIMIT = int(os.getenv("EXTERNAL_REVIEWS_LIMIT", "20"))
EXTERNAL_REVIEWS_DISABLE_PROXY = os.getenv("EXTERNAL_REVIEWS_DISABLE_PROXY") in {"1", "true", "True"}

MOBILE_USER_AGENT_PATTERN = re.compile(
    r"(android|iphone|ipod|ipad|blackberry|windows phone|opera mini|mobile)",
    re.IGNORECASE,
)

def ensure_directory(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def ensure_credentials_file() -> None:
    ensure_directory(DATA_DIR)
    if CREDENTIALS_PATH.exists():
        return
    credentials = {"login": DEFAULT_LOGIN, "password": DEFAULT_PASSWORD}
    CREDENTIALS_PATH.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding="utf-8")


def read_credentials() -> Dict[str, str]:
    ensure_credentials_file()
    try:
        data = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
        login = data.get("login", "").strip()
        password = data.get("password", "")
        if login and password:
            return {"login": login, "password": password}
    except (OSError, ValueError, TypeError):
        pass
    return {"login": DEFAULT_LOGIN, "password": DEFAULT_PASSWORD}


app = Flask(__name__, static_folder=str(PUBLIC_DIR), static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = MAX_ATTACHMENT_SIZE

ensure_directory(DATA_DIR)
ensure_credentials_file()


def read_content() -> Dict[str, Any]:
    if CONTENT_PATH.exists():
        try:
            return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
    return {}


def write_content(content: Dict[str, Any]) -> None:
    ensure_directory(DATA_DIR)
    CONTENT_PATH.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_whitespace(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_rating(value: Any) -> float:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number < 0:
            return None
        return min(number, 5.0)

    match = re.search(r"[0-9]+(?:[.,][0-9]+)?", str(value))
    if not match:
        return None
    try:
        number = float(match.group(0).replace(",", "."))
    except ValueError:
        return None
    if number < 0:
        return None
    return min(number, 5.0)


def is_mobile_user_agent(user_agent: str) -> bool:
    if not user_agent:
        return False
    if MOBILE_USER_AGENT_PATTERN.search(user_agent):
        lower = user_agent.lower()
        if "macintosh" in lower and "ipad" not in lower:
            return False
        return True
    return False


def normalise_review_entry(entry: Any) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {}

    text_candidates = [
        entry.get("text"),
        entry.get("body"),
        entry.get("review_text"),
        entry.get("description"),
        entry.get("message"),
    ]
    text = next((clean_whitespace(value) for value in text_candidates if clean_whitespace(value)), "")
    if not text:
        return {}

    user = entry.get("user") if isinstance(entry.get("user"), dict) else {}
    name_candidates = [
        entry.get("name"),
        entry.get("author"),
        entry.get("author_name"),
        user.get("name") if user else None,
        user.get("full_name") if user else None,
        user.get("display_name") if user else None,
    ]
    name = next((clean_whitespace(value) for value in name_candidates if clean_whitespace(value)), "Клиент 2ГИС")

    image_candidates = [
        entry.get("image"),
        entry.get("photo"),
        entry.get("avatar"),
        user.get("photo") if user else None,
        user.get("avatar") if user else None,
    ]
    image_url = ""
    for candidate in image_candidates:
        if isinstance(candidate, dict):
            candidate = candidate.get("url") or candidate.get("src") or candidate.get("value")
        candidate = clean_whitespace(candidate)
        if candidate:
            image_url = candidate
            break

    date_candidates = [
        entry.get("date"),
        entry.get("created_at"),
        entry.get("publish_date"),
        entry.get("updated_at"),
        entry.get("datetime"),
        entry.get("time"),
    ]
    date_value = next((clean_whitespace(value) for value in date_candidates if clean_whitespace(value)), "")

    location_candidates: List[Any] = []
    branch = entry.get("branch") or entry.get("address") or entry.get("city")
    if isinstance(branch, dict):
        location_candidates.extend(
            [
                branch.get("name"),
                branch.get("address_name"),
                branch.get("full_address"),
                branch.get("city_name"),
            ]
        )
    else:
        location_candidates.append(branch)

    location_value = next((clean_whitespace(value) for value in location_candidates if clean_whitespace(value)), "")
    meta_parts = [part for part in [location_value, date_value] if part]
    meta = ", ".join(meta_parts) if meta_parts else "2ГИС"

    rating_candidate = entry.get("rating")
    if isinstance(rating_candidate, dict):
        rating_candidate = rating_candidate.get("value") or rating_candidate.get("rating")
    if rating_candidate is None:
        rating_candidate = (
            entry.get("rating_value")
            or entry.get("score")
            or entry.get("stars")
            or entry.get("overall")
        )
    rating = parse_rating(rating_candidate)

    return {
        "name": name or "Клиент 2ГИС",
        "text": text,
        "location": meta,
        "image": image_url,
        "rating": rating,
    }


def deduplicate_reviews(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique = []
    seen = set()
    for review in reviews:
        if not isinstance(review, dict):
            continue
        name = review.get("name") or ""
        text = review.get("text") or ""
        key = (name, text)
        if not text or key in seen:
            continue
        seen.add(key)
        unique.append(review)
    return unique


def parse_reviews_from_dom(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    reviews: List[Dict[str, Any]] = []
    for card in soup.select("._1k5soqfl"):
        text_node = card.select_one('[itemprop="reviewBody"]') or card.select_one("p")
        text = clean_whitespace(text_node.get_text(" ", strip=True) if text_node else "")
        if not text:
            continue

        name = ""
        for selector in (
            '[itemprop="author"]',
            '._16f8ve6d',
            '._1nx0fuu',
            'strong',
            'header',
        ):
            node = card.select_one(selector)
            name = clean_whitespace(node.get_text(" ", strip=True) if node else "")
            if name:
                break
        if not name:
            candidate = card.find("span") or card.find("div")
            name = clean_whitespace(candidate.get_text(" ", strip=True) if candidate else "")

        image_node = card.select_one("img")
        image_url = clean_whitespace(image_node["src"]) if image_node and image_node.has_attr("src") else ""

        date_node = card.select_one("time")
        date_value = clean_whitespace(date_node.get_text(" ", strip=True) if date_node else "")

        rating_node = card.select_one('[itemprop="ratingValue"]') or card.select_one('[aria-label*="оцен"]')
        rating = parse_rating(rating_node.get_text("", strip=True) if rating_node else None)

        reviews.append(
            {
                "name": name or "Клиент 2ГИС",
                "text": text,
                "location": date_value or "2ГИС",
                "image": image_url,
                "rating": rating,
            }
        )

    return reviews


def extract_review_dicts(state: Any) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if state is None:
        return results

    queue = deque([state])
    visited = set()
    while queue:
        node = queue.popleft()
        node_id = id(node)
        if node_id in visited:
            continue
        visited.add(node_id)

        if isinstance(node, dict):
            values = list(node.values())
            keys = {str(key).lower() for key in node.keys()}
            if any("review" in key for key in keys):
                for value in values:
                    if isinstance(value, list):
                        dict_items = [item for item in value if isinstance(item, dict)]
                        if dict_items and any(
                            any(field in item for field in ("text", "body", "review_text", "description"))
                            for item in dict_items
                        ):
                            results.extend(dict_items)
                    elif isinstance(value, (dict, list)):
                        queue.append(value)
            for value in values:
                if isinstance(value, (dict, list)):
                    queue.append(value)
        elif isinstance(node, list):
            dict_items = [item for item in node if isinstance(item, dict)]
            if dict_items and any(
                any(field in item for field in ("text", "body", "review_text", "description"))
                for item in dict_items
            ):
                results.extend(dict_items)
            for value in node:
                if isinstance(value, (dict, list)):
                    queue.append(value)

    return results


def parse_reviews_from_initial_state(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    script_node = soup.find("script", id="__INITIAL_STATE__")
    raw_payload = ""
    if script_node and script_node.string:
        raw_payload = script_node.string.strip()
    else:
        match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;\s*<", html, re.S)
        if match:
            raw_payload = match.group(1)

    if not raw_payload:
        return []

    payload = raw_payload
    if payload.startswith("window.__INITIAL_STATE__"):
        parts = payload.split("=", 1)
        payload = parts[1] if len(parts) > 1 else ""
    payload = payload.strip().rstrip(";")

    try:
        state = json.loads(payload)
    except json.JSONDecodeError:
        return []

    review_dicts = extract_review_dicts(state)
    normalised = [normalise_review_entry(item) for item in review_dicts]
    return [item for item in normalised if item]


def fetch_external_reviews() -> List[Dict[str, Any]]:
    proxies = {"http": None, "https": None} if EXTERNAL_REVIEWS_DISABLE_PROXY else None
    response = requests.get(
        EXTERNAL_REVIEWS_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ElektrokonstruktivBot/1.0)"},
        timeout=EXTERNAL_REVIEWS_TIMEOUT,
        proxies=proxies,
    )
    response.raise_for_status()

    html = response.text
    reviews = parse_reviews_from_initial_state(html)
    if not reviews:
        reviews = parse_reviews_from_dom(html)

    deduped = deduplicate_reviews(reviews)
    if not deduped:
        return []

    return deduped[:EXTERNAL_REVIEWS_LIMIT]


def compute_auth_token(credentials: Dict[str, str]) -> str:
    base = f"{credentials['login']}:{credentials['password']}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def has_valid_session() -> bool:
    token = request.cookies.get("adminAuth")
    if not token:
        return False
    credentials = read_credentials()
    return token == compute_auth_token(credentials)


def build_cookie(response, value: str, max_age: int = COOKIE_TTL_SECONDS) -> None:
    response.set_cookie(
        "adminAuth",
        value=value,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def clear_cookie(response) -> None:
    response.set_cookie(
        "adminAuth",
        value="",
        max_age=0,
        httponly=True,
        samesite="Lax",
        secure=COOKIE_SECURE,
        path="/",
    )


def create_email_message(subject: str, text: str, html: str, attachment, recipient: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["To"] = recipient or DEFAULT_REQUEST_EMAIL
    message["From"] = MAIL_FROM
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    if attachment:
        filename, data, mimetype = attachment
        maintype, _, subtype = mimetype.partition("/")
        if not maintype:
            maintype = "application"
            subtype = "octet-stream"
        message.add_attachment(data, maintype=maintype, subtype=subtype or "octet-stream", filename=filename)

    return message


def normalise_smtp_settings(raw_settings: Any) -> Dict[str, Any]:
    if not isinstance(raw_settings, dict):
        return {}

    result: Dict[str, Any] = {}

    host = clean_whitespace(raw_settings.get("host"))
    if host:
        result["host"] = host

    port_value = raw_settings.get("port")
    if port_value not in (None, ""):
        try:
            result["port"] = int(str(port_value).strip())
        except (TypeError, ValueError):
            pass

    security_value = raw_settings.get("security")
    if isinstance(security_value, str):
        security = security_value.strip().lower()
        if security in {"none", "starttls", "ssl"}:
            result["security"] = security

    username = raw_settings.get("username")
    if username is not None:
        result["username"] = clean_whitespace(username)

    password = raw_settings.get("password")
    if password is not None:
        result["password"] = str(password)

    return result


def send_email(message: EmailMessage, smtp_settings: Dict[str, Any] = None) -> None:
    smtp_settings = smtp_settings or {}
    host = clean_whitespace(
        smtp_settings.get("host")
        or os.getenv("SMTP_HOST", "")
    )
    if not host:
        raise RuntimeError(
            "SMTP-сервер не настроен. Укажите адрес сервера в панели управления или через переменную окружения SMTP_HOST."
        )

    port_value = smtp_settings.get("port") or os.getenv("SMTP_PORT") or "587"
    try:
        port = int(str(port_value).strip())
    except (TypeError, ValueError):
        raise RuntimeError("Некорректное значение порта SMTP. Проверьте настройки.")

    security_raw = smtp_settings.get("security")
    if security_raw is None:
        security_raw = os.getenv("SMTP_SECURITY")
    if security_raw is None:
        security_raw = os.getenv("SMTP_SECURE")

    if security_raw is None:
        security = "starttls"
    else:
        security_candidate = str(security_raw).strip().lower()
        if security_candidate in {"none", "starttls", "ssl"}:
            security = security_candidate
        elif security_candidate in {"true", "1", "yes", "starttls", "tls"}:
            security = "starttls"
        elif security_candidate in {"ssl/tls", "smtps"}:
            security = "ssl"
        elif security_candidate in {"false", "0", "no"}:
            security = "none"
        else:
            security = "starttls"

    username = smtp_settings.get("username")
    if username is None:
        username = os.getenv("SMTP_USER")

    password = smtp_settings.get("password")
    if password is None:
        password = os.getenv("SMTP_PASSWORD")

    if security == "ssl":
        with smtplib.SMTP_SSL(host, port) as server:
            if username and password:
                server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host, port) as server:
        if security == "starttls":
            try:
                server.ehlo()
                server.starttls()
                server.ehlo()
            except smtplib.SMTPException:
                pass
        if username and password:
            server.login(username, password)
        server.send_message(message)


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_):
    return jsonify({"error": "Файл слишком большой", "code": "FILE_TOO_LARGE", "limit": MAX_ATTACHMENT_SIZE}), 413


@app.route("/")
def serve_root():
    user_agent = request.headers.get("User-Agent", "") or ""
    if is_mobile_user_agent(user_agent):
        return redirect("/mobile", code=302)
    return send_from_directory(str(PUBLIC_DIR), "landingStart.html")


@app.route("/mobile")
def serve_mobile():
    return send_from_directory(str(PUBLIC_DIR), "mobile.html")


@app.route("/login")
def serve_login():
    return send_from_directory(str(PUBLIC_DIR), "login.html")


@app.route("/admin")
def serve_admin():
    if not has_valid_session():
        redirect_target = request.full_path or "/admin"
        if redirect_target.endswith("?"):
            redirect_target = redirect_target[:-1]
        encoded = quote(redirect_target, safe="")
        return redirect(f"/login?redirect={encoded}", code=302)
    return send_from_directory(str(PUBLIC_DIR), "admin.html")


@app.route("/admin.html")
def serve_admin_html():
    return serve_admin()


@app.route("/api/content", methods=["GET"])
def get_content():
    return jsonify(read_content())


@app.route("/api/reviews/external", methods=["GET"])
def get_external_reviews():
    fallback_reviews = read_content().get("reviews", [])
    try:
        reviews = fetch_external_reviews()
        if reviews:
            return jsonify({"reviews": reviews, "source": "external"})
        return jsonify(
            {
                "reviews": fallback_reviews,
                "source": "fallback",
                "error": "Не удалось разобрать отзывы с 2ГИС.",
            }
        )
    except requests.RequestException as exc:
        app.logger.warning("Не удалось загрузить отзывы с 2ГИС: %s", exc)
    except Exception as exc:
        app.logger.warning("Ошибка обработки отзывов 2ГИС: %s", exc)
    return jsonify(
        {
            "reviews": fallback_reviews,
            "source": "fallback",
            "error": "Не удалось загрузить отзывы с 2ГИС.",
        }
    )


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    login = (payload.get("login") or "").strip()
    password = payload.get("password") or ""
    credentials = read_credentials()
    if login == credentials["login"] and password == credentials["password"]:
        response = jsonify({"status": "ok"})
        build_cookie(response, compute_auth_token(credentials))
        return response
    return jsonify({"error": "Неверные учётные данные"}), 403


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    response = jsonify({"status": "ok"})
    clear_cookie(response)
    return response


@app.route("/api/content", methods=["POST"])
def save_content():
    if not has_valid_session():
        return jsonify({"error": "Неверные учётные данные"}), 403
    payload = request.get_json(silent=True) or {}
    data = payload.get("data")
    if not isinstance(data, dict):
        return jsonify({"error": "Некорректный формат данных"}), 400
    write_content(data)
    return jsonify({"status": "ok"})


@app.route("/api/request", methods=["POST"])
def send_request():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    comment = (request.form.get("comment") or "").strip()
    errors = {}

    if not name:
        errors["name"] = "Заполните это поле"

    has_contact = bool(email) or bool(phone)
    if not has_contact:
        contact_message = "Укажите e-mail или телефон"
        errors["email"] = contact_message
        errors["phone"] = contact_message
    elif email and ("@" not in email or "." not in email.split("@")[-1]):
        errors["email"] = "Введите корректный e-mail"

    file_storage = request.files.get("attachment")
    attachment_tuple = None
    has_attachment = False
    if file_storage and file_storage.filename:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
        if size > MAX_ATTACHMENT_SIZE:
            errors["attachment"] = "Файл слишком большой"
        else:
            attachment_tuple = (
                file_storage.filename,
                file_storage.read(),
                file_storage.mimetype or "application/octet-stream",
            )
            has_attachment = True

    if not comment and not has_attachment:
        requirement_message = "Добавьте комментарий или приложите файл"
        errors["comment"] = requirement_message
        if "attachment" not in errors:
            errors["attachment"] = requirement_message

    if errors:
        return jsonify({"error": "Некорректные данные", "errors": errors}), 400

    parts = [f"Имя: {name}"]
    if email:
        parts.append(f"E-mail: {email}")
    if phone:
        parts.append(f"Телефон: {phone}")
    if comment:
        parts.append(f"Комментарий: {comment}")
    if attachment_tuple:
        parts.append(f"Файл: {attachment_tuple[0]} (во вложении)")
    parts.append(f"Отправлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    text_body = "\n".join(parts)
    html_body = "".join(f"<p>{item}</p>" for item in parts)

    content_snapshot = read_content()
    raw_request_settings = content_snapshot.get("request")
    request_settings = raw_request_settings if isinstance(raw_request_settings, dict) else {}
    raw_contacts = content_snapshot.get("contacts")
    contacts_settings = raw_contacts if isinstance(raw_contacts, dict) else {}
    smtp_settings = normalise_smtp_settings(request_settings.get("smtp"))
    target_email = next(
        (
            candidate.strip()
            for candidate in [
                request_settings.get("targetEmail"),
                contacts_settings.get("email"),
                DEFAULT_REQUEST_EMAIL,
            ]
            if isinstance(candidate, str) and candidate.strip()
        ),
        DEFAULT_REQUEST_EMAIL,
    )

    message = create_email_message(
        "Новая заявка с сайта Электроконструктив",
        text_body,
        html_body,
        attachment_tuple,
        target_email,
    )

    try:
        send_email(message, smtp_settings=smtp_settings)
    except Exception as exc:
        app.logger.error("Не удалось отправить заявку: %s", exc)
        return jsonify({"error": "Не удалось отправить заявку. Повторите попытку позже."}), 500

    return jsonify(
        {
            "status": "ok",
            "message": "Ваша заявка отправлена. Мы свяжемся с вами в ближайшее время.",
        }
    )


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Маршрут не найден"}), 404


if __name__ == "__main__":
    ensure_credentials_file()
    ensure_directory(DATA_DIR)
    app.run(host="0.0.0.0", port=PORT)