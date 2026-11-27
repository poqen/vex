"""VEX — Discord-бот для управления Rust-кланом. Весь проект в ОДНОМ файле.

Запуск:  python main.py
Переменные окружения: DISCORD_TOKEN (обязательно), GUILD_ID, DATA_DIR, TIMEZONE.
Библиотека discord.py при первом запуске установится автоматически.

Устройство файла: ниже в словаре _SOURCES лежит исходный код модулей бота (обычный текст,
его можно править прямо здесь — цвета, типы тикетов и домены в блоке vex/config.py).
В самом конце файла — точка входа.
"""
import importlib.abc
import importlib.util
import logging
import subprocess
import sys


def _ensure_dependencies():
    try:
        import discord  # noqa: F401
        return
    except ImportError:
        pass
    print("Устанавливаю discord.py (только при первом запуске)...", flush=True)
    base = [sys.executable, "-m", "pip", "install", "--quiet", "discord.py>=2.4,<3"]
    for extra in ([], ["--break-system-packages"], ["--user"]):
        if subprocess.call(base + extra) == 0:
            break
    else:
        raise SystemExit(
            "Не удалось установить discord.py автоматически. "
            "Добавь на хостинг файл requirements.txt со строкой: discord.py>=2.4,<3"
        )
    importlib.invalidate_caches()


_ensure_dependencies()

_PACKAGES = ['vex', 'vex.cogs']

_SOURCES = {
    'vex': r'''"""VEX — Discord-бот для управления клан-сообществом в Rust."""
''',
    'vex.config': r'''"""Настройки и константы VEX. Всё, что хочется поменять «под себя», — здесь."""
import json
import os
from pathlib import Path

try:  # .env нужен только для локального запуска; на хостинге переменные задаются в панели
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --- Окружение -------------------------------------------------------------
TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
GUILD_ID = _int("GUILD_ID")  # ID сервера: команды появятся сразу. Пусто = глобальная синхронизация (до часа)
# Здесь лежит база. На bothost постоянные данные хранятся в /app/data — он выбирается сам, если существует.
DATA_DIR = Path(os.getenv("DATA_DIR") or ("/app/data" if Path("/app").is_dir() else "./data"))
TRANSCRIPT_DIR = DATA_DIR / "transcripts"  # HTML и TXT транскрипты закрытых тикетов
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# --- Сайт-панель -------------------------------------------------------------
# Сайт включается, когда хостинг передаёт порт (переменная PORT, появляется вместе с опцией «Использовать домен»).
WEB_PORT = _int("PORT") or _int("WEB_PORT")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "").strip()  # Developer Portal -> OAuth2 -> Client Secret
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "").strip()  # необязательно: по умолчанию берётся ID бота
PUBLIC_URL = os.getenv("PUBLIC_URL", "").strip().rstrip("/")  # необязательно: https://адрес-твоего-бота

# --- Оформление ------------------------------------------------------------
BRAND = "VEX"
FOOTER = "VEX • Clan Control"
COLOR_MAIN = 0x8B5CF6  # фиолетовый
COLOR_DARK = 0x6D28D9  # тёмно-фиолетовый (закрытые события)
COLOR_OK = 0x22C55E
COLOR_ERR = 0xEF4444
COLOR_WARN = 0xF59E0B

# Названия цветов для конструктора эмбедов (/say). Можно дописывать свои.
NAMED_COLORS = {
    "purple": COLOR_MAIN,
    "фиолетовый": COLOR_MAIN,
    "dark": COLOR_DARK,
    "green": COLOR_OK,
    "зелёный": COLOR_OK,
    "зеленый": COLOR_OK,
    "red": COLOR_ERR,
    "красный": COLOR_ERR,
    "orange": COLOR_WARN,
    "оранжевый": COLOR_WARN,
    "blue": 0x3B82F6,
    "синий": 0x3B82F6,
    "blurple": 0x5865F2,
    "black": 0x0F0A1F,
    "white": 0xFFFFFF,
    "gold": 0xF1C40F,
}

# --- Тикеты: типы обращений (меню на панели). Меняй как угодно, до 25 штук. ---
TICKET_TYPES = [
    {"key": "join", "slug": "join", "label": "Вступление в клан", "emoji": "🛡️",
     "description": "Подать заявку на вступление"},
    {"key": "question", "slug": "question", "label": "Вопрос", "emoji": "❓",
     "description": "Задать вопрос администрации"},
    {"key": "report", "slug": "report", "label": "Жалоба", "emoji": "🚨",
     "description": "Жалоба на игрока или участника клана"},
    {"key": "appeal", "slug": "appeal", "label": "Обжалование наказания", "emoji": "⚖️",
     "description": "Оспорить мут, бан или предупреждение"},
    {"key": "other", "slug": "other", "label": "Другое", "emoji": "📨",
     "description": "Всё остальное"},
]

# --- Тикеты: приоритеты -----------------------------------------------------
PRIORITY_ORDER = ("low", "normal", "high", "urgent")
PRIORITY_LABELS = {
    "low": "🟢 Низкий",
    "normal": "🔵 Обычный",
    "high": "🟠 Высокий",
    "urgent": "🔴 Срочный",
}
# Префикс имени канала: срочные тикеты видно в списке каналов сразу.
PRIORITY_CHANNEL_PREFIX = {
    "low": "",
    "normal": "",
    "high": "🟠-",
    "urgent": "🔴-",
}

def load_ticket_types(raw):
    """Типы тикетов сервера: из настроек (JSON, их меняют на сайте) или значения по умолчанию."""
    if raw:
        try:
            out = []
            for item in json.loads(raw)[:25]:
                out.append({
                    "key": str(item["key"]),
                    "slug": str(item.get("slug") or "ticket")[:20],
                    "label": str(item["label"])[:100],
                    "emoji": str(item.get("emoji") or ""),
                    "description": str(item.get("description") or "")[:100],
                })
            if out:
                return out
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    return [dict(t) for t in TICKET_TYPES]


# --- Автомодерация: домены, которые разрешены всегда ------------------------
DEFAULT_ALLOWED_DOMAINS = (
    "tenor.com",
    "giphy.com",
    "cdn.discordapp.com",
    "media.discordapp.net",
)

# --- Ключи команд для системы доступа (/perms) -------------------------------
COMMAND_KEYS = {
    "dashboard": "Сайт-панель: команда /dashboard и вход (разделы «Обзор», «Модерация», «События»)",
    "mod": "Модерация: /warn /mute /unmute /kick /history /unwarn /purge",
    "ban": "Баны: /ban и /unban",
    "ticket_admin": "Панель и настройка тикетов",
    "ticket_manage": "Работа с тикетами (закрыть, добавить, взять)",
    "role": "Выдача и снятие ролей (/role add, /role remove)",
    "role_admin": "Список ролей, которые можно выдавать (/role allow)",
    "wipe": "Вайп-реакты, /noreact и /wipe stats",
    "automod": "Настройка автомодерации",
    "autorole": "Настройка авто-выдачи ролей",
    "say": "Сообщения и конструктор эмбедов (/say)",
    "roster": "Состав клана и чужие карточки (/roster, /nick clear)",
    "poll": "Голосования (/poll)",
}
''',
    'vex.embeds': r'''"""Единый стиль эмбедов VEX."""
import discord

from . import config


def make(title=None, description=None, color=config.COLOR_MAIN, footer=True):
    embed = discord.Embed(title=title, description=description, color=color)
    if footer:
        embed.set_footer(text=config.FOOTER)
    return embed


def ok(text, title="Готово"):
    return make(f"✅ {title}", text, config.COLOR_OK)


def err(text, title="Ошибка"):
    return make(f"⛔ {title}", text, config.COLOR_ERR)


def warn(text, title="Внимание"):
    return make(f"⚠️ {title}", text, config.COLOR_WARN)


def info(text, title=None):
    return make(title, text)
''',
    'vex.db': r'''"""Небольшая обёртка над SQLite (стандартная библиотека, без доп. зависимостей)."""
import asyncio
import json
import sqlite3
import threading
import time
from pathlib import Path
from time import time as now_ts

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER NOT NULL,
    key      TEXT    NOT NULL,
    value    TEXT    NOT NULL,
    PRIMARY KEY (guild_id, key)
);

-- Универсальное хранилище «ролей и каналов по назначению»:
--   cmd:<ключ>            роли с доступом к команде
--   ticket_support        роли поддержки тикетов
--   manageable            роли, которые модераторы могут выдавать
--   autorole_member       роли для новых участников
--   autorole_bot          роли для новых ботов
--   automod_bypass        роли, которых не трогает автомодерация
--   automod_ignore_channel каналы, где автомодерация выключена
CREATE TABLE IF NOT EXISTS guild_targets (
    guild_id  INTEGER NOT NULL,
    kind      TEXT    NOT NULL,
    target_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, kind, target_id)
);

CREATE TABLE IF NOT EXISTS allowed_domains (
    guild_id INTEGER NOT NULL,
    domain   TEXT    NOT NULL,
    PRIMARY KEY (guild_id, domain)
);

CREATE TABLE IF NOT EXISTS automod_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    link       TEXT    NOT NULL,
    ts         INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS mod_cases (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   INTEGER NOT NULL,
    case_no    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    mod_id     INTEGER NOT NULL,
    action     TEXT    NOT NULL,
    reason     TEXT    NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    active     INTEGER NOT NULL DEFAULT 1,
    UNIQUE (guild_id, case_no)
);
CREATE INDEX IF NOT EXISTS idx_cases_user ON mod_cases(guild_id, user_id);

CREATE TABLE IF NOT EXISTS role_panels (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id    INTEGER NOT NULL,
    channel_id  INTEGER NOT NULL,
    message_id  INTEGER NOT NULL DEFAULT 0,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    exclusive   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS role_panel_roles (
    panel_id INTEGER NOT NULL,
    role_id  INTEGER NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (panel_id, role_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id       INTEGER NOT NULL,
    channel_id     INTEGER NOT NULL DEFAULT 0,
    user_id        INTEGER NOT NULL,
    type           TEXT    NOT NULL,
    reason         TEXT    NOT NULL DEFAULT '',
    claimed_by     INTEGER,
    status         TEXT    NOT NULL DEFAULT 'open',
    created_at     INTEGER NOT NULL,
    closed_at      INTEGER,
    priority       TEXT    NOT NULL DEFAULT 'normal',
    close_reason   TEXT,
    closed_by      INTEGER,
    rating         INTEGER,
    rating_comment TEXT,
    last_activity  INTEGER,
    first_reply_at INTEGER,
    locked         INTEGER NOT NULL DEFAULT 0,
    transcript     TEXT
);

-- Внутренние заметки поддержки: автор тикета их не видит.
CREATE TABLE IF NOT EXISTS ticket_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id  INTEGER NOT NULL,
    author_id  INTEGER NOT NULL,
    text       TEXT    NOT NULL,
    created_at INTEGER NOT NULL
);

-- Кому запрещено открывать тикеты.
CREATE TABLE IF NOT EXISTS ticket_blacklist (
    guild_id INTEGER,
    user_id  INTEGER,
    reason   TEXT,
    added_by INTEGER,
    added_at INTEGER,
    PRIMARY KEY (guild_id, user_id)
);

-- Свои типы обращений сервера. Пусто = берутся значения из config.TICKET_TYPES.
CREATE TABLE IF NOT EXISTS ticket_types (
    guild_id    INTEGER,
    key         TEXT,
    label       TEXT    NOT NULL,
    emoji       TEXT    NOT NULL DEFAULT '🎫',
    description TEXT    NOT NULL DEFAULT '',
    slug        TEXT    NOT NULL,
    position    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, key)
);

-- Сохранённые заготовки эмбедов для /say.
CREATE TABLE IF NOT EXISTS embed_templates (
    guild_id   INTEGER,
    name       TEXT,
    payload    TEXT    NOT NULL,
    author_id  INTEGER,
    created_at INTEGER,
    PRIMARY KEY (guild_id, name)
);

-- Карточки участников клана (/nick, /roster).
CREATE TABLE IF NOT EXISTS clan_members (
    guild_id   INTEGER,
    user_id    INTEGER,
    nick       TEXT,
    hours      INTEGER,
    timezone   TEXT,
    note       TEXT,
    updated_at INTEGER,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS polls (
    message_id INTEGER PRIMARY KEY,
    guild_id   INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    author_id  INTEGER NOT NULL,
    question   TEXT    NOT NULL,
    options    TEXT    NOT NULL,
    multi      INTEGER NOT NULL DEFAULT 0,
    anonymous  INTEGER NOT NULL DEFAULT 1,
    closed     INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS poll_votes (
    message_id   INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    option_index INTEGER NOT NULL,
    PRIMARY KEY (message_id, user_id, option_index)
);

CREATE TABLE IF NOT EXISTS wipe_events (
    message_id   INTEGER PRIMARY KEY,
    guild_id     INTEGER NOT NULL,
    channel_id   INTEGER NOT NULL,
    creator_id   INTEGER NOT NULL,
    creator_name TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    description  TEXT    NOT NULL DEFAULT '',
    server       TEXT,
    ts           INTEGER NOT NULL,
    ask_reason   INTEGER NOT NULL DEFAULT 0,
    ping_role_id INTEGER,
    closed       INTEGER NOT NULL DEFAULT 0,
    reminded     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS wipe_responses (
    message_id INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    status     TEXT    NOT NULL,
    reason     TEXT,
    PRIMARY KEY (message_id, user_id)
);
"""

# Колонки, которые должны быть в tickets. База могла быть создана старой версией бота,
# поэтому при старте недостающие колонки добавляются через ALTER TABLE.
TICKET_COLUMNS = (
    ("priority", "TEXT NOT NULL DEFAULT 'normal'"),
    ("close_reason", "TEXT"),
    ("closed_by", "INTEGER"),
    ("rating", "INTEGER"),
    ("rating_comment", "TEXT"),
    ("last_activity", "INTEGER"),
    ("first_reply_at", "INTEGER"),
    ("locked", "INTEGER NOT NULL DEFAULT 0"),
    ("transcript", "TEXT"),
)


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._conn = None

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._migrate()
        self._conn.commit()

    def _migrate(self):
        """Безопасно добавляет новые колонки в уже существующую базу."""
        existing = {row["name"] for row in self._conn.execute("PRAGMA table_info(tickets)")}
        for name, definition in TICKET_COLUMNS:
            if name not in existing:
                self._conn.execute(f"ALTER TABLE tickets ADD COLUMN {name} {definition}")
        # У старых тикетов нет времени последней активности — берём время создания.
        self._conn.execute(
            "UPDATE tickets SET last_activity=created_at WHERE last_activity IS NULL"
        )

    # --- низкий уровень (выполняется в потоке, чтобы не блокировать бота) ----
    def _execute(self, sql, params):
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur.rowcount, cur.lastrowid

    def _fetch(self, sql, params, one):
        with self._lock:
            cur = self._conn.execute(sql, params)
            return cur.fetchone() if one else cur.fetchall()

    def _replace(self, table, guild_id, column, kind, values):
        with self._lock:
            if table == "guild_targets":
                self._conn.execute("DELETE FROM guild_targets WHERE guild_id=? AND kind=?", (guild_id, kind))
                self._conn.executemany(
                    "INSERT OR IGNORE INTO guild_targets(guild_id, kind, target_id) VALUES(?,?,?)",
                    [(guild_id, kind, v) for v in values],
                )
            else:
                self._conn.execute("DELETE FROM allowed_domains WHERE guild_id=?", (guild_id,))
                self._conn.executemany(
                    "INSERT OR IGNORE INTO allowed_domains(guild_id, domain) VALUES(?,?)",
                    [(guild_id, v) for v in values],
                )
            self._conn.commit()

    def _add_case(self, guild_id, user_id, mod_id, action, reason, expires_at):
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO mod_cases(guild_id, case_no, user_id, mod_id, action, reason, created_at, expires_at) "
                "VALUES(?, (SELECT COALESCE(MAX(case_no), 0) + 1 FROM mod_cases WHERE guild_id=?), ?,?,?,?,?,?)",
                (guild_id, guild_id, user_id, mod_id, action, reason, int(time.time()), expires_at),
            )
            self._conn.commit()
            return self._conn.execute("SELECT * FROM mod_cases WHERE id=?", (cur.lastrowid,)).fetchone()

    async def add_case(self, guild_id, user_id, mod_id, action, reason="", expires_at=None):
        """Создаёт запись о наказании; номер у каждого сервера свой. Возвращает строку записи."""
        return await asyncio.to_thread(self._add_case, guild_id, user_id, mod_id, action, reason, expires_at)

    def _set_panel_roles(self, panel_id, role_ids):
        with self._lock:
            self._conn.execute("DELETE FROM role_panel_roles WHERE panel_id=?", (panel_id,))
            self._conn.executemany(
                "INSERT OR IGNORE INTO role_panel_roles(panel_id, role_id, position) VALUES(?,?,?)",
                [(panel_id, role_id, index) for index, role_id in enumerate(role_ids)],
            )
            self._conn.commit()

    async def set_panel_roles(self, panel_id, role_ids):
        await asyncio.to_thread(self._set_panel_roles, panel_id, list(role_ids))

    async def set_targets(self, guild_id, kind, ids):
        """Полностью заменяет список ролей/каналов этого назначения."""
        await asyncio.to_thread(self._replace, "guild_targets", guild_id, None, kind, list(ids))

    async def set_domains(self, guild_id, domains):
        """Полностью заменяет список разрешённых доменов сервера."""
        await asyncio.to_thread(self._replace, "allowed_domains", guild_id, None, None, list(domains))

    async def execute(self, sql, params=()):
        """Выполняет запрос, возвращает число затронутых строк."""
        rowcount, _ = await asyncio.to_thread(self._execute, sql, tuple(params))
        return rowcount

    async def insert(self, sql, params=()):
        """Выполняет INSERT, возвращает id новой строки."""
        _, last_id = await asyncio.to_thread(self._execute, sql, tuple(params))
        return last_id

    async def fetchone(self, sql, params=()):
        return await asyncio.to_thread(self._fetch, sql, tuple(params), True)

    async def fetchall(self, sql, params=()):
        return await asyncio.to_thread(self._fetch, sql, tuple(params), False)

    # --- настройки сервера ---------------------------------------------------
    async def get_setting(self, guild_id, key, default=None):
        row = await self.fetchone(
            "SELECT value FROM settings WHERE guild_id=? AND key=?", (guild_id, key)
        )
        return row["value"] if row else default

    async def set_setting(self, guild_id, key, value):
        await self.execute(
            "INSERT INTO settings(guild_id, key, value) VALUES(?,?,?) "
            "ON CONFLICT(guild_id, key) DO UPDATE SET value=excluded.value",
            (guild_id, key, str(value)),
        )

    async def del_setting(self, guild_id, key):
        await self.execute("DELETE FROM settings WHERE guild_id=? AND key=?", (guild_id, key))

    # --- роли и каналы по назначению ----------------------------------------
    async def get_targets(self, guild_id, kind):
        rows = await self.fetchall(
            "SELECT target_id FROM guild_targets WHERE guild_id=? AND kind=?", (guild_id, kind)
        )
        return [r["target_id"] for r in rows]

    async def add_target(self, guild_id, kind, target_id):
        """True, если запись добавлена (раньше её не было)."""
        changed = await self.execute(
            "INSERT OR IGNORE INTO guild_targets(guild_id, kind, target_id) VALUES(?,?,?)",
            (guild_id, kind, target_id),
        )
        return changed > 0

    async def remove_target(self, guild_id, kind, target_id):
        """True, если запись была и удалена."""
        changed = await self.execute(
            "DELETE FROM guild_targets WHERE guild_id=? AND kind=? AND target_id=?",
            (guild_id, kind, target_id),
        )
        return changed > 0

    async def clear_targets(self, guild_id, kind):
        await self.execute("DELETE FROM guild_targets WHERE guild_id=? AND kind=?", (guild_id, kind))

    # --- типы обращений ------------------------------------------------------
    async def get_ticket_types(self, guild_id):
        """Типы обращений сервера. Если сервер своих не задал — значения из config."""
        rows = await self.fetchall(
            "SELECT key, label, emoji, description, slug FROM ticket_types "
            "WHERE guild_id=? ORDER BY position, rowid",
            (guild_id,),
        )
        if not rows:
            return [dict(t) for t in config.TICKET_TYPES]
        return [dict(row) for row in rows]

    async def _seed_ticket_types(self, guild_id):
        """Переносит типы по умолчанию в базу, чтобы их можно было менять и удалять."""
        row = await self.fetchone(
            "SELECT COUNT(*) AS n FROM ticket_types WHERE guild_id=?", (guild_id,)
        )
        if row and row["n"]:
            return
        for position, t in enumerate(config.TICKET_TYPES):
            await self.execute(
                "INSERT OR IGNORE INTO ticket_types(guild_id, key, label, emoji, description, slug, "
                "position) VALUES(?,?,?,?,?,?,?)",
                (guild_id, t["key"], t["label"], t["emoji"], t["description"], t["slug"], position),
            )

    async def add_ticket_type(self, guild_id, key, label, emoji, description, slug, position=100):
        await self._seed_ticket_types(guild_id)
        await self.execute(
            "INSERT INTO ticket_types(guild_id, key, label, emoji, description, slug, position) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(guild_id, key) DO UPDATE SET "
            "label=excluded.label, emoji=excluded.emoji, description=excluded.description, "
            "slug=excluded.slug",
            (guild_id, key, label, emoji, description, slug, position),
        )

    async def set_ticket_types(self, guild_id, types):
        """Полностью заменяет типы обращений сервера (используется сайтом)."""
        await self.execute("DELETE FROM ticket_types WHERE guild_id=?", (guild_id,))
        for position, t in enumerate(types):
            await self.execute(
                "INSERT OR REPLACE INTO ticket_types(guild_id, key, label, emoji, description, slug, position) "
                "VALUES(?,?,?,?,?,?,?)",
                (guild_id, t["key"], t["label"], t.get("emoji") or "🎫", t.get("description") or "",
                 t["slug"], position),
            )

    async def remove_ticket_type(self, guild_id, key):
        """True, если тип был и удалён."""
        await self._seed_ticket_types(guild_id)
        changed = await self.execute(
            "DELETE FROM ticket_types WHERE guild_id=? AND key=?", (guild_id, key)
        )
        return changed > 0

    # --- чёрный список тикетов ----------------------------------------------
    async def is_blacklisted(self, guild_id, user_id):
        """Возвращает строку чёрного списка или None."""
        return await self.fetchone(
            "SELECT * FROM ticket_blacklist WHERE guild_id=? AND user_id=?", (guild_id, user_id)
        )

    async def add_blacklist(self, guild_id, user_id, reason, added_by):
        await self.execute(
            "INSERT INTO ticket_blacklist(guild_id, user_id, reason, added_by, added_at) "
            "VALUES(?,?,?,?,?) ON CONFLICT(guild_id, user_id) DO UPDATE SET "
            "reason=excluded.reason, added_by=excluded.added_by, added_at=excluded.added_at",
            (guild_id, user_id, reason, added_by, int(now_ts())),
        )

    async def remove_blacklist(self, guild_id, user_id):
        """True, если пользователь был в списке."""
        changed = await self.execute(
            "DELETE FROM ticket_blacklist WHERE guild_id=? AND user_id=?", (guild_id, user_id)
        )
        return changed > 0

    async def list_blacklist(self, guild_id):
        return await self.fetchall(
            "SELECT * FROM ticket_blacklist WHERE guild_id=? ORDER BY added_at DESC", (guild_id,)
        )

    # --- шаблоны эмбедов -----------------------------------------------------
    async def save_template(self, guild_id, name, payload, author_id):
        await self.execute(
            "INSERT INTO embed_templates(guild_id, name, payload, author_id, created_at) "
            "VALUES(?,?,?,?,?) ON CONFLICT(guild_id, name) DO UPDATE SET "
            "payload=excluded.payload, author_id=excluded.author_id, created_at=excluded.created_at",
            (guild_id, name, json.dumps(payload, ensure_ascii=False), author_id, int(now_ts())),
        )

    async def load_template(self, guild_id, name):
        """Возвращает словарь шаблона или None."""
        row = await self.fetchone(
            "SELECT payload FROM embed_templates WHERE guild_id=? AND name=?", (guild_id, name)
        )
        if row is None:
            return None
        try:
            return json.loads(row["payload"])
        except (ValueError, TypeError):
            return None

    async def list_templates(self, guild_id):
        return await self.fetchall(
            "SELECT name, author_id, created_at FROM embed_templates WHERE guild_id=? ORDER BY name",
            (guild_id,),
        )

    async def delete_template(self, guild_id, name):
        """True, если шаблон был и удалён."""
        changed = await self.execute(
            "DELETE FROM embed_templates WHERE guild_id=? AND name=?", (guild_id, name)
        )
        return changed > 0

    # --- карточки участников клана -------------------------------------------
    async def get_clan_member(self, guild_id, user_id):
        return await self.fetchone(
            "SELECT * FROM clan_members WHERE guild_id=? AND user_id=?", (guild_id, user_id)
        )

    async def set_clan_member(self, guild_id, user_id, nick=None, hours=None, timezone=None, note=None):
        """Обновляет только переданные поля, остальные оставляет как были."""
        old = await self.get_clan_member(guild_id, user_id)
        values = {
            "nick": nick if nick is not None else (old["nick"] if old else None),
            "hours": hours if hours is not None else (old["hours"] if old else None),
            "timezone": timezone if timezone is not None else (old["timezone"] if old else None),
            "note": note if note is not None else (old["note"] if old else None),
        }
        await self.execute(
            "INSERT INTO clan_members(guild_id, user_id, nick, hours, timezone, note, updated_at) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(guild_id, user_id) DO UPDATE SET "
            "nick=excluded.nick, hours=excluded.hours, timezone=excluded.timezone, "
            "note=excluded.note, updated_at=excluded.updated_at",
            (guild_id, user_id, values["nick"], values["hours"], values["timezone"],
             values["note"], int(now_ts())),
        )

    async def clear_clan_member(self, guild_id, user_id):
        """True, если карточка была и удалена."""
        changed = await self.execute(
            "DELETE FROM clan_members WHERE guild_id=? AND user_id=?", (guild_id, user_id)
        )
        return changed > 0

    async def list_clan_members(self, guild_id):
        return await self.fetchall(
            "SELECT * FROM clan_members WHERE guild_id=? ORDER BY COALESCE(hours, 0) DESC, nick",
            (guild_id,),
        )
''',
    'vex.checks': r'''"""Система доступа: какая роль может пользоваться какой командой.

Правило простое:
  * администраторы и владелец сервера могут всё;
  * остальным нужна роль, которой выдан доступ командой /perms grant;
  * пока доступ никому не выдан, команда доступна только администраторам.
"""
import discord
from discord import app_commands


class NoAccess(app_commands.CheckFailure):
    def __init__(self, key=None, admin_only=False):
        self.key = key
        self.admin_only = admin_only
        super().__init__("Нет доступа к команде")


def is_admin(member):
    return member.guild_permissions.administrator or member.guild.owner_id == member.id


async def member_has_access(bot, member, key):
    if not isinstance(member, discord.Member):
        return False
    if is_admin(member):
        return True
    allowed = await bot.db.get_targets(member.guild.id, f"cmd:{key}")
    return any(role.id in allowed for role in member.roles)


def access(key):
    """Декоратор слеш-команды: доступ по ролям из /perms."""

    async def predicate(interaction):
        if await member_has_access(interaction.client, interaction.user, key):
            return True
        raise NoAccess(key)

    return app_commands.check(predicate)


def admin_only():
    """Декоратор слеш-команды: только администраторы (для /perms и /config)."""

    async def predicate(interaction):
        user = interaction.user
        if isinstance(user, discord.Member) and is_admin(user):
            return True
        raise NoAccess(admin_only=True)

    return app_commands.check(predicate)
''',
    'vex.modutil': r'''"""Чистые помощники для модерации и ролей (без discord.py — их легко тестировать)."""
import re

UNITS = {
    "s": 1, "с": 1,
    "m": 60, "м": 60,
    "h": 3600, "ч": 3600,
    "d": 86400, "д": 86400,
    "w": 604800, "н": 604800,
}
_DURATION = re.compile(r"(\d+)\s*([smhdwсмчдн])", re.IGNORECASE)

MAX_TIMEOUT = 28 * 86400  # Discord не даёт тайм-аут дольше 28 дней

ACTION_LABELS = {
    "warn": "Предупреждение",
    "mute": "Мут",
    "unmute": "Размут",
    "kick": "Кик",
    "ban": "Бан",
    "unban": "Разбан",
}
ACTION_ICONS = {"warn": "⚠️", "mute": "🔇", "unmute": "🔊", "kick": "👢", "ban": "🔨", "unban": "♻️"}

# категория логов -> (название, описание, включена по умолчанию)
LOG_CATEGORIES = {
    "messages": ("Сообщения", "Удалённые и изменённые сообщения, массовая очистка", True),
    "members": ("Участники", "Входы, выходы, смена ролей и ников", True),
    "voice": ("Голосовые каналы", "Кто зашёл, вышел или перешёл между каналами", False),
    "server": ("Сервер", "Создание и удаление каналов и ролей", True),
}


def parse_duration(text):
    """'30m', '2h', '1d12h', '7д' -> секунды. Не распознано или ноль -> None."""
    text = (text or "").strip().lower()
    if not text:
        return None
    total, pos = 0, 0
    for match in _DURATION.finditer(text):
        if text[pos:match.start()].strip():
            return None
        total += int(match.group(1)) * UNITS[match.group(2).lower()]
        pos = match.end()
    if text[pos:].strip() or total <= 0:
        return None
    return total


def format_duration(seconds):
    seconds = int(seconds)
    parts = []
    for size, name in ((86400, "д"), (3600, "ч"), (60, "мин"), (1, "с")):
        if seconds >= size:
            parts.append(f"{seconds // size} {name}")
            seconds %= size
    return " ".join(parts[:3]) or "0 с"


def hierarchy_error(actor, target, guild, me):
    """Текст ошибки, если actor не может наказать target, иначе None.

    Работает и с участниками, и с «чужими» пользователями (у них нет top_role — проверки ролей пропускаются).
    """
    if target.id == actor.id:
        return "Нельзя применить это к себе."
    if target.id == me.id:
        return "Нельзя применить это к боту VEX."
    if target.id == guild.owner_id:
        return "Нельзя применить это к владельцу сервера."
    target_top = getattr(target, "top_role", None)
    if target_top is None:
        return None
    if actor.id != guild.owner_id and target_top >= actor.top_role:
        return "Роль этого участника не ниже твоей — наказать его нельзя."
    if target_top >= me.top_role:
        return "Роль этого участника выше или равна роли VEX. Подними роль VEX в настройках сервера."
    return None


DANGEROUS_PERMISSIONS = (
    "administrator", "manage_guild", "manage_roles", "manage_channels", "manage_messages",
    "kick_members", "ban_members", "moderate_members", "mention_everyone", "manage_webhooks",
)


def dangerous_role(role):
    """Роль с правами, которые нельзя раздавать кнопками самообслуживания."""
    perms = role.permissions
    return any(getattr(perms, name, False) for name in DANGEROUS_PERMISSIONS)
''',
    'vex.bot': r'''"""Ядро бота: интенты, загрузка модулей, обработка ошибок команд, логирование на сервер."""
import logging

import discord
from discord import app_commands
from discord.ext import commands

from . import config, embeds
from .checks import NoAccess
from .db import Database
from .web import start_web

log = logging.getLogger("vex")

EXTENSIONS = (
    "vex.cogs.tickets",
    "vex.cogs.wipe",
    "vex.cogs.automod",
    "vex.cogs.roles",
    "vex.cogs.staff",
    "vex.cogs.clan",
    "vex.cogs.moderation",
    "vex.cogs.panels",
    "vex.cogs.logs",
    "vex.cogs.admin",
)


class VexTree(app_commands.CommandTree):
    async def on_error(self, interaction, error):
        if isinstance(error, NoAccess):
            if error.admin_only:
                text = "Эта команда доступна только администраторам."
            else:
                text = (
                    "У тебя нет доступа к этой команде.\n"
                    "Администратор может выдать его через `/perms grant`."
                )
            message = embeds.err(text, "Нет доступа")
        elif isinstance(error, app_commands.CheckFailure):
            message = embeds.err("Эту команду нельзя использовать здесь.", "Недоступно")
        else:
            log.error("Ошибка в команде %s", getattr(interaction.command, "name", "?"), exc_info=error)
            message = embeds.err("Что-то пошло не так. Подробности записаны в логи бота.")

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=message, ephemeral=True)
            else:
                await interaction.response.send_message(embed=message, ephemeral=True)
        except discord.HTTPException:
            pass


class VexBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # автороли, поиск не ответивших (включить в Developer Portal)
        intents.message_content = True  # автомодерация ссылок (включить в Developer Portal)
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            tree_cls=VexTree,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
        )
        self.db = Database(config.DATA_DIR / "vex.sqlite3")
        self.web_runner = None
        self.public_url = config.PUBLIC_URL

    async def get_public_url(self):
        """Адрес сайта: из PUBLIC_URL или запомненный после первого входа на сайт."""
        if self.public_url:
            return self.public_url
        self.public_url = await self.db.get_setting(0, "public_url", "")
        return self.public_url

    async def remember_public_url(self, url):
        if url and url != self.public_url and not config.PUBLIC_URL:
            self.public_url = url
            await self.db.set_setting(0, "public_url", url)

    async def close(self):
        if self.web_runner is not None:
            await self.web_runner.cleanup()
        await super().close()

    async def setup_hook(self):
        self.db.connect()
        log.info("База данных: %s", self.db.path.resolve())
        for extension in EXTENSIONS:
            await self.load_extension(extension)

        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        log.info("Синхронизировано команд: %d", len(synced))
        self.web_runner = await start_web(self)

    async def on_ready(self):
        log.info("VEX запущен как %s (серверов: %d)", self.user, len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="за кланом")
        )

    async def send_log(self, guild, embed, key="mod_log", file=None):
        """Отправляет эмбед в лог-канал сервера. Для тикетов, если нет своего канала, берёт общий."""
        channel_id = await self.db.get_setting(guild.id, key)
        if not channel_id and key != "mod_log":
            channel_id = await self.db.get_setting(guild.id, "mod_log")
        if not channel_id:
            return
        channel = guild.get_channel(int(channel_id))
        if channel is None:
            return
        try:
            await channel.send(embed=embed, file=file)
        except discord.HTTPException:
            log.warning("Не удалось отправить лог в канал %s", channel_id)
''',
    'vex.webui': r'''"""Страницы сайта VEX: чистые функции «данные -> HTML». Без зависимостей от discord и aiohttp.

Во всех формах стоит метка __CSRF__ — layout() заменяет её на токен сессии.
"""
import html
import re
import zlib
from datetime import datetime
from zoneinfo import ZoneInfo

FLASH_OK = {
    "saved": "Сохранено.",
    "sent": "Панель отправлена в канал.",
    "deleted": "Удалено.",
    "reminded": "Напоминание отправлено.",
    "noone": "Все уже ответили — напоминать некому.",
}
FLASH_ERR = {
    "denied": "Вход отменён.",
    "state": "Не удалось подтвердить вход. Попробуй ещё раз.",
    "oauth": "Discord не принял вход. Проверь Client Secret и Redirect URI в Developer Portal.",
    "nosecret": "Сайт не настроен: не задана переменная DISCORD_CLIENT_SECRET.",
    "types_empty": "Добавь хотя бы один тип обращения.",
    "types_many": "Типов обращений может быть не больше 25.",
    "channel": "Выбери канал из списка.",
    "noperm": "У VEX нет прав писать в этот канал.",
    "noevent": "Событие не найдено.",
    "nocog": "Модуль бота ещё не загружен, попробуй через минуту.",
    "nocase": "Активное предупреждение с таким номером не найдено.",
    "nopanel": "Панель не найдена.",
    "panel_title": "Укажи заголовок панели.",
    "panel_roles": "Выбери хотя бы одну роль для кнопок (замки 🔒 выбрать нельзя).",
}

# (раздел, название, значок, только для администраторов)
NAV = [
    ("", "Обзор", "🏠", False),
    ("moderation", "Модерация", "🔨", False),
    ("access", "Доступ к командам", "🔐", True),
    ("roles", "Роли", "🎭", True),
    ("panels", "Панели ролей", "🎛️", True),
    ("automod", "Автомодерация", "🛡️", True),
    ("tickets", "Тикеты", "🎫", True),
    ("events", "События", "📝", False),
    ("logs", "Логи", "📜", True),
    ("general", "Общие", "⚙️", True),
]


def nav_for(level):
    """Разделы, доступные уровню: «admin» видит всё, «staff» (роль с доступом к /dashboard) — только общие."""
    return [item for item in NAV if level == "admin" or not item[3]]

CSS = """
:root{color-scheme:dark;--bg:#0e0a1a;--panel:#171124;--panel2:#1e1730;--line:#2d2447;--text:#eee9fb;--muted:#9d93bd;
--brand:#8b5cf6;--brand2:#6d28d9;--ok:#22c55e;--err:#ef4444;--warn:#f59e0b;--r:14px}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--text);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Arial,sans-serif;
background:radial-gradient(900px 500px at 85% -10%,#2b1b57 0,transparent 60%),radial-gradient(700px 400px at -10% 110%,#1d1240 0,transparent 55%),var(--bg)}
a{color:#c4b5fd;text-decoration:none}a:hover{text-decoration:underline}
code{background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:.9em}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:18px;margin:0 0 4px}h3{font-size:15px;margin:0 0 8px}
.muted,.sub{color:var(--muted)}
.top{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--line);background:rgba(14,10,26,.75);
backdrop-filter:blur(8px);position:sticky;top:0;z-index:5}
.brand{display:flex;align-items:baseline;gap:10px;color:var(--text)}.brand:hover{text-decoration:none}
.brand b{font-size:20px;letter-spacing:.12em;background:linear-gradient(135deg,#c4b5fd,#8b5cf6);-webkit-background-clip:text;background-clip:text;color:transparent}
.brand small{color:var(--muted);font-size:12px}
.spacer{flex:1}
.user{display:flex;align-items:center;gap:10px}.user img{border-radius:50%}.user form{margin:0}
.link{background:none;border:0;color:#c4b5fd;cursor:pointer;font:inherit;padding:0}.link:hover{text-decoration:underline}
.shell{display:block;max-width:1120px;margin:0 auto;padding:24px 20px 60px}
.shell.has-side{display:grid;grid-template-columns:230px minmax(0,1fr);gap:28px;max-width:1280px}
.side{position:sticky;top:76px;align-self:start}
.guild{display:flex;align-items:center;gap:10px;padding:10px 12px;margin-bottom:12px;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);font-weight:600}
.side nav{display:flex;flex-direction:column;gap:2px}
.side nav a{display:flex;gap:10px;align-items:center;padding:9px 12px;border-radius:10px;color:var(--text)}
.side nav a:hover{background:var(--panel);text-decoration:none}
.side nav a.active{background:linear-gradient(135deg,rgba(139,92,246,.32),rgba(109,40,217,.22));box-shadow:inset 0 0 0 1px rgba(139,92,246,.55)}
.ico{width:32px;height:32px;border-radius:50%;flex:none;object-fit:cover}
.ico.ph{display:grid;place-items:center;background:var(--brand2);font-weight:700}
.head{margin-bottom:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:18px 20px;margin-bottom:16px}
.card>h2{margin-bottom:2px}.card>.sub{margin:0 0 14px}
.block{padding:14px 0;border-top:1px solid var(--line)}.block:first-of-type{border-top:0;padding-top:4px}
.block h3 small{color:var(--muted);font-weight:400;margin-left:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:14px 16px}
.tile b{display:block;font-size:24px;line-height:1.2}.tile span{color:var(--muted);font-size:13px}
.gcard{display:flex;align-items:center;gap:12px;padding:14px 16px;background:var(--panel);border:1px solid var(--line);border-radius:var(--r);color:var(--text)}
.gcard:hover{border-color:var(--brand);text-decoration:none;transform:translateY(-1px)}
.gcard small{display:block;color:var(--muted)}
.field{margin:0 0 16px}.field>label,.field>.lbl{display:block;font-weight:600;margin-bottom:6px}
.hint{color:var(--muted);font-size:13px;margin-top:4px}
input[type=text],input[type=number],select,textarea{width:100%;background:var(--panel2);color:var(--text);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font:inherit}
input:focus,select:focus,textarea:focus{outline:2px solid rgba(139,92,246,.6);outline-offset:1px;border-color:var(--brand)}
textarea{min-height:110px;resize:vertical}textarea.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13.5px}
input[type=number]{max-width:140px}
.row{display:flex;gap:16px;flex-wrap:wrap}.row .field{flex:1;min-width:170px}
.check{display:flex;align-items:center;gap:10px;cursor:pointer}.check input{width:18px;height:18px;accent-color:var(--brand)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{position:relative}.chip input{position:absolute;opacity:0;inset:0;width:100%;height:100%;cursor:pointer;margin:0}
.chip span{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border:1px solid var(--line);border-radius:999px;background:var(--panel2);color:var(--muted);transition:.12s}
.chip:hover span{border-color:var(--brand);color:var(--text)}
.chip input:checked+span{background:var(--brand2);border-color:var(--brand);color:#fff}
.chip input:focus-visible+span{outline:2px solid #c4b5fd;outline-offset:2px}
.chip.locked{opacity:.45}.chip.locked input{cursor:not-allowed}
.dot{width:10px;height:10px;border-radius:50%;display:inline-block;flex:none}
.actions{margin-top:6px;display:flex;gap:10px;flex-wrap:wrap}
.btn{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;border:0;border-radius:10px;padding:10px 18px;font:inherit;font-weight:600;cursor:pointer}
.btn:hover{filter:brightness(1.1);text-decoration:none}
.btn.ghost{background:var(--panel2);border:1px solid var(--line);color:var(--text)}
.btn.danger{background:#b91c1c}.btn.sm{padding:5px 12px;font-size:13px}
.flash{padding:12px 16px;border-radius:12px;margin-bottom:16px;border:1px solid}
.flash.ok{background:rgba(34,197,94,.12);border-color:rgba(34,197,94,.5)}
.flash.err{background:rgba(239,68,68,.12);border-color:rgba(239,68,68,.55)}
.flash.warn{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.5)}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 10px;border-top:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;font-size:13px;border-top:0}
.tablewrap{overflow-x:auto}
ul.health{list-style:none;margin:0;padding:0}ul.health li{padding:6px 0}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;background:var(--panel2);border:1px solid var(--line)}
.pill.on{background:rgba(34,197,94,.15);border-color:rgba(34,197,94,.5)}.pill.off{background:rgba(239,68,68,.15);border-color:rgba(239,68,68,.5)}
.inline{display:inline-block;margin:0 6px 4px 0}
details summary{cursor:pointer;color:#fca5a5;display:inline-block}
.hero{text-align:center;padding:70px 10px 40px}.hero h1{font-size:40px}.hero p{color:var(--muted);max-width:520px;margin:10px auto 26px}
@media (max-width:860px){
.shell.has-side{grid-template-columns:minmax(0,1fr);gap:14px}
.side{position:static;min-width:0}.side nav{flex-direction:row;overflow-x:auto;padding-bottom:6px}.side nav a{white-space:nowrap}
main{min-width:0}.shell{padding:16px 16px 50px}.card{padding:16px}
.top{padding:10px 14px}.brand small,.user span{display:none}.hero h1{font-size:30px}
}
"""


def esc(value):
    return html.escape(str(value), quote=True)


# --------------------------------------------------------------------------- разбор форм
def is_emoji(text):
    """Грубая проверка «это эмодзи» (Discord отклоняет мусор в SelectOption)."""
    return bool(text) and len(text) <= 8 and all(ord(ch) > 0x2000 for ch in text)


def make_slug(label):
    return re.sub(r"[^\w]+", "-", label.lower()).strip("-")[:20] or "ticket"


def types_to_text(types):
    return "\n".join(f"{t.get('emoji', '')} | {t['label']} | {t.get('description', '')}" for t in types)


def parse_types_text(text, existing):
    """Строки вида «эмодзи | Название | Описание» -> (список типов, код ошибки).

    existing: {название в нижнем регистре: (key, slug)} — чтобы старые тикеты не теряли свой тип.
    """
    types, used = [], set()
    for line in str(text).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            emoji, label, desc = parts[0], parts[1], " | ".join(parts[2:])
        elif len(parts) == 2:
            if is_emoji(parts[0]):
                emoji, label, desc = parts[0], parts[1], ""
            else:
                emoji, label, desc = "", parts[0], parts[1]
        else:
            emoji, label, desc = "", parts[0], ""
        if not is_emoji(emoji):
            emoji = ""
        label, desc = label[:100], desc[:100]
        if not label:
            continue
        found = existing.get(label.lower())
        key = found[0] if found else f"{zlib.crc32(label.lower().encode('utf-8')):08x}"
        slug = found[1] if found else make_slug(label)
        if key in used:
            continue
        used.add(key)
        types.append({"key": key, "slug": slug, "label": label, "emoji": emoji, "description": desc})
    if not types:
        return None, "types_empty"
    if len(types) > 25:
        return None, "types_many"
    return types, None


def fmt_ts(ts, tz):
    try:
        return datetime.fromtimestamp(int(ts), ZoneInfo(tz)).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(ts)


# --------------------------------------------------------------------------- кирпичики
def icon(url, name, size=32):
    if url:
        return f'<img class="ico" src="{esc(url)}" alt="" width="{size}" height="{size}">'
    letter = esc((name or "?")[:1].upper())
    return f'<span class="ico ph" style="width:{size}px;height:{size}px">{letter}</span>'


def chips(name, items, selected, empty="Ничего не найдено."):
    if not items:
        return f'<p class="muted">{esc(empty)}</p>'
    sel = set(selected)
    out = ['<div class="chips">']
    for it in items:
        locked = bool(it.get("locked"))
        checked = " checked" if (it["id"] in sel and not locked) else ""
        dot = ""
        if "color" in it:
            color = it["color"] or 0x99AAB5
            dot = f'<i class="dot" style="background:#{color:06x}"></i>'
        lock = "🔒 " if locked else ""
        out.append(
            f'<label class="chip{" locked" if locked else ""}"><input type="checkbox" name="{esc(name)}" '
            f'value="{it["id"]}"{checked}{" disabled" if locked else ""}><span>{dot}{lock}{esc(it["name"])}</span></label>'
        )
    out.append("</div>")
    return "".join(out)


def select(name, items, selected, blank="— не выбран —"):
    out = [f'<select name="{esc(name)}"><option value="">{esc(blank)}</option>']
    for it in items:
        sel = " selected" if selected is not None and it["id"] == selected else ""
        out.append(f'<option value="{it["id"]}"{sel}>{esc(it["name"])}</option>')
    out.append("</select>")
    return "".join(out)


def field(label, control, hint=""):
    hint_html = f'<div class="hint">{hint}</div>' if hint else ""
    return f'<div class="field"><span class="lbl">{esc(label)}</span>{control}{hint_html}</div>'


def card(title, inner, sub=""):
    sub_html = f'<p class="sub">{sub}</p>' if sub else ""
    return f'<section class="card"><h2>{esc(title)}</h2>{sub_html}{inner}</section>'


def head(title, sub=""):
    return f'<div class="head"><h1>{esc(title)}</h1><p class="sub">{sub}</p></div>'


def form(action, inner, button="Сохранить"):
    return (
        f'<form method="post" action="{esc(action)}"><input type="hidden" name="csrf" value="__CSRF__">'
        f'{inner}<div class="actions"><button class="btn" type="submit">{esc(button)}</button></div></form>'
    )


def mini_form(action, button, cls="btn ghost sm"):
    return (
        f'<form class="inline" method="post" action="{esc(action)}"><input type="hidden" name="csrf" value="__CSRF__">'
        f'<button class="{cls}" type="submit">{esc(button)}</button></form>'
    )


def tiles(items):
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in items
    ) + "</div>"


def layout(title, body, *, user=None, guild=None, section=None, csrf="", ok=None, err=None, level="admin"):
    flash = ""
    if ok:
        flash += f'<div class="flash ok">✅ {esc(FLASH_OK.get(ok, "Готово."))}</div>'
    if err:
        flash += f'<div class="flash err">⛔ {esc(FLASH_ERR.get(err, "Что-то пошло не так."))}</div>'

    side = ""
    switch = ""
    if guild:
        links = []
        for slug, label, emoji, _admin_only in nav_for(level):
            href = f"/g/{guild['id']}" + (f"/{slug}" if slug else "")
            cls = ' class="active"' if slug == (section or "") else ""
            links.append(f'<a{cls} href="{href}"><span>{emoji}</span>{esc(label)}</a>')
        side = (
            f'<aside class="side"><div class="guild">{icon(guild.get("icon"), guild["name"])}'
            f'<span>{esc(guild["name"])}</span></div><nav>{"".join(links)}</nav></aside>'
        )
        switch = '<a href="/">Сменить сервер</a>'

    userbar = ""
    if user:
        userbar = (
            f'<div class="user"><img src="{esc(user["avatar"])}" alt="" width="28" height="28"><span>{esc(user["name"])}</span>'
            '<form method="post" action="/logout"><input type="hidden" name="csrf" value="__CSRF__">'
            '<button class="link" type="submit">Выйти</button></form></div>'
        )

    page = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} · VEX</title><style>{CSS}</style></head><body>"
        '<header class="top"><a class="brand" href="/"><b>VEX</b><small>панель управления</small></a>'
        f'<span class="spacer"></span>{switch}{userbar}</header>'
        f'<div class="shell{" has-side" if guild else ""}">{side}<main>{flash}{body}</main></div></body></html>'
    )
    return page.replace("__CSRF__", esc(csrf))


# --------------------------------------------------------------------------- страницы
def login_page(configured):
    if configured:
        action = '<a class="btn" href="/login">Войти через Discord</a>'
    else:
        action = (
            '<div class="flash warn">Сайт ещё не настроен: на хостинге не задана переменная '
            "<code>DISCORD_CLIENT_SECRET</code>.</div>"
        )
    return (
        '<section class="hero"><h1>VEX</h1>'
        "<p>Панель управления ботом для клана: доступ к командам, роли, автомодерация, тикеты и события — всё в браузере.</p>"
        f"{action}</section>"
    )


def guilds_page(guilds, invite_url):
    if guilds:
        cards = "".join(
            f'<a class="gcard" href="/g/{g["id"]}">{icon(g.get("icon"), g["name"], 40)}'
            f'<div><b>{esc(g["name"])}</b><small>{esc(g.get("members", ""))} участников</small></div></a>'
            for g in guilds
        )
        body = f'<div class="grid">{cards}</div>'
    else:
        body = (
            '<div class="flash warn">Не нашёл серверов, где ты администратор и где уже есть VEX. '
            "Пригласи бота на свой сервер и обнови страницу.</div>"
        )
    body += f'<p style="margin-top:18px"><a class="btn ghost" href="{esc(invite_url)}">➕ Добавить VEX на сервер</a></p>'
    return head("Твои серверы", "Выбери сервер, которым хочешь управлять.") + body


def overview_page(gid, stats, health, recent, level="admin"):
    t = tiles([
        (stats["open_tickets"], "открытых тикетов"),
        (stats["active_events"], "ближайших событий"),
        ("вкл" if stats["automod_on"] else "выкл", "автомодерация"),
        (stats["members"], "участников"),
    ])
    items = "".join(
        f'<li>{"ℹ️" if ok is None else ("✅" if ok else "⛔")} {esc(text)}</li>' for ok, text in health
    )
    health_card = card("Состояние бота", f'<ul class="health">{items}</ul>')

    if recent:
        rows = "".join(
            f"<tr><td>{esc(r['when'])}</td><td>{esc(r['user'])}</td><td>{esc(r['channel'])}</td>"
            f"<td><code>{esc(r['link'])}</code></td></tr>"
            for r in recent
        )
        table = (
            '<div class="tablewrap"><table><tr><th>Когда</th><th>Кто</th><th>Канал</th><th>Ссылка</th></tr>'
            f"{rows}</table></div>"
        )
    else:
        table = '<p class="muted">Пока нарушений не было.</p>'
    recent_card = card("Последние срабатывания автомодерации", table)

    links = "".join(
        f'<a class="gcard" href="/g/{gid}/{slug}"><span style="font-size:22px">{emoji}</span><b>{esc(label)}</b></a>'
        for slug, label, emoji, _admin_only in nav_for(level) if slug
    )
    return head("Обзор", "Состояние бота и быстрые ссылки.") + t + health_card + recent_card + f'<div class="grid">{links}</div>'


def access_page(gid, roles, selected, keys):
    blocks = "".join(
        f'<div class="block"><h3><code>{esc(key)}</code><small>{esc(desc)}</small></h3>'
        f'{chips("cmd_" + key, roles, selected.get(key, []), "На сервере нет ролей.")}</div>'
        for key, desc in keys.items()
    )
    note = (
        '<div class="flash warn">Администраторы сервера всегда имеют доступ ко всем командам. '
        "Если у группы не выбрано ни одной роли — команды этой группы доступны только администраторам.</div>"
    )
    return (
        head("Доступ к командам", "Какие роли могут пользоваться какими командами бота.")
        + note + card("Группы команд", form(f"/g/{gid}/access", blocks))
    )


def roles_page(gid, assign_roles, manage_roles, member_sel, bot_sel, manageable_sel):
    inner = (
        '<div class="block"><h3>Роли новым участникам<small>выдаются при заходе на сервер</small></h3>'
        + chips("autorole_member", assign_roles, member_sel)
        + '</div><div class="block"><h3>Роли новым ботам<small>выдаются при добавлении бота</small></h3>'
        + chips("autorole_bot", assign_roles, bot_sel)
        + '</div><div class="block"><h3>Роли, которые модераторы могут выдавать<small>через /role add и /role remove</small></h3>'
        + chips("manageable", manage_roles, manageable_sel)
        + '<div class="hint">Если ничего не выбрано — можно выдавать любые роли ниже своей, кроме ролей с опасными правами.</div></div>'
    )
    note = (
        '<div class="flash warn">Роли с замком 🔒 стоят выше роли VEX или управляются интеграцией, поэтому бот не сможет их выдать. '
        "Подними роль VEX выше них в настройках сервера → Роли.</div>"
    )
    return head("Роли", "Авто-выдача при заходе и список ролей для модераторов.") + note + card("Настройки", form(f"/g/{gid}/roles", inner))


def automod_page(gid, s, roles, channels, default_domains):
    switch = (
        f'<label class="check"><input type="checkbox" name="enabled" value="1"{" checked" if s["enabled"] else ""}>'
        "<span>Автомодерация ссылок включена</span></label>"
    )
    punish = (
        '<div class="row">'
        + field("Нарушений до тайм-аута", f'<input type="number" name="strikes" min="1" max="10" value="{s["strikes"]}">',
                "Считаются за последние 10 минут.")
        + field("Тайм-аут, минут", f'<input type="number" name="timeout" min="0" max="1440" value="{s["timeout"]}">',
                "0 — не выдавать, только удалять ссылки.")
        + "</div>"
    )
    defaults = ", ".join(f"<code>{esc(d)}</code>" for d in default_domains)
    domains = field(
        "Разрешённые домены",
        f'<textarea class="mono" name="domains" placeholder="youtube.com&#10;twitch.tv">{esc(s["domains_text"])}</textarea>',
        f"По одному в строке. Поддомены разрешаются сами. Всегда разрешены: {defaults}.",
    )
    bypass = field("Роли, которых автомодерация не проверяет", chips("bypass", roles, s["bypass"]),
                   "Администраторы и модераторы с правом «Управлять сообщениями» не проверяются никогда.")
    ignore = field("Каналы, где ссылки разрешены", chips("ignore", channels, s["ignore"]))
    return head("Автомодерация", "Защита от нежелательных ссылок и инвайтов.") + card(
        "Настройки", form(f"/g/{gid}/automod", switch + "<br><br>" + punish + domains + bypass + ignore)
    )


def tickets_page(gid, t, categories, channels, roles, open_tickets):
    settings = (
        '<div class="row">'
        + field("Категория для тикетов", select("category", categories, t["category"]),
                "Новые тикеты создаются в этой категории.")
        + field("Канал для логов тикетов", select("log_channel", channels, t["log_channel"]),
                "Сюда приходят переписки закрытых тикетов.")
        + field("Тикетов на человека", f'<input type="number" name="max_open" min="1" max="5" value="{t["max_open"]}">')
        + "</div>"
        + '<div class="row">'
        + field("После закрытия",
                select("delete_on_close", [{"id": 0, "name": "Переносить в архив"}],
                       1 if t["delete_on_close"] else 0, "Удалять канал"),
                "Транскрипт сохраняется в любом случае.")
        + field("Категория-архив", select("archive", categories, t["archive"]),
                "Нужна, если каналы переносятся в архив.")
        + field("Автозакрытие, часов", f'<input type="number" name="autoclose" min="0" max="720" value="{t["autoclose"]}">',
                "Закрывать тикет после стольких часов тишины. 0 — выключено.")
        + "</div>"
        + field("Роли поддержки", chips("support", roles, t["support"]),
                "Видят все тикеты и могут их вести.")
        + field(
            "Типы обращений (меню на панели)",
            f'<textarea class="mono" name="types" rows="7">{esc(t["types_text"])}</textarea>',
            "По одному в строке: <code>эмодзи | Название | Описание</code>. Не больше 25. "
            "После изменения отправь панель заново — старая панель обновится при ближайшем выборе в меню.",
        )
    )
    panel = (
        '<div class="row">'
        + field("Канал", select("channel", channels, None, "— выбери канал —"))
        + field("Заголовок (необязательно)", '<input type="text" name="title" maxlength="200" placeholder="🎫 Центр поддержки">')
        + "</div>"
        + field("Текст (необязательно)", '<textarea name="description" rows="4" maxlength="2000" '
                'placeholder="Если пусто — стандартный текст со списком типов"></textarea>')
    )
    if open_tickets:
        rows = "".join(
            f"<tr><td>#{x['id']:04d}</td><td>{esc(x['user'])}</td><td>{esc(x['type'])}</td>"
            f"<td>{esc(x.get('priority', ''))}</td><td>{esc(x['status'])}</td><td>{esc(x['created'])}</td><td><code>#{esc(x['channel'])}</code></td></tr>"
            for x in open_tickets
        )
        table = (
            '<div class="tablewrap"><table><tr><th>№</th><th>Автор</th><th>Тип</th><th>Приоритет</th><th>Статус</th><th>Создан</th><th>Канал</th></tr>'
            f"{rows}</table></div>"
        )
    else:
        table = '<p class="muted">Открытых тикетов нет.</p>'
    return (
        head("Тикеты", "Панель обращений, роли поддержки и список открытых тикетов.")
        + card("Настройки", form(f"/g/{gid}/tickets", settings))
        + card("Отправить панель", form(f"/g/{gid}/tickets/panel", panel, "Отправить панель"),
               "Сообщение с меню, через которое участники открывают тикеты.")
        + card("Открытые тикеты", table)
    )


def events_page(gid, events):
    if not events:
        return head("События", "Вайп-реакты, созданные командой /wipereact.") + card(
            "События", '<p class="muted">Событий пока нет. Создай первое командой <code>/wipereact</code> в Discord.</p>'
        )
    rows = []
    for e in events:
        base = f"/g/{gid}/events/{e['message_id']}"
        status = '<span class="pill off">приём закрыт</span>' if e["closed"] else '<span class="pill on">идёт приём</span>'
        actions = (
            mini_form(f"{base}/toggle", "Открыть приём" if e["closed"] else "Закрыть приём")
            + mini_form(f"{base}/remind", "Напомнить не ответившим")
            + f'<details class="inline"><summary>Удалить</summary>{mini_form(f"{base}/delete", "Точно удалить", "btn danger sm")}</details>'
        )
        rows.append(
            f"<tr><td><b>{esc(e['title'])}</b><br><a href=\"{esc(e['url'])}\" target=\"_blank\" rel=\"noopener\">#{esc(e['channel'])}</a></td>"
            f"<td>{esc(e['when'])}</td><td>✅ {e['accepted']} · ❌ {e['declined']} · 🕒 {e['late']}</td><td>{status}</td><td>{actions}</td></tr>"
        )
    table = (
        '<div class="tablewrap"><table><tr><th>Событие</th><th>Когда</th><th>Ответы</th><th>Статус</th><th>Действия</th></tr>'
        + "".join(rows) + "</table></div>"
    )
    return head("События", "Вайп-реакты, созданные командой /wipereact.") + card("Последние события", table)


def general_page(gid, g, channels, timezone):
    inner = (
        field("Лог-канал модерации", select("mod_log", channels, g["mod_log"]),
              "Сюда пишутся действия автомодерации, выдача ролей, сообщения /say, входы и выходы.")
        + field("Канал приветствий", select("welcome_channel", channels, g["welcome_channel"]),
                "Если не выбран — приветствия выключены.")
        + field("Текст приветствия", f'<textarea name="welcome_text" rows="4" maxlength="1500" '
                f'placeholder="{esc(g["welcome_default"])}">{esc(g["welcome_text"])}</textarea>',
                "Можно использовать <code>{user}</code> и <code>{server}</code>. Пусто — стандартный текст.")
    )
    info = f'<p class="muted">Часовой пояс бота: <code>{esc(timezone)}</code> (задаётся переменной <code>TIMEZONE</code> на хостинге).</p>'
    return head("Общие настройки", "Логи и приветствие новых участников.") + card("Настройки", form(f"/g/{gid}/general", inner)) + info


def moderation_page(gid, s, cases, is_admin):
    parts = [head("Модерация", "История наказаний сервера. Выдавать наказания можно командами в Discord: "
                  "<code>/warn</code> <code>/mute</code> <code>/kick</code> <code>/ban</code>.")]
    if is_admin:
        inner = (
            '<div class="row">'
            + field("Предупреждений до автоматического мута",
                    f'<input type="number" name="warn_threshold" min="0" max="20" value="{s["warn_threshold"]}">',
                    "0 — автоматический мут выключен.")
            + field("Длительность автоматического мута, минут",
                    f'<input type="number" name="warn_timeout" min="1" max="40320" value="{s["warn_timeout"]}">',
                    "Максимум 40320 (28 дней).")
            + "</div>"
        )
        parts.append(card("Автоматические наказания", form(f"/g/{gid}/moderation", inner)))
    if cases:
        rows = []
        for c in cases:
            status = ""
            if c["action"] == "warn":
                status = '<span class="pill on">активно</span>' if c["active"] else '<span class="pill">снято</span>'
            elif c["action"] == "ban" and c["active"] and c.get("expires"):
                status = f'<span class="pill on">до {esc(c["expires"])}</span>'
            action = mini_form(f"/g/{gid}/moderation/{c['no']}/revoke", "Снять") if c["action"] == "warn" and c["active"] else ""
            rows.append(
                f"<tr><td>#{c['no']}</td><td>{esc(c['when'])}</td><td>{esc(c['icon'])} {esc(c['label'])} {status}</td>"
                f"<td>{esc(c['user'])}</td><td>{esc(c['mod'])}</td><td>{esc(c['reason'])}</td><td>{action}</td></tr>"
            )
        table = (
            '<div class="tablewrap"><table><tr><th>№</th><th>Когда</th><th>Действие</th><th>Участник</th>'
            '<th>Модератор</th><th>Причина</th><th></th></tr>' + "".join(rows) + "</table></div>"
        )
    else:
        table = '<p class="muted">Наказаний пока не было.</p>'
    parts.append(card("Последние наказания", table))
    return "".join(parts)


def panel_form(action, p, channels, roles, button):
    inner = (
        field("Заголовок", f'<input type="text" name="title" maxlength="200" required value="{esc(p["title"])}" '
                           'placeholder="Выбери свою роль">')
        + field("Описание (необязательно)",
                f'<textarea name="description" rows="3" maxlength="1500">{esc(p["description"])}</textarea>')
        + '<div class="row">'
        + field("Канал", select("channel", channels, p["channel_id"], "— выбери канал —"))
        + field("Режим", f'<label class="check"><input type="checkbox" name="exclusive" value="1"'
                         f'{" checked" if p["exclusive"] else ""}><span>Только одна роль на выбор</span></label>')
        + "</div>"
        + field("Роли-кнопки", chips("roles", roles, p["role_ids"]),
                "Участники нажимают на кнопку, чтобы взять или снять роль. До 25 ролей.")
    )
    return form(action, inner, button)


def panels_page(gid, panels, channels, roles):
    note = (
        '<div class="flash warn">Роли с замком 🔒 нельзя сделать кнопками: они выше роли VEX, управляются интеграцией '
        "или дают опасные права (администратор, управление, баны и т.п.).</div>"
    )
    blank = {"title": "", "description": "", "channel_id": None, "exclusive": False, "role_ids": []}
    parts = [head("Панели ролей", "Сообщения с кнопками, по которым участники сами берут и снимают роли."), note,
             card("Новая панель", panel_form(f"/g/{gid}/panels/new", blank, channels, roles, "Создать и отправить"))]
    for p in panels:
        base = f"/g/{gid}/panels/{p['id']}"
        tools = (
            mini_form(f"{base}/resend", "Обновить сообщение")
            + f'<details class="inline"><summary>Удалить панель</summary>{mini_form(f"{base}/delete", "Точно удалить", "btn danger sm")}</details>'
        )
        edit = f'<details><summary style="color:#c4b5fd">Редактировать</summary>{panel_form(base, p, channels, roles, "Сохранить и обновить")}</details>'
        parts.append(card(p["title"], f'<p class="muted">Канал: <code>#{esc(p["channel"])}</code> · ролей: {len(p["role_ids"])}</p>'
                          + tools + "<br><br>" + edit))
    return "".join(parts)


def logs_page(gid, cats, channels):
    blocks = []
    for c in cats:
        blocks.append(
            f'<div class="block"><h3>{esc(c["label"])}<small>{esc(c["desc"])}</small></h3>'
            f'<label class="check"><input type="checkbox" name="on_{esc(c["key"])}" value="1"{" checked" if c["enabled"] else ""}>'
            "<span>Записывать</span></label><br>"
            + field("Канал для этих логов", select(f"ch_{c['key']}", channels, c["channel_id"], "— общий лог-канал —"))
            + "</div>"
        )
    note = (
        '<div class="flash warn">Если канал не выбран, записи идут в общий лог-канал (раздел «Общие»). '
        "Без общего канала такие логи не пишутся. Действия модерации (предупреждения, баны) всегда идут в общий лог-канал.</div>"
    )
    return head("Логи", "Что бот записывает о жизни сервера.") + note + card("Категории", form(f"/g/{gid}/logs", "".join(blocks)))


def error_page(text):
    return f'<section class="hero"><h1>Ой</h1><p>{esc(text)}</p><a class="btn" href="/">На главную</a></section>'
''',
    'vex.web': r'''"""Сайт-панель VEX: вход через Discord (OAuth2), настройка бота в браузере.

Работает в том же процессе, что и бот, и пользуется той же базой.
Включается, только если хостинг передал порт (переменная PORT).
"""
import json
import logging
import re
import secrets
import time
from urllib.parse import urlencode

import discord
from aiohttp import ClientSession, ClientTimeout, web

from . import config, webui
from .checks import is_admin, member_has_access
from .cogs.admin import DEFAULT_WELCOME
from .cogs.automod import normalize_domain
from .modutil import ACTION_ICONS, ACTION_LABELS, LOG_CATEGORIES, dangerous_role

log = logging.getLogger("vex.web")

API = "https://discord.com/api/v10"
SESSION_TTL = 12 * 3600
COOKIE = "vex_session"
STATE_COOKIE = "vex_state"
INVITE_PERMISSIONS = 1099780320272
ADMINISTRATOR = 0x8
USER_AGENT = "DiscordBot (https://discord.com, 1.0) VEX-dashboard"

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' https://cdn.discordapp.com data:; style-src 'unsafe-inline'; "
        "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Cache-Control": "no-store",
}


# --------------------------------------------------------------------------- общие помощники
def base_url(request):
    if config.PUBLIC_URL:
        return config.PUBLIC_URL
    proto = request.headers.get("X-Forwarded-Proto", request.scheme).split(",")[0].strip()
    host = request.headers.get("X-Forwarded-Host", request.host).split(",")[0].strip()
    return f"{proto}://{host}"


def is_https(request):
    return base_url(request).startswith("https://")


def html_response(text, status=200):
    return web.Response(text=text, status=status, content_type="text/html", charset="utf-8")


def current_session(request):
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    store = request.app["sessions"]
    sess = store.get(token)
    if sess is None:
        return None
    if sess["exp"] < time.time():
        store.pop(token, None)
        return None
    return sess


async def access_level(bot, sess, guild):
    """«admin» — администратор сервера, «staff» — роль с доступом к /dashboard, иначе None."""
    member = guild.get_member(sess["uid"])
    if member is not None:  # права проверяем по живым данным: их могли отозвать после входа
        if is_admin(member):
            return "admin"
        if await member_has_access(bot, member, "dashboard"):
            return "staff"
        return None
    return "admin" if guild.id in sess["admin"] else None


async def authorize(request, staff_ok=False):
    """Проверяет вход и права на сервер. Возвращает (сессия, сервер, уровень) или прерывает запрос.

    staff_ok=True пускает и роли с доступом к /dashboard, иначе — только администраторов.
    """
    sess = current_session(request)
    if sess is None:
        raise web.HTTPFound("/")
    try:
        gid = int(request.match_info["gid"])
    except (KeyError, ValueError):
        raise web.HTTPNotFound(text="Сервер не найден")
    if gid not in sess["guilds"]:
        raise web.HTTPForbidden(text="Нет доступа к этому серверу")
    bot = request.app["bot"]
    guild = bot.get_guild(gid)
    if guild is None:
        raise web.HTTPNotFound(text="VEX не добавлен на этот сервер")
    level = await access_level(bot, sess, guild)
    if level is None:
        raise web.HTTPForbidden(text="Нет доступа: нужна роль с доступом к /dashboard или права администратора")
    if level == "staff" and not staff_ok:
        raise web.HTTPForbidden(text="Этот раздел доступен только администраторам сервера")
    return sess, guild, level


def check_csrf(sess, data):
    if not secrets.compare_digest(str(data.get("csrf", "")), sess["csrf"]):
        raise web.HTTPForbidden(text="Сессия устарела. Обнови страницу и повтори.")


async def post_context(request, staff_ok=False):
    sess, guild, level = await authorize(request, staff_ok)
    data = await request.post()
    check_csrf(sess, data)
    return sess, guild, data, level


def back(gid, section="", ok=None, err=None):
    path = f"/g/{gid}" + (f"/{section}" if section else "")
    if ok:
        path += f"?ok={ok}"
    elif err:
        path += f"?err={err}"
    return web.HTTPSeeOther(path)


def render(request, sess, title, body, guild=None, section=None, level="admin"):
    user = {"name": sess["name"], "avatar": sess["avatar"]} if sess else None
    guild_ctx = None
    if guild is not None:
        guild_ctx = {"id": guild.id, "name": guild.name, "icon": guild.icon.url if guild.icon else None}
    text = webui.layout(
        title, body, user=user, guild=guild_ctx, section=section, level=level,
        csrf=sess["csrf"] if sess else "", ok=request.query.get("ok"), err=request.query.get("err"),
    )
    return html_response(text)


def role_items(guild, lock=None):
    me_top = guild.me.top_role
    items = []
    for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
        if role.is_default():
            continue
        item = {"id": role.id, "name": role.name, "color": role.color.value}
        if lock == "assign" and (role.managed or role >= me_top):
            item["locked"] = True
        elif lock == "managed" and role.managed:
            item["locked"] = True
        elif lock == "panel" and (role.managed or role >= me_top or dangerous_role(role)):
            item["locked"] = True
        items.append(item)
    return items


def channel_items(guild):
    return [{"id": c.id, "name": f"#{c.name}"} for c in guild.text_channels]


def category_items(guild):
    return [{"id": c.id, "name": c.name} for c in guild.categories]


def free_ids(items):
    return {i["id"] for i in items if not i.get("locked")}


def pick_ids(values, valid):
    out = []
    for value in values:
        text = str(value)
        if text.isdigit() and int(text) in valid and int(text) not in out:
            out.append(int(text))
    return out


def pick_one(value, valid):
    text = str(value or "")
    return int(text) if text.isdigit() and int(text) in valid else None


def clamp(value, low, high, default):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, number))


async def set_or_del(db, gid, key, value):
    if value is None or value == "":
        await db.del_setting(gid, key)
    else:
        await db.set_setting(gid, key, value)


# --------------------------------------------------------------------------- middleware
@web.middleware
async def middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException:
        raise
    except Exception:
        log.exception("Ошибка на странице %s", request.path)
        response = html_response(
            webui.layout("Ошибка", webui.error_page("Внутренняя ошибка. Подробности записаны в логи бота.")), 500
        )
    response.headers.update(SECURITY_HEADERS)
    return response


# --------------------------------------------------------------------------- вход и выход
def avatar_url(user):
    if user.get("avatar"):
        return f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=64"
    return f"https://cdn.discordapp.com/embed/avatars/{(int(user['id']) >> 22) % 6}.png"


def client_id(bot):
    return config.CLIENT_ID or str(bot.user.id)


async def health(request):
    return web.Response(text="ok")


async def index(request):
    bot = request.app["bot"]
    sess = current_session(request)
    if sess is None:
        body = webui.login_page(bool(config.CLIENT_SECRET))
        return html_response(
            webui.layout("Вход", body, ok=request.query.get("ok"), err=request.query.get("err"))
        )
    guilds = []
    for gid in sess["guilds"]:
        guild = bot.get_guild(gid)
        if guild and await access_level(bot, sess, guild):
            guilds.append({
                "id": gid, "name": guild.name, "members": guild.member_count,
                "icon": guild.icon.url if guild.icon else None,
            })
    invite = (
        "https://discord.com/oauth2/authorize?"
        + urlencode({"client_id": client_id(bot), "scope": "bot applications.commands", "permissions": INVITE_PERMISSIONS})
    )
    return render(request, sess, "Серверы", webui.guilds_page(guilds, invite))


async def login(request):
    if not config.CLIENT_SECRET:
        raise web.HTTPFound("/?err=nosecret")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": client_id(request.app["bot"]),
        "redirect_uri": base_url(request) + "/callback",
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
        "prompt": "none",
    }
    response = web.HTTPFound("https://discord.com/oauth2/authorize?" + urlencode(params))
    response.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True, samesite="Lax", secure=is_https(request))
    raise response


async def callback(request):
    bot = request.app["bot"]
    if request.query.get("error"):
        raise web.HTTPFound("/?err=denied")
    code = request.query.get("code")
    state = request.query.get("state")
    expected = request.cookies.get(STATE_COOKIE)
    if not code or not state or not expected or not secrets.compare_digest(state, expected):
        raise web.HTTPFound("/?err=state")

    async with ClientSession(timeout=ClientTimeout(total=15), headers={"User-Agent": USER_AGENT}) as http:
        async with http.post(f"{API}/oauth2/token", data={
            "client_id": client_id(bot),
            "client_secret": config.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": base_url(request) + "/callback",
        }) as resp:
            if resp.status != 200:
                log.warning("OAuth: обмен кода не удался (%s): %s", resp.status, (await resp.text())[:200])
                raise web.HTTPFound("/?err=oauth")
            token = (await resp.json())["access_token"]
        auth = {"Authorization": f"Bearer {token}"}
        async with http.get(f"{API}/users/@me", headers=auth) as resp:
            if resp.status != 200:
                raise web.HTTPFound("/?err=oauth")
            user = await resp.json()
        async with http.get(f"{API}/users/@me/guilds", headers=auth) as resp:
            if resp.status != 200:
                raise web.HTTPFound("/?err=oauth")
            guilds = await resp.json()

    all_guilds, admin_ids = {}, set()
    for item in guilds:
        gid = int(item["id"])
        all_guilds[gid] = {"name": item["name"]}
        if item.get("owner") or int(item.get("permissions") or 0) & ADMINISTRATOR:
            admin_ids.add(gid)

    # Вход прошёл: Discord принял адрес возврата, значит этому адресу можно доверять. Запоминаем для /dashboard.
    await bot.remember_public_url(base_url(request))

    store = request.app["sessions"]
    now = time.time()
    for old in [t for t, s in store.items() if s["exp"] < now]:
        del store[old]
    session_token = secrets.token_urlsafe(32)
    store[session_token] = {
        "uid": int(user["id"]),
        "name": user.get("global_name") or user["username"],
        "avatar": avatar_url(user),
        "guilds": all_guilds,
        "admin": admin_ids,
        "csrf": secrets.token_urlsafe(24),
        "exp": now + SESSION_TTL,
    }
    response = web.HTTPFound("/")
    response.set_cookie(COOKIE, session_token, max_age=SESSION_TTL, httponly=True, samesite="Lax", secure=is_https(request))
    response.del_cookie(STATE_COOKIE)
    raise response


async def logout(request):
    sess = current_session(request)
    data = await request.post()
    if sess is not None:
        check_csrf(sess, data)
        request.app["sessions"].pop(request.cookies.get(COOKIE), None)
    response = web.HTTPSeeOther("/")
    response.del_cookie(COOKIE)
    raise response


# --------------------------------------------------------------------------- обзор
async def overview(request):
    sess, guild, level = await authorize(request, staff_ok=True)
    db = request.app["bot"].db
    gid = guild.id

    open_tickets = (await db.fetchone(
        "SELECT COUNT(*) AS c FROM tickets WHERE guild_id=? AND status='open'", (gid,)))["c"]
    active_events = (await db.fetchone(
        "SELECT COUNT(*) AS c FROM wipe_events WHERE guild_id=? AND closed=0 AND ts>?", (gid, int(time.time()))))["c"]
    automod_on = await db.get_setting(gid, "automod_enabled", "1") != "0"

    recent = []
    for row in await db.fetchall(
        "SELECT user_id, channel_id, link, ts FROM automod_log WHERE guild_id=? ORDER BY id DESC LIMIT 8", (gid,)
    ):
        member = guild.get_member(row["user_id"])
        channel = guild.get_channel(row["channel_id"])
        recent.append({
            "when": webui.fmt_ts(row["ts"], config.TIMEZONE),
            "user": member.display_name if member else str(row["user_id"]),
            "channel": f"#{channel.name}" if channel else "—",
            "link": row["link"][:80],
        })

    me = guild.me
    perms = me.guild_permissions
    above = sum(1 for r in guild.roles if not r.is_default() and r > me.top_role)
    health = [
        (perms.manage_roles, "Право «Управлять ролями» (для /role и авто-ролей)"),
        (perms.manage_channels, "Право «Управлять каналами» (для тикетов)"),
        (perms.manage_messages, "Право «Управлять сообщениями» (для автомодерации)"),
        (perms.moderate_members, "Право «Отправлять участников подумать» (тайм-ауты автомодерации)"),
        (bool(await db.get_setting(gid, "mod_log")), "Задан лог-канал модерации (раздел «Общие»)"),
        (bool(await db.get_setting(gid, "ticket_category")), "Настроена категория тикетов (раздел «Тикеты»)"),
        (None, f"Выше роли VEX стоит ролей: {above}. Их бот выдать не сможет — при необходимости подними роль VEX."),
    ]
    stats = {"open_tickets": open_tickets, "active_events": active_events, "automod_on": automod_on,
             "members": guild.member_count}
    return render(request, sess, "Обзор", webui.overview_page(gid, stats, health, recent, level), guild, "", level)


# --------------------------------------------------------------------------- доступ к командам
async def access_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    selected = {}
    for key in config.COMMAND_KEYS:
        selected[key] = await db.get_targets(guild.id, f"cmd:{key}")
    body = webui.access_page(guild.id, role_items(guild), selected, config.COMMAND_KEYS)
    return render(request, sess, "Доступ к командам", body, guild, "access")


async def access_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    valid = {r["id"] for r in role_items(guild)}
    for key in config.COMMAND_KEYS:
        await db.set_targets(guild.id, f"cmd:{key}", pick_ids(data.getall(f"cmd_{key}", []), valid))
    raise back(guild.id, "access", ok="saved")


# --------------------------------------------------------------------------- роли
async def roles_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    body = webui.roles_page(
        guild.id, role_items(guild, "assign"), role_items(guild, "managed"),
        await db.get_targets(guild.id, "autorole_member"),
        await db.get_targets(guild.id, "autorole_bot"),
        await db.get_targets(guild.id, "manageable"),
    )
    return render(request, sess, "Роли", body, guild, "roles")


async def roles_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    assignable = free_ids(role_items(guild, "assign"))
    manageable = free_ids(role_items(guild, "managed"))
    await db.set_targets(guild.id, "autorole_member", pick_ids(data.getall("autorole_member", []), assignable))
    await db.set_targets(guild.id, "autorole_bot", pick_ids(data.getall("autorole_bot", []), assignable))
    await db.set_targets(guild.id, "manageable", pick_ids(data.getall("manageable", []), manageable))
    raise back(guild.id, "roles", ok="saved")


# --------------------------------------------------------------------------- автомодерация
async def automod_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    gid = guild.id
    domains = [r["domain"] for r in await db.fetchall(
        "SELECT domain FROM allowed_domains WHERE guild_id=? ORDER BY domain", (gid,))]
    state = {
        "enabled": await db.get_setting(gid, "automod_enabled", "1") != "0",
        "strikes": clamp(await db.get_setting(gid, "automod_strikes", "3"), 1, 10, 3),
        "timeout": clamp(await db.get_setting(gid, "automod_timeout", "10"), 0, 1440, 10),
        "domains_text": "\n".join(domains),
        "bypass": await db.get_targets(gid, "automod_bypass"),
        "ignore": await db.get_targets(gid, "automod_ignore_channel"),
    }
    body = webui.automod_page(gid, state, role_items(guild), channel_items(guild), config.DEFAULT_ALLOWED_DOMAINS)
    return render(request, sess, "Автомодерация", body, guild, "automod")


async def automod_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    gid = guild.id
    await db.set_setting(gid, "automod_enabled", "1" if data.get("enabled") else "0")
    await db.set_setting(gid, "automod_strikes", clamp(data.get("strikes"), 1, 10, 3))
    await db.set_setting(gid, "automod_timeout", clamp(data.get("timeout"), 0, 1440, 10))

    domains = []
    for item in re.split(r"[\s,;]+", str(data.get("domains", ""))):
        domain = normalize_domain(item) if item else ""
        if domain and "." in domain and len(domain) <= 100 and re.fullmatch(r"[a-z0-9.\-]+", domain) \
                and domain not in domains:
            domains.append(domain)
    await db.set_domains(gid, domains[:200])

    await db.set_targets(gid, "automod_bypass",
                         pick_ids(data.getall("bypass", []), {r["id"] for r in role_items(guild)}))
    await db.set_targets(gid, "automod_ignore_channel",
                         pick_ids(data.getall("ignore", []), {c.id for c in guild.text_channels}))
    raise back(gid, "automod", ok="saved")


# --------------------------------------------------------------------------- тикеты
async def tickets_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    gid = guild.id

    def as_int(value):
        return int(value) if value and str(value).isdigit() else None

    types = await db.get_ticket_types(gid)
    labels = {t["key"]: t["label"] for t in types}
    state = {
        "category": as_int(await db.get_setting(gid, "ticket_category")),
        "log_channel": as_int(await db.get_setting(gid, "ticket_log")),
        "max_open": clamp(await db.get_setting(gid, "ticket_max_open", "1"), 1, 5, 1),
        "support": await db.get_targets(gid, "ticket_support"),
        "types_text": webui.types_to_text(types),
        "archive": as_int(await db.get_setting(gid, "ticket_archive")),
        "autoclose": clamp(await db.get_setting(gid, "ticket_autoclose", "0"), 0, 720, 0),
        "delete_on_close": (await db.get_setting(gid, "ticket_delete_on_close", "1")) == "1",
    }
    open_tickets = []
    for row in await db.fetchall(
        "SELECT id, user_id, type, claimed_by, created_at, channel_id, priority FROM tickets "
        "WHERE guild_id=? AND status='open' ORDER BY id DESC LIMIT 50", (gid,)
    ):
        member = guild.get_member(row["user_id"])
        channel = guild.get_channel(row["channel_id"])
        claimer = guild.get_member(row["claimed_by"]) if row["claimed_by"] else None
        open_tickets.append({
            "id": row["id"],
            "user": member.display_name if member else str(row["user_id"]),
            "type": labels.get(row["type"], "Обращение"),
            "status": f"В работе — {claimer.display_name}" if claimer else "Ожидает ответа",
            "created": webui.fmt_ts(row["created_at"], config.TIMEZONE),
            "channel": channel.name if channel else "удалён",
            "priority": config.PRIORITY_LABELS.get(row["priority"] or "normal", ""),
        })
    body = webui.tickets_page(gid, state, category_items(guild), channel_items(guild), role_items(guild), open_tickets)
    return render(request, sess, "Тикеты", body, guild, "tickets")


async def tickets_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    gid = guild.id

    existing = {t["label"].lower(): (t["key"], t["slug"])
                for t in await db.get_ticket_types(gid)}
    types, error = webui.parse_types_text(data.get("types", ""), existing)
    if error:
        raise back(gid, "tickets", err=error)

    await db.set_ticket_types(gid, types)
    await set_or_del(db, gid, "ticket_archive", pick_one(data.get("archive"), {c.id for c in guild.categories}))
    await db.set_setting(gid, "ticket_autoclose", clamp(data.get("autoclose"), 0, 720, 0))
    await db.set_setting(gid, "ticket_delete_on_close", 0 if data.get("delete_on_close") == "0" else 1)
    await set_or_del(db, gid, "ticket_category", pick_one(data.get("category"), {c.id for c in guild.categories}))
    await set_or_del(db, gid, "ticket_log", pick_one(data.get("log_channel"), {c.id for c in guild.text_channels}))
    await db.set_setting(gid, "ticket_max_open", clamp(data.get("max_open"), 1, 5, 1))
    await db.set_targets(gid, "ticket_support",
                         pick_ids(data.getall("support", []), {r["id"] for r in role_items(guild)}))
    raise back(gid, "tickets", ok="saved")


async def tickets_panel(request):
    sess, guild, data, level = await post_context(request)
    channels = {c.id: c for c in guild.text_channels}
    channel_id = pick_one(data.get("channel"), set(channels))
    if channel_id is None:
        raise back(guild.id, "tickets", err="channel")
    channel = channels[channel_id]
    perms = channel.permissions_for(guild.me)
    if not (perms.send_messages and perms.embed_links):
        raise back(guild.id, "tickets", err="noperm")
    cog = request.app["bot"].get_cog("Tickets")
    if cog is None:
        raise back(guild.id, "tickets", err="nocog")
    title = str(data.get("title", "")).strip()[:200] or None
    description = str(data.get("description", "")).strip()[:2000] or None
    try:
        await cog.send_panel(channel, title, description)
    except discord.HTTPException:
        raise back(guild.id, "tickets", err="noperm")
    raise back(guild.id, "tickets", ok="sent")


# --------------------------------------------------------------------------- события
async def events_get(request):
    sess, guild, level = await authorize(request, staff_ok=True)
    db = request.app["bot"].db
    gid = guild.id
    events = []
    for ev in await db.fetchall("SELECT * FROM wipe_events WHERE guild_id=? ORDER BY ts DESC LIMIT 25", (gid,)):
        counts = {"accepted": 0, "declined": 0, "late": 0}
        for row in await db.fetchall(
            "SELECT status, COUNT(*) AS c FROM wipe_responses WHERE message_id=? GROUP BY status", (ev["message_id"],)
        ):
            if row["status"] in counts:
                counts[row["status"]] = row["c"]
        channel = guild.get_channel(ev["channel_id"])
        events.append({
            "message_id": ev["message_id"],
            "title": ev["title"],
            "when": webui.fmt_ts(ev["ts"], config.TIMEZONE),
            "closed": bool(ev["closed"]),
            "channel": channel.name if channel else "удалён",
            "url": f"https://discord.com/channels/{gid}/{ev['channel_id']}/{ev['message_id']}",
            **counts,
        })
    return render(request, sess, "События", webui.events_page(gid, events), guild, "events", level)


async def event_action(request):
    sess, guild, data, level = await post_context(request, staff_ok=True)
    db = request.app["bot"].db
    message_id = request.match_info["mid"]
    action = request.match_info["action"]
    if not message_id.isdigit() or action not in ("toggle", "delete", "remind"):
        raise web.HTTPNotFound()
    ev = await db.fetchone(
        "SELECT * FROM wipe_events WHERE message_id=? AND guild_id=?", (int(message_id), guild.id)
    )
    if ev is None:
        raise back(guild.id, "events", err="noevent")
    cog = request.app["bot"].get_cog("Wipe")
    if cog is None:
        raise back(guild.id, "events", err="nocog")
    if action == "toggle":
        await cog.set_closed(ev["message_id"], not ev["closed"])
        raise back(guild.id, "events", ok="saved")
    if action == "delete":
        await cog.delete_event(ev["message_id"])
        raise back(guild.id, "events", ok="deleted")
    count = await cog.remind_pending(ev["message_id"])
    raise back(guild.id, "events", ok="reminded" if count else "noone")


# --------------------------------------------------------------------------- модерация
async def moderation_get(request):
    sess, guild, level = await authorize(request, staff_ok=True)
    db = request.app["bot"].db
    gid = guild.id

    def name(user_id):
        member = guild.get_member(user_id)
        return member.display_name if member else f"ID {user_id}"

    cases = []
    for row in await db.fetchall("SELECT * FROM mod_cases WHERE guild_id=? ORDER BY id DESC LIMIT 50", (gid,)):
        cases.append({
            "no": row["case_no"],
            "when": webui.fmt_ts(row["created_at"], config.TIMEZONE),
            "action": row["action"],
            "label": ACTION_LABELS.get(row["action"], row["action"]),
            "icon": ACTION_ICONS.get(row["action"], "📌"),
            "user": name(row["user_id"]),
            "mod": name(row["mod_id"]),
            "reason": (row["reason"] or "—")[:200],
            "active": bool(row["active"]),
            "expires": webui.fmt_ts(row["expires_at"], config.TIMEZONE) if row["expires_at"] else None,
        })
    state = {
        "warn_threshold": clamp(await db.get_setting(gid, "warn_threshold", "3"), 0, 20, 3),
        "warn_timeout": clamp(await db.get_setting(gid, "warn_timeout", "60"), 1, 40320, 60),
    }
    body = webui.moderation_page(gid, state, cases, level == "admin")
    return render(request, sess, "Модерация", body, guild, "moderation", level)


async def moderation_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    await db.set_setting(guild.id, "warn_threshold", clamp(data.get("warn_threshold"), 0, 20, 3))
    await db.set_setting(guild.id, "warn_timeout", clamp(data.get("warn_timeout"), 1, 40320, 60))
    raise back(guild.id, "moderation", ok="saved")


async def moderation_revoke(request):
    sess, guild, data, level = await post_context(request, staff_ok=True)
    number = request.match_info["no"]
    if not number.isdigit():
        raise web.HTTPNotFound()
    changed = await request.app["bot"].db.execute(
        "UPDATE mod_cases SET active=0 WHERE guild_id=? AND case_no=? AND action='warn' AND active=1",
        (guild.id, int(number)),
    )
    if not changed:
        raise back(guild.id, "moderation", err="nocase")
    raise back(guild.id, "moderation", ok="saved")


# --------------------------------------------------------------------------- панели ролей
def parse_panel(guild, data):
    """Проверяет форму панели. Возвращает (значения, None) или (None, код ошибки)."""
    title = str(data.get("title", "")).strip()[:200]
    if not title:
        return None, "panel_title"
    channels = {c.id: c for c in guild.text_channels}
    channel_id = pick_one(data.get("channel"), set(channels))
    if channel_id is None:
        return None, "channel"
    role_ids = pick_ids(data.getall("roles", []), free_ids(role_items(guild, "panel")))[:25]
    if not role_ids:
        return None, "panel_roles"
    perms = channels[channel_id].permissions_for(guild.me)
    if not (perms.send_messages and perms.embed_links):
        return None, "noperm"
    return {
        "title": title,
        "description": str(data.get("description", "")).strip()[:1500],
        "channel_id": channel_id,
        "exclusive": 1 if data.get("exclusive") else 0,
        "role_ids": role_ids,
    }, None


async def panels_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    panels = []
    for row in await db.fetchall("SELECT * FROM role_panels WHERE guild_id=? ORDER BY id", (guild.id,)):
        ids = [r["role_id"] for r in await db.fetchall(
            "SELECT role_id FROM role_panel_roles WHERE panel_id=? ORDER BY position", (row["id"],))]
        channel = guild.get_channel(row["channel_id"])
        panels.append({
            "id": row["id"], "title": row["title"], "description": row["description"],
            "channel_id": row["channel_id"], "channel": channel.name if channel else "удалён",
            "exclusive": bool(row["exclusive"]), "role_ids": ids,
        })
    body = webui.panels_page(guild.id, panels, channel_items(guild), role_items(guild, "panel"))
    return render(request, sess, "Панели ролей", body, guild, "panels")


async def panels_new(request):
    sess, guild, data, level = await post_context(request)
    bot = request.app["bot"]
    values, error = parse_panel(guild, data)
    if error:
        raise back(guild.id, "panels", err=error)
    cog = bot.get_cog("RolePanels")
    if cog is None:
        raise back(guild.id, "panels", err="nocog")
    panel_id = await bot.db.insert(
        "INSERT INTO role_panels(guild_id, channel_id, title, description, exclusive) VALUES(?,?,?,?,?)",
        (guild.id, values["channel_id"], values["title"], values["description"], values["exclusive"]),
    )
    await bot.db.set_panel_roles(panel_id, values["role_ids"])
    try:
        await cog.publish(panel_id)
    except discord.HTTPException:
        await cog.delete_panel(panel_id)
        raise back(guild.id, "panels", err="noperm")
    raise back(guild.id, "panels", ok="sent")


async def load_panel(request, guild):
    pid = request.match_info["pid"]
    if not pid.isdigit():
        raise web.HTTPNotFound()
    panel = await request.app["bot"].db.fetchone(
        "SELECT * FROM role_panels WHERE id=? AND guild_id=?", (int(pid), guild.id))
    if panel is None:
        raise back(guild.id, "panels", err="nopanel")
    return panel


async def panels_edit(request):
    sess, guild, data, level = await post_context(request)
    bot = request.app["bot"]
    panel = await load_panel(request, guild)
    values, error = parse_panel(guild, data)
    if error:
        raise back(guild.id, "panels", err=error)
    cog = bot.get_cog("RolePanels")
    if cog is None:
        raise back(guild.id, "panels", err="nocog")
    message_id = panel["message_id"]
    if values["channel_id"] != panel["channel_id"]:  # переехала в другой канал — старое сообщение убираем
        await cog.remove_message(panel)
        message_id = 0
    await bot.db.execute(
        "UPDATE role_panels SET channel_id=?, message_id=?, title=?, description=?, exclusive=? WHERE id=?",
        (values["channel_id"], message_id, values["title"], values["description"], values["exclusive"], panel["id"]),
    )
    await bot.db.set_panel_roles(panel["id"], values["role_ids"])
    try:
        await cog.publish(panel["id"])
    except discord.HTTPException:
        raise back(guild.id, "panels", err="noperm")
    raise back(guild.id, "panels", ok="saved")


async def panels_action(request):
    sess, guild, data, level = await post_context(request)
    bot = request.app["bot"]
    panel = await load_panel(request, guild)
    action = request.match_info["action"]
    cog = bot.get_cog("RolePanels")
    if cog is None:
        raise back(guild.id, "panels", err="nocog")
    if action == "delete":
        await cog.delete_panel(panel["id"])
        raise back(guild.id, "panels", ok="deleted")
    if action == "resend":
        try:
            await cog.publish(panel["id"])
        except discord.HTTPException:
            raise back(guild.id, "panels", err="noperm")
        raise back(guild.id, "panels", ok="saved")
    raise web.HTTPNotFound()


# --------------------------------------------------------------------------- логи
async def logs_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    cats = []
    for key, (label, desc, default_on) in LOG_CATEGORIES.items():
        channel = await db.get_setting(guild.id, f"log_ch_{key}")
        cats.append({
            "key": key, "label": label, "desc": desc,
            "enabled": await db.get_setting(guild.id, f"log_on_{key}", "1" if default_on else "0") != "0",
            "channel_id": int(channel) if channel and channel.isdigit() else None,
        })
    return render(request, sess, "Логи", webui.logs_page(guild.id, cats, channel_items(guild)), guild, "logs")


async def logs_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    valid = {c.id for c in guild.text_channels}
    for key in LOG_CATEGORIES:
        await db.set_setting(guild.id, f"log_on_{key}", "1" if data.get(f"on_{key}") else "0")
        await set_or_del(db, guild.id, f"log_ch_{key}", pick_one(data.get(f"ch_{key}"), valid))
    raise back(guild.id, "logs", ok="saved")


# --------------------------------------------------------------------------- общие
async def general_get(request):
    sess, guild, level = await authorize(request)
    db = request.app["bot"].db
    gid = guild.id

    def as_int(value):
        return int(value) if value and str(value).isdigit() else None

    state = {
        "mod_log": as_int(await db.get_setting(gid, "mod_log")),
        "welcome_channel": as_int(await db.get_setting(gid, "welcome_channel")),
        "welcome_text": await db.get_setting(gid, "welcome_text", ""),
        "welcome_default": DEFAULT_WELCOME.replace("\n", " "),
    }
    body = webui.general_page(gid, state, channel_items(guild), config.TIMEZONE)
    return render(request, sess, "Общие настройки", body, guild, "general")


async def general_post(request):
    sess, guild, data, level = await post_context(request)
    db = request.app["bot"].db
    gid = guild.id
    valid = {c.id for c in guild.text_channels}
    await set_or_del(db, gid, "mod_log", pick_one(data.get("mod_log"), valid))
    await set_or_del(db, gid, "welcome_channel", pick_one(data.get("welcome_channel"), valid))
    text = str(data.get("welcome_text", "")).replace("\r\n", "\n").strip()[:1500]
    await set_or_del(db, gid, "welcome_text", text)
    raise back(gid, "general", ok="saved")


# --------------------------------------------------------------------------- запуск
def build_app(bot):
    app = web.Application(middlewares=[middleware])
    app["bot"] = bot
    app["sessions"] = {}
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/login", login)
    app.router.add_get("/callback", callback)
    app.router.add_post("/logout", logout)
    app.router.add_get("/g/{gid}", overview)
    for section, getter, poster in (
        ("access", access_get, access_post),
        ("roles", roles_get, roles_post),
        ("automod", automod_get, automod_post),
        ("tickets", tickets_get, tickets_post),
        ("moderation", moderation_get, moderation_post),
        ("logs", logs_get, logs_post),
        ("general", general_get, general_post),
    ):
        app.router.add_get(f"/g/{{gid}}/{section}", getter)
        app.router.add_post(f"/g/{{gid}}/{section}", poster)
    app.router.add_post("/g/{gid}/tickets/panel", tickets_panel)
    app.router.add_post("/g/{gid}/moderation/{no}/revoke", moderation_revoke)
    app.router.add_get("/g/{gid}/panels", panels_get)
    app.router.add_post("/g/{gid}/panels/new", panels_new)
    app.router.add_post("/g/{gid}/panels/{pid}/{action}", panels_action)
    app.router.add_post("/g/{gid}/panels/{pid}", panels_edit)
    app.router.add_get("/g/{gid}/events", events_get)
    app.router.add_post("/g/{gid}/events/{mid}/{action}", event_action)
    return app


async def start_web(bot):
    """Запускает сайт. Возвращает runner (для остановки) или None, если сайт выключен."""
    if not config.WEB_PORT:
        log.info("Сайт выключен: хостинг не передал порт (PORT). Включи опцию «Использовать домен».")
        return None
    try:
        runner = web.AppRunner(build_app(bot))
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", config.WEB_PORT).start()
    except OSError:
        log.exception("Не удалось запустить сайт на порту %s", config.WEB_PORT)
        return None
    log.info("Сайт запущен на порту %s%s", config.WEB_PORT,
             "" if config.CLIENT_SECRET else " (вход не настроен: нет DISCORD_CLIENT_SECRET)")
    return runner
''',
    'vex.cogs': r'''''',
    'vex.cogs.tickets': r'''"""Тикеты: панель с меню, приватные каналы, приоритеты, заметки, транскрипты и оценки."""
import asyncio
import html as html_mod
import io
import logging
import re
import unicodedata
from datetime import datetime
from time import time as now_ts
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import config, embeds
from ..checks import access, member_has_access

log = logging.getLogger("vex")
TZ = ZoneInfo(config.TIMEZONE)

# Приоритет задаёт цвет эмбеда и префикс имени канала.
PRIORITIES = {
    "low": ("🟢 Низкий", config.COLOR_OK),
    "normal": ("🔵 Обычный", config.COLOR_MAIN),
    "high": ("🟠 Высокий", config.COLOR_WARN),
    "urgent": ("🔴 Срочный", config.COLOR_ERR),
}
PRIORITY_CHOICES = [
    app_commands.Choice(name=label, value=key) for key, (label, _) in PRIORITIES.items()
]
FALLBACK_TYPE = {"key": "other", "slug": "ticket", "label": "Обращение", "emoji": "🎫",
                 "description": ""}
PAGE_SIZE = 15


# --------------------------------------------------------------------------- утилиты
def slugify(text):
    """'Вступление в клан' -> 'vstuplenie-v-klan' (имена каналов Discord любят латиницу)."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
        "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
        "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
        "я": "ya",
    }
    out = "".join(table.get(ch, ch) for ch in text.lower())
    out = unicodedata.normalize("NFKD", out).encode("ascii", "ignore").decode()
    out = re.sub(r"[^a-z0-9]+", "-", out).strip("-")
    return out[:20] or "ticket"


def safe_emoji(value):
    """Эмодзи из базы может оказаться мусором — тогда просто не показываем его."""
    if not value:
        return None
    try:
        return discord.PartialEmoji.from_str(value)
    except Exception:
        return None


def fmt_ts(epoch):
    """Unix-время -> '25.11.2026 19:30' в часовом поясе бота."""
    try:
        return datetime.fromtimestamp(int(epoch), TZ).strftime("%d.%m.%Y %H:%M")
    except (TypeError, ValueError, OSError):
        return "—"


def fmt_duration(seconds):
    """3725 -> '1 ч 2 мин'."""
    if not seconds:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} сек"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days} д {hours} ч"
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def priority_of(row):
    try:
        value = row["priority"] or "normal"
    except (IndexError, KeyError):
        value = "normal"
    return value if value in PRIORITIES else "normal"


def channel_name_for(slug, ticket_id, priority):
    return f"{config.PRIORITY_CHANNEL_PREFIX.get(priority, '')}{slug}-{ticket_id:04d}"


# --------------------------------------------------------------------------- эмбеды
def panel_embed(types, title=None, description=None):
    if description:
        text = description
    else:
        listing = "\n".join(f"{t['emoji']} **{t['label']}** — {t['description']}" for t in types)
        text = (
            "Нужна помощь или хочешь вступить в клан?\n"
            "Выбери тип обращения в меню ниже — для тебя создастся приватный канал, "
            "где с тобой свяжется администрация.\n\n" + listing
        )
    embed = embeds.make(title or "🎫 Центр поддержки", text)
    if not description:
        embed.add_field(
            name="ℹ️ Правила",
            value="• Один открытый тикет на человека\n• Пиши по делу и не спамь\n"
                  "• Не пингуй администрацию без причины",
            inline=False,
        )
    return embed


def ticket_embed(guild, row, type_info):
    priority = priority_of(row)
    label, color = PRIORITIES[priority]
    embed = embeds.make(
        f"{type_info['emoji']} Тикет #{row['id']:04d} — {type_info['label']}", color=color
    )
    embed.description = f">>> {row['reason']}"[:4000]
    embed.add_field(name="👤 Автор", value=f"<@{row['user_id']}>", inline=True)

    if row["status"] != "open":
        status = "⚫ Закрыт"
    elif row["locked"]:
        status = "🔇 Заблокирован — автор не может писать"
    elif row["claimed_by"]:
        status = f"🟡 В работе — <@{row['claimed_by']}>"
    else:
        status = "🟢 Ожидает ответа"
    embed.add_field(name="📌 Статус", value=status, inline=True)
    embed.add_field(name="🚦 Приоритет", value=label, inline=True)
    embed.add_field(name="🕒 Создан", value=f"<t:{row['created_at']}:R>", inline=True)
    member = guild.get_member(row["user_id"])
    if member:
        embed.set_thumbnail(url=member.display_avatar.url)
    return embed


# --------------------------------------------------------------------------- интерфейс
class TicketReasonModal(discord.ui.Modal):
    def __init__(self, cog, type_info):
        super().__init__(title=type_info["label"][:45])
        self.cog = cog
        self.type_info = type_info
        self.reason = discord.ui.TextInput(
            label="Опишите ваш вопрос",
            style=discord.TextStyle.paragraph,
            placeholder="Расскажи подробно: что нужно, ник в игре, возраст, часы в Rust и т.д.",
            max_length=1000,
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction):
        await self.cog.create_ticket(interaction, self.type_info, str(self.reason))


class TicketSelect(discord.ui.Select):
    def __init__(self, types=None):
        types = types or config.TICKET_TYPES
        options = []
        for t in types[:25]:
            description = (t.get("description") or "")[:100] or None
            options.append(discord.SelectOption(
                label=t["label"][:100], value=t["key"],
                description=description, emoji=safe_emoji(t["emoji"]),
            ))
        super().__init__(
            placeholder="Выберите тип обращения…",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="vex:ticket:select",
        )

    async def callback(self, interaction):
        cog = interaction.client.get_cog("Tickets")
        types = await cog.bot.db.get_ticket_types(interaction.guild.id)
        chosen = next((t for t in types if t["key"] == self.values[0]), None)
        if chosen is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот тип обращения больше не доступен — обнови панель."),
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(TicketReasonModal(cog, chosen))
        # сбрасываем выбор в меню, чтобы им можно было пользоваться снова
        try:
            await interaction.message.edit(view=TicketPanelView(types))
        except discord.HTTPException:
            pass


class TicketPanelView(discord.ui.View):
    def __init__(self, types=None):
        super().__init__(timeout=None)
        self.add_item(TicketSelect(types))


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть", emoji="🔒", style=discord.ButtonStyle.danger,
                       custom_id="vex:ticket:close")
    async def close_button(self, interaction, button):
        await interaction.client.get_cog("Tickets").on_close_button(interaction)

    @discord.ui.button(label="Взять в работу", emoji="✋", style=discord.ButtonStyle.success,
                       custom_id="vex:ticket:claim")
    async def claim_button(self, interaction, button):
        await interaction.client.get_cog("Tickets").on_claim_button(interaction)

    @discord.ui.button(label="Транскрипт", emoji="📄", style=discord.ButtonStyle.secondary,
                       custom_id="vex:ticket:transcript")
    async def transcript_button(self, interaction, button):
        await interaction.client.get_cog("Tickets").on_transcript_button(interaction)

    @discord.ui.button(label="Заблокировать", emoji="🔇", style=discord.ButtonStyle.secondary,
                       custom_id="vex:ticket:lock")
    async def lock_button(self, interaction, button):
        await interaction.client.get_cog("Tickets").on_lock_button(interaction)


class ConfirmCloseView(discord.ui.View):
    def __init__(self, cog, channel):
        super().__init__(timeout=60)
        self.cog = cog
        self.channel = channel

    @discord.ui.button(label="Да, закрыть", emoji="🔒", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        await interaction.response.edit_message(embed=embeds.warn("Закрываю тикет…"), view=None)
        await self.cog.close_ticket(self.channel, interaction.user)

    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(embed=embeds.info("Отменено."), view=None)


class RateCommentModal(discord.ui.Modal):
    def __init__(self, cog, ticket_id, score):
        super().__init__(title="Спасибо за оценку!")
        self.cog = cog
        self.ticket_id = ticket_id
        self.score = score
        self.comment = discord.ui.TextInput(
            label="Комментарий (необязательно)",
            style=discord.TextStyle.paragraph,
            placeholder="Что понравилось, а что можно сделать лучше?",
            required=False,
            max_length=500,
        )
        self.add_item(self.comment)

    async def on_submit(self, interaction):
        await self.cog.save_rating_comment(interaction, self.ticket_id, self.score,
                                           str(self.comment).strip())


class RateButton(discord.ui.DynamicItem[discord.ui.Button],
                 template=r"vex:rate:(?P<ticket>[0-9]+):(?P<score>[1-5])"):
    """Кнопка оценки в ЛС. Работает и после перезапуска бота — id разбирается из custom_id."""

    def __init__(self, ticket_id, score):
        self.ticket_id = ticket_id
        self.score = score
        super().__init__(
            discord.ui.Button(
                label=str(score),
                emoji="⭐",
                style=discord.ButtonStyle.secondary,
                custom_id=f"vex:rate:{ticket_id}:{score}",
            )
        )

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["ticket"]), int(match["score"]))

    async def callback(self, interaction):
        cog = interaction.client.get_cog("Tickets")
        if cog is None:
            return
        await cog.on_rate(interaction, self.ticket_id, self.score)


def rating_view(ticket_id):
    view = discord.ui.View(timeout=None)
    for score in range(1, 6):
        view.add_item(RateButton(ticket_id, score))
    return view


class PageView(discord.ui.View):
    """Простая листалка эмбедов — для /ticket list, /roster и других списков."""

    def __init__(self, pages, author_id):
        super().__init__(timeout=180)
        self.pages = pages
        self.index = 0
        self.author_id = author_id
        self._sync()

    def _sync(self):
        self.prev.disabled = self.index == 0
        self.next.disabled = self.index >= len(self.pages) - 1

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=embeds.err("Это чужой список — вызови команду сам."), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction, button):
        self.index = max(0, self.index - 1)
        self._sync()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction, button):
        self.index = min(len(self.pages) - 1, self.index + 1)
        self._sync()
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)


def paginate(items, per_page, title, build_line, color=config.COLOR_MAIN):
    """Режет список строк на страницы-эмбеды."""
    pages = []
    total = (len(items) - 1) // per_page + 1 if items else 1
    for start in range(0, max(len(items), 1), per_page):
        chunk = items[start:start + per_page]
        body = "\n".join(build_line(item) for item in chunk) or "—"
        page = embeds.make(title, body, color=color)
        page.set_footer(text=f"{config.FOOTER} • страница {len(pages) + 1} из {total}")
        pages.append(page)
    return pages


# --------------------------------------------------------------------------- модуль
class Tickets(commands.Cog):
    ticket = app_commands.Group(name="ticket", description="Система тикетов", guild_only=True)
    support = app_commands.Group(name="support", description="Роли поддержки", parent=ticket)
    blacklist = app_commands.Group(name="blacklist", description="Кому запрещено открывать тикеты",
                                   parent=ticket)
    type_group = app_commands.Group(name="type", description="Типы обращений на панели",
                                    parent=ticket)

    def __init__(self, bot):
        self.bot = bot
        self._open_channels = set()  # кэш, чтобы не дёргать базу на каждое сообщение

    async def cog_load(self):
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())
        self.bot.add_dynamic_items(RateButton)
        rows = await self.bot.db.fetchall(
            "SELECT channel_id FROM tickets WHERE status='open' AND channel_id != 0"
        )
        self._open_channels = {r["channel_id"] for r in rows}
        try:
            config.TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            log.warning("Не удалось создать папку для транскриптов: %s", config.TRANSCRIPT_DIR)
        self.autoclose_loop.start()

    async def cog_unload(self):
        self.autoclose_loop.cancel()

    # ---- вспомогательное
    async def send_panel(self, channel, title=None, description=None):
        """Отправляет в канал панель с меню типов. Используется и командой, и сайтом."""
        types = await self.bot.db.get_ticket_types(channel.guild.id)
        return await channel.send(embed=panel_embed(types, title, description), view=TicketPanelView(types))

    async def get_ticket(self, channel_id):
        return await self.bot.db.fetchone(
            "SELECT * FROM tickets WHERE channel_id=? AND status='open'", (channel_id,)
        )

    async def type_info(self, guild_id, key):
        types = await self.bot.db.get_ticket_types(guild_id)
        for t in types:
            if t["key"] == key:
                return t
        return dict(FALLBACK_TYPE, key=key, label=key.capitalize())

    async def is_staff(self, member):
        if not isinstance(member, discord.Member):
            return False
        if member.guild_permissions.administrator:
            return True
        support = await self.bot.db.get_targets(member.guild.id, "ticket_support")
        if any(role.id in support for role in member.roles):
            return True
        return await member_has_access(self.bot, member, "ticket_manage")

    async def reload_row(self, ticket_id):
        return await self.bot.db.fetchone("SELECT * FROM tickets WHERE id=?", (ticket_id,))

    async def refresh_panel(self, channel, row):
        """Перерисовывает шапку тикета (первое сообщение бота в канале)."""
        try:
            info = await self.type_info(row["guild_id"], row["type"])
            async for message in channel.history(limit=5, oldest_first=True):
                if message.author.id == self.bot.user.id and message.embeds:
                    await message.edit(embed=ticket_embed(channel.guild, row, info),
                                       view=TicketControlView())
                    return
        except discord.HTTPException:
            pass

    async def resolve_ticket(self, interaction, ticket_id=None):
        """Тикет по номеру или тикет текущего канала (в любом статусе)."""
        db = self.bot.db
        if ticket_id:
            return await db.fetchone(
                "SELECT * FROM tickets WHERE id=? AND guild_id=?",
                (ticket_id, interaction.guild.id),
            )
        return await db.fetchone(
            "SELECT * FROM tickets WHERE channel_id=? ORDER BY id DESC LIMIT 1",
            (interaction.channel.id,),
        )

    # ---- транскрипты
    async def collect_messages(self, channel):
        result = []
        async for message in channel.history(limit=None, oldest_first=True):
            result.append(message)
        return result

    def render_txt(self, guild, row, info, messages, notes):
        lines = [
            f"Тикет #{row['id']:04d} • {guild.name}",
            f"Тип: {info['label']}",
            f"Автор: {row['user_id']}",
            f"Приоритет: {PRIORITIES[priority_of(row)][0]}",
            "-" * 48,
        ]
        for message in messages:
            stamp = message.created_at.astimezone(TZ).strftime("%d.%m.%Y %H:%M")
            text = message.content or ""
            for embed in message.embeds:
                if embed.title:
                    text += f" [embed: {embed.title}]"
            for attachment in message.attachments:
                text += f" [файл: {attachment.url}]"
            lines.append(f"[{stamp}] {message.author}: {text}")
        if notes:
            lines.append("-" * 48)
            lines.append("Внутренние заметки поддержки:")
            for note in notes:
                lines.append(f"[{fmt_ts(note['created_at'])}] {note['author_id']}: {note['text']}")
        return "\n".join(lines).encode("utf-8")

    def render_html(self, guild, row, info, messages, notes):
        """Тёмная тема, аватары, время в часовом поясе бота."""
        esc = html_mod.escape
        title = f"Тикет #{row['id']:04d} — {info['label']}"
        parts = [
            "<!doctype html>", '<html lang="ru">', "<head>", '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{esc(title)}</title>", "<style>",
            "body{margin:0;background:#0f0a1f;color:#ede9fe;"
            "font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-size:15px}",
            ".wrap{max-width:860px;margin:0 auto;padding:24px 16px 64px}",
            "header{border:1px solid rgba(139,92,246,.4);background:rgba(139,92,246,.12);"
            "border-radius:14px;padding:18px 22px;margin-bottom:24px}",
            "h1{margin:0 0 .4rem;font-size:1.5rem;color:#c4b5fd}",
            ".meta{color:#a78bfa;font-size:.9rem;line-height:1.6}",
            ".msg{display:flex;gap:12px;padding:10px 12px;border-radius:10px}",
            ".msg:hover{background:rgba(139,92,246,.07)}",
            ".av{width:40px;height:40px;border-radius:50%;flex:0 0 40px;background:#2e1065}",
            ".body{min-width:0;flex:1}",
            ".name{font-weight:600;color:#c4b5fd}",
            ".time{color:#7c6aa8;font-size:.78rem;margin-left:8px}",
            ".text{white-space:pre-wrap;word-wrap:break-word;margin-top:2px}",
            ".att,.emb{display:block;margin-top:6px;font-size:.85rem;color:#a78bfa}",
            ".notes{margin-top:28px;border-top:1px solid rgba(139,92,246,.3);padding-top:16px}",
            ".note{background:rgba(245,158,11,.1);border-left:3px solid #f59e0b;"
            "padding:8px 12px;border-radius:0 8px 8px 0;margin-bottom:8px}",
            "a{color:#a78bfa}",
            "</style>", "</head>", "<body>", '<div class="wrap">', "<header>",
            f"<h1>{esc(title)}</h1>", '<div class="meta">',
            f"Сервер: {esc(guild.name)}<br>",
            f"Автор ID: {row['user_id']}<br>",
            f"Приоритет: {esc(PRIORITIES[priority_of(row)][0])}<br>",
            f"Открыт: {esc(fmt_ts(row['created_at']))}<br>",
            f"Сообщений: {len(messages)}",
            "</div>", "</header>",
        ]
        for message in messages:
            stamp = message.created_at.astimezone(TZ).strftime("%d.%m.%Y %H:%M")
            try:
                avatar = str(message.author.display_avatar.url)
            except AttributeError:
                avatar = ""
            parts.append('<div class="msg">')
            parts.append(f'<img class="av" src="{esc(avatar)}" alt="">')
            parts.append('<div class="body">')
            parts.append(
                f'<span class="name">{esc(str(message.author))}</span>'
                f'<span class="time">{esc(stamp)}</span>'
            )
            if message.content:
                parts.append(f'<div class="text">{esc(message.content)}</div>')
            for embed in message.embeds:
                head = embed.title or ""
                body = (embed.description or "")[:500]
                if head or body:
                    parts.append(f'<span class="emb">▌ {esc(head)} {esc(body)}</span>')
            for attachment in message.attachments:
                parts.append(
                    f'<a class="att" href="{esc(attachment.url)}">📎 {esc(attachment.filename)}</a>'
                )
            parts.append("</div></div>")

        if notes:
            parts.append('<div class="notes"><h2 style="color:#f59e0b;font-size:1.1rem">'
                         "🗒️ Внутренние заметки поддержки</h2>")
            for note in notes:
                parts.append(
                    f'<div class="note"><b>ID {note["author_id"]}</b>'
                    f'<span class="time">{esc(fmt_ts(note["created_at"]))}</span>'
                    f'<div class="text">{esc(note["text"])}</div></div>'
                )
            parts.append("</div>")

        parts.append("</div></body></html>")
        return "\n".join(parts).encode("utf-8")

    async def build_transcript(self, channel, row):
        """Собирает TXT и HTML, кладёт файлы в DATA_DIR/transcripts и запоминает путь."""
        info = await self.type_info(row["guild_id"], row["type"])
        notes = await self.bot.db.fetchall(
            "SELECT * FROM ticket_notes WHERE ticket_id=? ORDER BY id", (row["id"],)
        )
        messages = await self.collect_messages(channel)
        txt = self.render_txt(channel.guild, row, info, messages, notes)
        htm = self.render_html(channel.guild, row, info, messages, notes)

        base = f"ticket-{row['id']:04d}"
        try:
            config.TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
            (config.TRANSCRIPT_DIR / f"{base}.txt").write_bytes(txt)
            (config.TRANSCRIPT_DIR / f"{base}.html").write_bytes(htm)
            await self.bot.db.execute(
                "UPDATE tickets SET transcript=? WHERE id=?",
                (str(config.TRANSCRIPT_DIR / f"{base}.html"), row["id"]),
            )
        except OSError:
            log.warning("Не удалось сохранить транскрипт тикета #%s", row["id"])
        return txt, htm, base

    # ---- создание
    async def create_ticket(self, interaction, type_info, reason):
        guild = interaction.guild
        user = interaction.user
        db = self.bot.db
        await interaction.response.defer(ephemeral=True)

        banned = await db.is_blacklisted(guild.id, user.id)
        if banned:
            why = banned["reason"] or "причина не указана"
            await interaction.followup.send(
                embed=embeds.err(f"Тебе запрещено открывать тикеты.\n**Причина:** {why}",
                                 "Доступ закрыт"),
                ephemeral=True,
            )
            return

        category_id = await db.get_setting(guild.id, "ticket_category")
        category = guild.get_channel(int(category_id)) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send(
                embed=embeds.err("Тикеты ещё не настроены. Сообщи администрации."), ephemeral=True
            )
            return

        max_open = int(await db.get_setting(guild.id, "ticket_max_open", "1"))
        rows = await db.fetchall(
            "SELECT id, channel_id FROM tickets WHERE guild_id=? AND user_id=? AND status='open'",
            (guild.id, user.id),
        )
        live = []
        for row in rows:
            if guild.get_channel(row["channel_id"]):
                live.append(row)
            else:  # канал удалили вручную
                await db.execute(
                    "UPDATE tickets SET status='closed', closed_at=? WHERE id=?",
                    (int(now_ts()), row["id"]),
                )
                self._open_channels.discard(row["channel_id"])
        if len(live) >= max_open:
            await interaction.followup.send(
                embed=embeds.warn(f"У тебя уже есть открытый тикет: <#{live[0]['channel_id']}>"),
                ephemeral=True,
            )
            return

        support_ids = await db.get_targets(guild.id, "ticket_support")
        support_roles = [r for r in (guild.get_role(i) for i in support_ids) if r]

        created = int(now_ts())
        ticket_id = await db.insert(
            "INSERT INTO tickets(guild_id, user_id, type, reason, created_at, last_activity) "
            "VALUES(?,?,?,?,?,?)",
            (guild.id, user.id, type_info["key"], reason, created, created),
        )

        member_perms = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True,
        )
        staff_perms = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True,
            attach_files=True, embed_links=True, manage_messages=True,
        )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: member_perms,
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True, manage_messages=True,
                embed_links=True, attach_files=True, read_message_history=True,
            ),
        }
        for role in support_roles:
            overwrites[role] = staff_perms

        slug = type_info.get("slug") or slugify(type_info["label"])
        try:
            channel = await guild.create_text_channel(
                name=channel_name_for(slug, ticket_id, "normal"),
                category=category,
                overwrites=overwrites,
                topic=f"Тикет #{ticket_id:04d} • {user} ({user.id})",
                reason=f"Тикет от {user}",
            )
        except (discord.Forbidden, discord.HTTPException):
            await db.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
            await interaction.followup.send(
                embed=embeds.err("Не удалось создать канал. Проверь права бота (Manage Channels)."),
                ephemeral=True,
            )
            return

        await db.execute("UPDATE tickets SET channel_id=? WHERE id=?", (channel.id, ticket_id))
        self._open_channels.add(channel.id)
        row = await self.reload_row(ticket_id)

        pings = " ".join([user.mention] + [r.mention for r in support_roles])
        await channel.send(
            content=pings,
            embed=ticket_embed(guild, row, type_info),
            view=TicketControlView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )
        await interaction.followup.send(
            embed=embeds.ok(f"Тикет создан: {channel.mention}", "Обращение открыто"), ephemeral=True
        )

    # ---- кнопки внутри тикета
    async def on_close_button(self, interaction):
        row = await self.get_ticket(interaction.channel.id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот канал не является открытым тикетом."), ephemeral=True
            )
            return
        if not (interaction.user.id == row["user_id"] or await self.is_staff(interaction.user)):
            await interaction.response.send_message(
                embed=embeds.err("Закрыть тикет может его автор или поддержка."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.warn("Закрыть этот тикет? Переписка сохранится файлом в лог-канале."),
            view=ConfirmCloseView(self, interaction.channel),
            ephemeral=True,
        )

    async def on_claim_button(self, interaction):
        row = await self.get_ticket(interaction.channel.id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот канал не является открытым тикетом."), ephemeral=True
            )
            return
        if not await self.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=embeds.err("Брать тикеты в работу может только поддержка."), ephemeral=True
            )
            return
        if row["claimed_by"]:
            await interaction.response.send_message(
                embed=embeds.warn(f"Тикет уже ведёт <@{row['claimed_by']}>."), ephemeral=True
            )
            return
        await self.bot.db.execute(
            "UPDATE tickets SET claimed_by=? WHERE id=?", (interaction.user.id, row["id"])
        )
        row = await self.reload_row(row["id"])
        info = await self.type_info(row["guild_id"], row["type"])
        await interaction.response.edit_message(
            embed=ticket_embed(interaction.guild, row, info), view=TicketControlView()
        )
        await interaction.channel.send(
            embed=embeds.info(f"✋ {interaction.user.mention} взял(а) тикет в работу."),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    async def on_transcript_button(self, interaction):
        row = await self.bot.db.fetchone(
            "SELECT * FROM tickets WHERE channel_id=? ORDER BY id DESC LIMIT 1",
            (interaction.channel.id,),
        )
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот канал не связан с тикетом."), ephemeral=True
            )
            return
        if not await self.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=embeds.err("Транскрипт доступен только поддержке."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        _, htm, base = await self.build_transcript(interaction.channel, row)
        await interaction.followup.send(
            embed=embeds.ok(f"Транскрипт тикета #{row['id']:04d}."),
            file=discord.File(io.BytesIO(htm), filename=f"{base}.html"),
            ephemeral=True,
        )

    async def on_lock_button(self, interaction):
        row = await self.get_ticket(interaction.channel.id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот канал не является открытым тикетом."), ephemeral=True
            )
            return
        if not await self.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=embeds.err("Блокировать тикет может только поддержка."), ephemeral=True
            )
            return
        new_state = not bool(row["locked"])
        await self.set_lock(interaction.channel, row, new_state)
        row = await self.reload_row(row["id"])
        info = await self.type_info(row["guild_id"], row["type"])
        await interaction.response.edit_message(
            embed=ticket_embed(interaction.guild, row, info), view=TicketControlView()
        )
        text = ("🔇 Тикет заблокирован — автор пока не может писать."
                if new_state else "🔊 Тикет разблокирован — автор снова может писать.")
        await interaction.channel.send(embed=embeds.info(text))

    async def set_lock(self, channel, row, locked):
        member = channel.guild.get_member(row["user_id"])
        if member:
            try:
                await channel.set_permissions(
                    member, view_channel=True, read_message_history=True,
                    send_messages=not locked, attach_files=not locked, embed_links=not locked,
                )
            except discord.HTTPException:
                pass
        await self.bot.db.execute(
            "UPDATE tickets SET locked=? WHERE id=?", (int(locked), row["id"])
        )

    # ---- оценка качества поддержки
    async def on_rate(self, interaction, ticket_id, score):
        row = await self.reload_row(ticket_id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Этот тикет больше не существует."), ephemeral=True
            )
            return
        if interaction.user.id != row["user_id"]:
            await interaction.response.send_message(
                embed=embeds.err("Оценить тикет может только его автор."), ephemeral=True
            )
            return
        await self.bot.db.execute("UPDATE tickets SET rating=? WHERE id=?", (score, ticket_id))
        await interaction.response.send_modal(RateCommentModal(self, ticket_id, score))

    async def save_rating_comment(self, interaction, ticket_id, score, comment):
        await self.bot.db.execute(
            "UPDATE tickets SET rating_comment=? WHERE id=?", (comment or None, ticket_id)
        )
        row = await self.reload_row(ticket_id)
        stars = "⭐" * score
        done = embeds.ok(f"Твоя оценка: {stars} ({score}/5)\nСпасибо, это помогает нам стать лучше!",
                         "Оценка принята")
        try:
            await interaction.response.edit_message(embed=done, view=None)
        except discord.HTTPException:
            try:
                await interaction.followup.send(embed=done, ephemeral=True)
            except discord.HTTPException:
                pass

        guild = self.bot.get_guild(row["guild_id"]) if row else None
        if guild is None:
            return
        info = await self.type_info(guild.id, row["type"])
        report = embeds.make(f"⭐ Оценка тикета #{ticket_id:04d}",
                             color=config.COLOR_OK if score >= 4 else config.COLOR_WARN)
        report.add_field(name="Оценка", value=f"{stars} ({score}/5)", inline=True)
        report.add_field(name="Автор", value=f"<@{row['user_id']}>", inline=True)
        report.add_field(name="Тип", value=info["label"], inline=True)
        if row["claimed_by"]:
            report.add_field(name="Вёл", value=f"<@{row['claimed_by']}>", inline=True)
        if comment:
            report.add_field(name="Комментарий", value=comment[:1000], inline=False)
        await self.bot.send_log(guild, report, key="ticket_log")

    # ---- закрытие
    async def close_ticket(self, channel, closer, reason=None):
        row = await self.get_ticket(channel.id)
        if row is None:
            return
        guild = channel.guild
        db = self.bot.db
        closed_at = int(now_ts())
        await db.execute(
            "UPDATE tickets SET status='closed', closed_at=?, closed_by=?, close_reason=? WHERE id=?",
            (closed_at, getattr(closer, "id", None), reason, row["id"]),
        )
        self._open_channels.discard(channel.id)
        row = await self.reload_row(row["id"])
        info = await self.type_info(guild.id, row["type"])
        _, htm, base = await self.build_transcript(channel, row)

        note_count = await db.fetchone(
            "SELECT COUNT(*) AS n FROM ticket_notes WHERE ticket_id=?", (row["id"],)
        )
        entry = embeds.make(f"🔒 Тикет #{row['id']:04d} закрыт")
        entry.add_field(name="Автор", value=f"<@{row['user_id']}>", inline=True)
        entry.add_field(name="Закрыл", value=getattr(closer, "mention", str(closer)), inline=True)
        if row["claimed_by"]:
            entry.add_field(name="Вёл", value=f"<@{row['claimed_by']}>", inline=True)
        entry.add_field(name="Тип", value=info["label"], inline=True)
        entry.add_field(name="Приоритет", value=PRIORITIES[priority_of(row)][0], inline=True)
        entry.add_field(name="Открыт", value=f"<t:{row['created_at']}:f>", inline=True)
        entry.add_field(name="В работе", value=fmt_duration(closed_at - row["created_at"]),
                        inline=True)
        if note_count and note_count["n"]:
            entry.add_field(name="Заметок", value=str(note_count["n"]), inline=True)
        if reason:
            entry.add_field(name="Причина закрытия", value=reason[:1000], inline=False)
        await self.bot.send_log(
            guild, entry, key="ticket_log",
            file=discord.File(io.BytesIO(htm), filename=f"{base}.html"),
        )

        author = guild.get_member(row["user_id"])
        if author:
            try:
                dm = embeds.make(f"🔒 Твой тикет #{row['id']:04d} закрыт",
                                 f"Сервер: **{guild.name}**")
                if reason:
                    dm.add_field(name="Причина", value=reason[:1000], inline=False)
                dm.add_field(name="Оцени работу поддержки",
                             value="Нажми на звёзды ниже — это займёт пару секунд.", inline=False)
                await author.send(
                    embed=dm,
                    file=discord.File(io.BytesIO(htm), filename=f"{base}.html"),
                    view=rating_view(row["id"]),
                )
            except discord.HTTPException:
                pass  # личные сообщения закрыты

        delete_on_close = (await db.get_setting(guild.id, "ticket_delete_on_close", "1")) == "1"
        archive_id = await db.get_setting(guild.id, "ticket_archive")
        archive = guild.get_channel(int(archive_id)) if archive_id else None

        if not delete_on_close and isinstance(archive, discord.CategoryChannel):
            try:
                await channel.send(embed=embeds.warn("Тикет закрыт и перенесён в архив."))
                if author:
                    await channel.set_permissions(
                        author, view_channel=True, read_message_history=True, send_messages=False
                    )
                await channel.edit(category=archive, name=f"closed-{row['id']:04d}",
                                   reason=f"Тикет закрыт: {closer}")
            except discord.HTTPException:
                log.warning("Не удалось отправить тикет #%s в архив", row["id"])
            return

        try:
            await channel.send(embed=embeds.warn("Тикет закрыт. Канал будет удалён через 5 секунд."))
        except discord.HTTPException:
            pass
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Тикет закрыт: {closer}")
        except discord.HTTPException:
            pass

    # ---- фоновое автозакрытие
    @tasks.loop(minutes=10)
    async def autoclose_loop(self):
        try:
            rows = await self.bot.db.fetchall(
                "SELECT * FROM tickets WHERE status='open' AND channel_id != 0"
            )
            now = int(now_ts())
            hours_cache = {}
            for row in rows:
                gid = row["guild_id"]
                if gid not in hours_cache:
                    try:
                        hours_cache[gid] = int(
                            await self.bot.db.get_setting(gid, "ticket_autoclose", "0")
                        )
                    except (TypeError, ValueError):
                        hours_cache[gid] = 0
                hours = hours_cache[gid]
                if hours <= 0:
                    continue
                last = row["last_activity"] or row["created_at"]
                if now - last < hours * 3600:
                    continue
                guild = self.bot.get_guild(gid)
                channel = guild.get_channel(row["channel_id"]) if guild else None
                if channel is None:
                    await self.bot.db.execute(
                        "UPDATE tickets SET status='closed', closed_at=? WHERE id=?", (now, row["id"])
                    )
                    self._open_channels.discard(row["channel_id"])
                    continue
                await self.close_ticket(channel, guild.me, reason="Автозакрытие: нет активности")
        except Exception:  # цикл не должен умирать из-за одной ошибки
            log.exception("Ошибка в цикле автозакрытия тикетов")

    @autoclose_loop.before_loop
    async def before_autoclose_loop(self):
        await self.bot.wait_until_ready()

    # ---- активность в тикете
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author.bot:
            return
        if message.channel.id not in self._open_channels:
            return
        row = await self.bot.db.fetchone(
            "SELECT * FROM tickets WHERE channel_id=? AND status='open'", (message.channel.id,)
        )
        if row is None:
            self._open_channels.discard(message.channel.id)
            return
        now = int(now_ts())
        first_reply = (
            row["first_reply_at"] is None
            and message.author.id != row["user_id"]
            and await self.is_staff(message.author)
        )
        if first_reply:
            await self.bot.db.execute(
                "UPDATE tickets SET last_activity=?, first_reply_at=? WHERE id=?",
                (now, now, row["id"]),
            )
        else:
            await self.bot.db.execute(
                "UPDATE tickets SET last_activity=? WHERE id=?", (now, row["id"])
            )

    # ---- команды администрации
    @ticket.command(name="panel", description="Отправить панель создания тикетов")
    @app_commands.describe(
        channel="Куда отправить панель (по умолчанию — текущий канал)",
        title="Свой заголовок панели",
        description="Свой текст панели (\\n — перенос строки)",
    )
    @access("ticket_admin")
    async def panel(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None,
                    title: str | None = None, description: str | None = None):
        channel = channel or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=embeds.err("Панель можно отправить только в текстовый канал."), ephemeral=True
            )
            return
        text = description.replace("\\n", "\n") if description else None
        try:
            await self.send_panel(channel, title, text)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.err(f"У меня нет прав писать в {channel.mention}."), ephemeral=True
            )
            return
        note = f"Панель отправлена в {channel.mention}."
        if not await self.bot.db.get_setting(interaction.guild.id, "ticket_category"):
            note += "\n⚠️ Категория для тикетов ещё не задана — выполни `/ticket setup`."
        await interaction.response.send_message(embed=embeds.ok(note), ephemeral=True)

    @ticket.command(name="setup", description="Настроить категорию, лог-канал и лимит тикетов")
    @app_commands.describe(
        category="Категория, где будут создаваться тикеты",
        log_channel="Канал для транскриптов закрытых тикетов",
        max_open="Сколько тикетов одновременно может быть у одного человека",
        delete_on_close="Удалять канал после закрытия (иначе — переносить в архив)",
    )
    @access("ticket_admin")
    async def setup_cmd(self, interaction: discord.Interaction, category: discord.CategoryChannel,
                        log_channel: discord.TextChannel | None = None,
                        max_open: app_commands.Range[int, 1, 5] = 1,
                        delete_on_close: bool = True):
        gid = interaction.guild.id
        await self.bot.db.set_setting(gid, "ticket_category", category.id)
        await self.bot.db.set_setting(gid, "ticket_max_open", max_open)
        await self.bot.db.set_setting(gid, "ticket_delete_on_close", int(delete_on_close))
        lines = [f"Категория: **{category.name}**", f"Лимит открытых тикетов: **{max_open}**"]
        if log_channel:
            await self.bot.db.set_setting(gid, "ticket_log", log_channel.id)
            lines.append(f"Лог тикетов: {log_channel.mention}")
        if delete_on_close:
            lines.append("После закрытия канал **удаляется** через 5 секунд.")
        else:
            lines.append("После закрытия канал **переносится в архив** "
                         "(категорию задаёт `/ticket archive`).")
        await interaction.response.send_message(
            embed=embeds.ok("\n".join(lines), "Тикеты настроены"), ephemeral=True
        )

    @ticket.command(name="autoclose", description="Автозакрытие тикетов без активности (0 — выключить)")
    @app_commands.describe(hours="Через сколько часов тишины закрывать тикет. 0 — не закрывать")
    @access("ticket_admin")
    async def autoclose(self, interaction: discord.Interaction,
                        hours: app_commands.Range[int, 0, 720]):
        await self.bot.db.set_setting(interaction.guild.id, "ticket_autoclose", hours)
        text = (f"Тикеты без активности будут закрываться через **{hours} ч**."
                if hours else "Автозакрытие выключено.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @ticket.command(name="archive", description="Категория-архив для закрытых тикетов")
    @app_commands.describe(category="Куда переносить каналы закрытых тикетов")
    @access("ticket_admin")
    async def archive(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        gid = interaction.guild.id
        await self.bot.db.set_setting(gid, "ticket_archive", category.id)
        lines = [f"Архив тикетов: **{category.name}**"]
        if (await self.bot.db.get_setting(gid, "ticket_delete_on_close", "1")) == "1":
            lines.append("⚠️ Сейчас каналы удаляются при закрытии. Чтобы они попадали в архив, "
                         "выполни `/ticket setup` с `delete_on_close: False`.")
        await interaction.response.send_message(embed=embeds.ok("\n".join(lines)), ephemeral=True)

    # ---- роли поддержки
    @support.command(name="add", description="Добавить роль поддержки (видит и ведёт все тикеты)")
    @app_commands.describe(role="Роль модераторов/поддержки")
    @access("ticket_admin")
    async def support_add(self, interaction: discord.Interaction, role: discord.Role):
        added = await self.bot.db.add_target(interaction.guild.id, "ticket_support", role.id)
        text = f"{role.mention} теперь видит новые тикеты." if added else f"{role.mention} уже в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @support.command(name="remove", description="Убрать роль поддержки")
    @app_commands.describe(role="Роль, которую нужно убрать")
    @access("ticket_admin")
    async def support_remove(self, interaction: discord.Interaction, role: discord.Role):
        removed = await self.bot.db.remove_target(interaction.guild.id, "ticket_support", role.id)
        text = f"{role.mention} убрана из поддержки." if removed else f"{role.mention} не была в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @support.command(name="list", description="Показать роли поддержки")
    @access("ticket_admin")
    async def support_list(self, interaction: discord.Interaction):
        ids = await self.bot.db.get_targets(interaction.guild.id, "ticket_support")
        text = "\n".join(f"• <@&{i}>" for i in ids) or "Роли не заданы — тикеты видят только администраторы."
        await interaction.response.send_message(
            embed=embeds.info(text, "🛠️ Роли поддержки"), ephemeral=True
        )

    # ---- типы обращений
    @type_group.command(name="add", description="Добавить или изменить тип обращения")
    @app_commands.describe(key="Короткий ключ (латиницей, без пробелов)", label="Название в меню",
                           emoji="Эмодзи", description="Подсказка под названием")
    @access("ticket_admin")
    async def type_add(self, interaction: discord.Interaction,
                       key: app_commands.Range[str, 1, 32],
                       label: app_commands.Range[str, 1, 80],
                       emoji: str = "🎫",
                       description: app_commands.Range[str, 1, 100] = ""):
        clean_key = slugify(key)
        types = await self.bot.db.get_ticket_types(interaction.guild.id)
        if len(types) >= 25 and clean_key not in {t["key"] for t in types}:
            await interaction.response.send_message(
                embed=embeds.err("В меню Discord помещается максимум 25 типов обращений."),
                ephemeral=True,
            )
            return
        await self.bot.db.add_ticket_type(
            interaction.guild.id, clean_key, label, emoji or "🎫", description,
            slugify(label), len(types),
        )
        await interaction.response.send_message(
            embed=embeds.ok(f"{emoji} **{label}** (`{clean_key}`) сохранён.\n"
                            "Отправь панель заново (`/ticket panel`), чтобы меню обновилось."),
            ephemeral=True,
        )

    @type_group.command(name="remove", description="Удалить тип обращения")
    @app_commands.describe(key="Ключ типа (см. /ticket type list)")
    @access("ticket_admin")
    async def type_remove(self, interaction: discord.Interaction, key: str):
        clean_key = slugify(key)
        removed = await self.bot.db.remove_ticket_type(interaction.guild.id, clean_key)
        if removed:
            message = embeds.ok(f"Тип `{clean_key}` удалён. Отправь панель заново (`/ticket panel`).")
        else:
            message = embeds.err(f"Тип `{clean_key}` не найден.")
        await interaction.response.send_message(embed=message, ephemeral=True)

    @type_group.command(name="list", description="Показать типы обращений сервера")
    @access("ticket_admin")
    async def type_list(self, interaction: discord.Interaction):
        types = await self.bot.db.get_ticket_types(interaction.guild.id)
        lines = [f"{t['emoji']} **{t['label']}** — `{t['key']}`\n└ {t['description'] or '—'}"
                 for t in types]
        await interaction.response.send_message(
            embed=embeds.info("\n".join(lines)[:4000], "🗂️ Типы обращений"), ephemeral=True
        )

    # ---- чёрный список
    @blacklist.command(name="add", description="Запретить участнику открывать тикеты")
    @app_commands.describe(user="Кому запретить", reason="Причина (покажем ему при попытке)")
    @access("ticket_admin")
    async def blacklist_add(self, interaction: discord.Interaction, user: discord.Member,
                            reason: str | None = None):
        await self.bot.db.add_blacklist(interaction.guild.id, user.id, reason, interaction.user.id)
        entry = embeds.make("🚫 Запрет на тикеты", color=config.COLOR_ERR)
        entry.add_field(name="Участник", value=f"{user.mention} (`{user.id}`)", inline=True)
        entry.add_field(name="Выдал", value=interaction.user.mention, inline=True)
        entry.add_field(name="Причина", value=reason or "—", inline=False)
        await self.bot.send_log(interaction.guild, entry, key="ticket_log")
        await interaction.response.send_message(
            embed=embeds.ok(f"{user.mention} больше не может открывать тикеты."), ephemeral=True
        )

    @blacklist.command(name="remove", description="Вернуть участнику возможность открывать тикеты")
    @app_commands.describe(user="Кого разблокировать")
    @access("ticket_admin")
    async def blacklist_remove(self, interaction: discord.Interaction, user: discord.Member):
        removed = await self.bot.db.remove_blacklist(interaction.guild.id, user.id)
        text = (f"{user.mention} снова может открывать тикеты."
                if removed else f"{user.mention} и не был в чёрном списке.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @blacklist.command(name="list", description="Кому запрещено открывать тикеты")
    @access("ticket_admin")
    async def blacklist_list(self, interaction: discord.Interaction):
        rows = await self.bot.db.list_blacklist(interaction.guild.id)
        if not rows:
            await interaction.response.send_message(
                embed=embeds.info("Чёрный список пуст.", "🚫 Запрет на тикеты"), ephemeral=True
            )
            return
        lines = [f"• <@{r['user_id']}> — {r['reason'] or 'без причины'} (<t:{r['added_at']}:R>)"
                 for r in rows]
        await interaction.response.send_message(
            embed=embeds.info("\n".join(lines)[:4000], "🚫 Запрет на тикеты"), ephemeral=True
        )

    # ---- команды внутри тикета
    async def _staff_ticket(self, interaction):
        """Возвращает строку тикета, если команда вызвана поддержкой в открытом тикете."""
        row = await self.get_ticket(interaction.channel.id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Эту команду нужно вызывать внутри открытого тикета."), ephemeral=True
            )
            return None
        if not await self.is_staff(interaction.user):
            await interaction.response.send_message(
                embed=embeds.err("Команда доступна только поддержке."), ephemeral=True
            )
            return None
        return row

    @ticket.command(name="add", description="Добавить участника в этот тикет")
    @app_commands.describe(user="Кого добавить")
    async def add(self, interaction: discord.Interaction, user: discord.Member):
        if await self._staff_ticket(interaction) is None:
            return
        await interaction.channel.set_permissions(
            user, view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        )
        await interaction.response.send_message(embed=embeds.ok(f"{user.mention} добавлен(а) в тикет."))

    @ticket.command(name="remove", description="Убрать участника из этого тикета")
    @app_commands.describe(user="Кого убрать")
    async def remove(self, interaction: discord.Interaction, user: discord.Member):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        if user.id == row["user_id"]:
            await interaction.response.send_message(
                embed=embeds.err("Автора тикета убрать нельзя — закрой тикет."), ephemeral=True
            )
            return
        await interaction.channel.set_permissions(user, overwrite=None)
        await interaction.response.send_message(embed=embeds.ok(f"{user.mention} убран(а) из тикета."))

    @ticket.command(name="rename", description="Переименовать канал тикета")
    @app_commands.describe(name="Новое название")
    async def rename(self, interaction: discord.Interaction, name: app_commands.Range[str, 1, 80]):
        if await self._staff_ticket(interaction) is None:
            return
        await interaction.channel.edit(name=name)
        await interaction.response.send_message(embed=embeds.ok("Канал переименован."), ephemeral=True)

    @ticket.command(name="move", description="Перенести тикет в другую категорию")
    @app_commands.describe(category="Куда перенести канал")
    async def move(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        if await self._staff_ticket(interaction) is None:
            return
        try:
            await interaction.channel.edit(category=category, reason=f"Перенос: {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.err("Нет прав переносить этот канал."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.ok(f"Тикет перенесён в **{category.name}**.")
        )

    @ticket.command(name="claim", description="Взять тикет в работу")
    async def claim(self, interaction: discord.Interaction):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        if row["claimed_by"] and row["claimed_by"] != interaction.user.id:
            await interaction.response.send_message(
                embed=embeds.warn(f"Тикет уже ведёт <@{row['claimed_by']}>. "
                                  "Используй `/ticket transfer`, чтобы передать его."),
                ephemeral=True,
            )
            return
        await self.bot.db.execute(
            "UPDATE tickets SET claimed_by=? WHERE id=?", (interaction.user.id, row["id"])
        )
        row = await self.reload_row(row["id"])
        await self.refresh_panel(interaction.channel, row)
        await interaction.response.send_message(
            embed=embeds.ok(f"✋ {interaction.user.mention} ведёт этот тикет."),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @ticket.command(name="unclaim", description="Отпустить тикет")
    async def unclaim(self, interaction: discord.Interaction):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        if not row["claimed_by"]:
            await interaction.response.send_message(
                embed=embeds.warn("Этот тикет никто не ведёт."), ephemeral=True
            )
            return
        await self.bot.db.execute("UPDATE tickets SET claimed_by=NULL WHERE id=?", (row["id"],))
        row = await self.reload_row(row["id"])
        await self.refresh_panel(interaction.channel, row)
        await interaction.response.send_message(
            embed=embeds.ok(f"🖐️ {interaction.user.mention} отпустил(а) тикет — он снова свободен."),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @ticket.command(name="transfer", description="Передать тикет другому сотруднику")
    @app_commands.describe(user="Кому передать")
    async def transfer(self, interaction: discord.Interaction, user: discord.Member):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        if not await self.is_staff(user):
            await interaction.response.send_message(
                embed=embeds.err(f"{user.mention} не входит в поддержку."), ephemeral=True
            )
            return
        await self.bot.db.execute("UPDATE tickets SET claimed_by=? WHERE id=?", (user.id, row["id"]))
        row = await self.reload_row(row["id"])
        await self.refresh_panel(interaction.channel, row)
        await interaction.channel.set_permissions(
            user, view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        )
        await interaction.response.send_message(
            embed=embeds.ok(f"🔁 Тикет передан {user.mention} (передал: {interaction.user.mention}).")
        )

    @ticket.command(name="priority", description="Сменить приоритет тикета")
    @app_commands.describe(level="Насколько срочно")
    @app_commands.choices(level=PRIORITY_CHOICES)
    async def priority(self, interaction: discord.Interaction, level: app_commands.Choice[str]):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        await self.bot.db.execute("UPDATE tickets SET priority=? WHERE id=?", (level.value, row["id"]))
        row = await self.reload_row(row["id"])
        info = await self.type_info(row["guild_id"], row["type"])
        slug = info.get("slug") or slugify(info["label"])
        await self.refresh_panel(interaction.channel, row)
        try:
            await interaction.channel.edit(
                name=channel_name_for(slug, row["id"], level.value),
                reason=f"Приоритет: {level.value}",
            )
        except discord.HTTPException:
            pass  # у Discord жёсткий лимит на переименование каналов
        await interaction.response.send_message(
            embed=embeds.ok(f"Приоритет тикета: **{level.name}**.")
        )

    @ticket.command(name="lock", description="Запретить автору писать в тикете")
    async def lock(self, interaction: discord.Interaction):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        await self.set_lock(interaction.channel, row, True)
        row = await self.reload_row(row["id"])
        await self.refresh_panel(interaction.channel, row)
        await interaction.response.send_message(
            embed=embeds.warn("🔇 Тикет заблокирован — автор пока не может писать.")
        )

    @ticket.command(name="unlock", description="Вернуть автору возможность писать")
    async def unlock(self, interaction: discord.Interaction):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        await self.set_lock(interaction.channel, row, False)
        row = await self.reload_row(row["id"])
        await self.refresh_panel(interaction.channel, row)
        await interaction.response.send_message(
            embed=embeds.ok("🔊 Тикет разблокирован — автор снова может писать.")
        )

    @ticket.command(name="note", description="Внутренняя заметка по тикету (автор её не увидит)")
    @app_commands.describe(text="Текст заметки")
    async def note(self, interaction: discord.Interaction, text: app_commands.Range[str, 1, 1000]):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        await self.bot.db.insert(
            "INSERT INTO ticket_notes(ticket_id, author_id, text, created_at) VALUES(?,?,?,?)",
            (row["id"], interaction.user.id, text, int(now_ts())),
        )
        entry = embeds.make(f"🗒️ Заметка по тикету #{row['id']:04d}", color=config.COLOR_WARN)
        entry.add_field(name="Автор заметки", value=interaction.user.mention, inline=True)
        entry.add_field(name="Канал", value=interaction.channel.mention, inline=True)
        entry.add_field(name="Текст", value=text[:1000], inline=False)
        await self.bot.send_log(interaction.guild, entry, key="ticket_log")
        await interaction.response.send_message(
            embed=embeds.ok("Заметка сохранена — она попадёт в транскрипт."), ephemeral=True
        )

    @ticket.command(name="notes", description="Показать заметки по этому тикету")
    async def notes(self, interaction: discord.Interaction):
        row = await self._staff_ticket(interaction)
        if row is None:
            return
        rows = await self.bot.db.fetchall(
            "SELECT * FROM ticket_notes WHERE ticket_id=? ORDER BY id", (row["id"],)
        )
        if not rows:
            await interaction.response.send_message(
                embed=embeds.info("Заметок пока нет.", "🗒️ Заметки"), ephemeral=True
            )
            return
        lines = [f"**<@{r['author_id']}>** · <t:{r['created_at']}:f>\n└ {r['text']}" for r in rows]
        await interaction.response.send_message(
            embed=embeds.info("\n\n".join(lines)[:4000], f"🗒️ Заметки по тикету #{row['id']:04d}"),
            ephemeral=True,
        )

    @ticket.command(name="close", description="Закрыть этот тикет")
    @app_commands.describe(reason="Причина закрытия (попадёт в лог и в ЛС автору)")
    async def close(self, interaction: discord.Interaction,
                    reason: app_commands.Range[str, 1, 500] | None = None):
        row = await self.get_ticket(interaction.channel.id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Эту команду нужно вызывать внутри открытого тикета."), ephemeral=True
            )
            return
        if not (interaction.user.id == row["user_id"] or await self.is_staff(interaction.user)):
            await interaction.response.send_message(
                embed=embeds.err("Закрыть тикет может его автор или поддержка."), ephemeral=True
            )
            return
        await interaction.response.send_message(embed=embeds.warn("Закрываю тикет…"), ephemeral=True)
        await self.close_ticket(interaction.channel, interaction.user, reason=reason or None)

    @ticket.command(name="reopen", description="Открыть закрытый тикет заново")
    @app_commands.describe(ticket_id="Номер тикета (например 7)")
    @access("ticket_admin")
    async def reopen(self, interaction: discord.Interaction, ticket_id: int):
        guild = interaction.guild
        db = self.bot.db
        row = await db.fetchone(
            "SELECT * FROM tickets WHERE id=? AND guild_id=?", (ticket_id, guild.id)
        )
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err(f"Тикет #{ticket_id:04d} не найден."), ephemeral=True
            )
            return
        if row["status"] == "open" and guild.get_channel(row["channel_id"]):
            await interaction.response.send_message(
                embed=embeds.warn(f"Тикет уже открыт: <#{row['channel_id']}>"), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        category_id = await db.get_setting(guild.id, "ticket_category")
        category = guild.get_channel(int(category_id)) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send(
                embed=embeds.err("Категория тикетов не настроена — выполни `/ticket setup`."),
                ephemeral=True,
            )
            return

        info = await self.type_info(guild.id, row["type"])
        author = guild.get_member(row["user_id"])
        support_ids = await db.get_targets(guild.id, "ticket_support")
        support_roles = [r for r in (guild.get_role(i) for i in support_ids) if r]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True, manage_messages=True,
                embed_links=True, attach_files=True, read_message_history=True,
            ),
        }
        if author:
            overwrites[author] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True,
            )
        for role in support_roles:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True, manage_messages=True,
            )

        old_channel = guild.get_channel(row["channel_id"])
        slug = info.get("slug") or slugify(info["label"])
        name = channel_name_for(slug, row["id"], priority_of(row))
        try:
            if old_channel is not None:  # канал жив (архив) — просто возвращаем его в работу
                channel = old_channel
                await channel.edit(category=category, name=name, overwrites=overwrites,
                                   reason=f"Тикет переоткрыт: {interaction.user}")
            else:
                channel = await guild.create_text_channel(
                    name=name, category=category, overwrites=overwrites,
                    topic=f"Тикет #{row['id']:04d} • переоткрыт",
                    reason=f"Тикет переоткрыт: {interaction.user}",
                )
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не удалось создать канал. Проверь права бота."), ephemeral=True
            )
            return

        now = int(now_ts())
        await db.execute(
            "UPDATE tickets SET status='open', channel_id=?, closed_at=NULL, closed_by=NULL, "
            "close_reason=NULL, locked=0, last_activity=? WHERE id=?",
            (channel.id, now, row["id"]),
        )
        self._open_channels.add(channel.id)
        row = await self.reload_row(row["id"])
        await channel.send(
            content=f"<@{row['user_id']}>",
            embed=ticket_embed(guild, row, info),
            view=TicketControlView(),
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        await channel.send(
            embed=embeds.info(f"♻️ Тикет переоткрыт по решению {interaction.user.mention}."),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await interaction.followup.send(
            embed=embeds.ok(f"Тикет #{row['id']:04d} снова открыт: {channel.mention}"), ephemeral=True
        )

    # ---- обзор и статистика
    @ticket.command(name="list", description="Список тикетов сервера")
    @app_commands.describe(user="Только тикеты этого участника", status="Статус",
                           ticket_type="Ключ типа обращения (см. /ticket type list)")
    @app_commands.choices(status=[
        app_commands.Choice(name="Открытые", value="open"),
        app_commands.Choice(name="Закрытые", value="closed"),
        app_commands.Choice(name="Все", value="all"),
    ])
    @access("ticket_manage")
    async def list_tickets(self, interaction: discord.Interaction,
                           user: discord.Member | None = None,
                           status: app_commands.Choice[str] | None = None,
                           ticket_type: str | None = None):
        sql = "SELECT * FROM tickets WHERE guild_id=?"
        params = [interaction.guild.id]
        state = status.value if status else "open"
        if state != "all":
            sql += " AND status=?"
            params.append(state)
        if user:
            sql += " AND user_id=?"
            params.append(user.id)
        if ticket_type:
            sql += " AND type=?"
            params.append(slugify(ticket_type))
        sql += " ORDER BY id DESC"
        rows = await self.bot.db.fetchall(sql, params)

        if not rows:
            await interaction.response.send_message(
                embed=embeds.info("Ничего не найдено.", "🎫 Тикеты"), ephemeral=True
            )
            return

        types = {t["key"]: t for t in await self.bot.db.get_ticket_types(interaction.guild.id)}

        def line(row):
            info = types.get(row["type"], FALLBACK_TYPE)
            mark = "🟢" if row["status"] == "open" else "⚫"
            where = f"<#{row['channel_id']}>" if row["status"] == "open" else "архив"
            lead = f" · ведёт <@{row['claimed_by']}>" if row["claimed_by"] else ""
            return (f"{mark} **#{row['id']:04d}** {info['emoji']} {info['label']} — "
                    f"<@{row['user_id']}> · {where}{lead}")

        pages = paginate(rows, PAGE_SIZE, f"🎫 Тикеты ({len(rows)})", line)
        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0], ephemeral=True)
            return
        await interaction.response.send_message(
            embed=pages[0], view=PageView(pages, interaction.user.id), ephemeral=True
        )

    @ticket.command(name="info", description="Карточка тикета")
    @app_commands.describe(ticket_id="Номер тикета (пусто — тикет этого канала)")
    @access("ticket_manage")
    async def info(self, interaction: discord.Interaction, ticket_id: int | None = None):
        row = await self.resolve_ticket(interaction, ticket_id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Тикет не найден. Укажи номер или вызови команду в канале тикета."),
                ephemeral=True,
            )
            return
        type_data = await self.type_info(row["guild_id"], row["type"])
        notes = await self.bot.db.fetchone(
            "SELECT COUNT(*) AS n FROM ticket_notes WHERE ticket_id=?", (row["id"],)
        )
        embed = embeds.make(f"{type_data['emoji']} Тикет #{row['id']:04d}",
                            color=PRIORITIES[priority_of(row)][1])
        embed.add_field(name="Автор", value=f"<@{row['user_id']}>", inline=True)
        embed.add_field(name="Тип", value=type_data["label"], inline=True)
        embed.add_field(name="Приоритет", value=PRIORITIES[priority_of(row)][0], inline=True)
        embed.add_field(name="Статус", value="🟢 Открыт" if row["status"] == "open" else "⚫ Закрыт",
                        inline=True)
        embed.add_field(name="Ведёт", value=f"<@{row['claimed_by']}>" if row["claimed_by"] else "—",
                        inline=True)
        embed.add_field(name="Заметок", value=str(notes["n"] if notes else 0), inline=True)
        embed.add_field(name="Открыт", value=f"<t:{row['created_at']}:f>", inline=True)
        embed.add_field(name="Закрыт",
                        value=f"<t:{row['closed_at']}:f>" if row["closed_at"] else "—", inline=True)
        if row["first_reply_at"]:
            embed.add_field(name="Первый ответ",
                            value=fmt_duration(row["first_reply_at"] - row["created_at"]), inline=True)
        if row["closed_by"]:
            embed.add_field(name="Закрыл", value=f"<@{row['closed_by']}>", inline=True)
        if row["close_reason"]:
            embed.add_field(name="Причина закрытия", value=row["close_reason"][:1000], inline=False)
        if row["rating"]:
            value = "⭐" * row["rating"] + f" ({row['rating']}/5)"
            if row["rating_comment"]:
                value += f"\n> {row['rating_comment'][:500]}"
            embed.add_field(name="Оценка", value=value, inline=False)
        embed.add_field(name="Обращение", value=f">>> {row['reason']}"[:1000], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ticket.command(name="transcript", description="Получить файл переписки тикета")
    @app_commands.describe(ticket_id="Номер тикета (пусто — тикет этого канала)")
    @access("ticket_manage")
    async def transcript(self, interaction: discord.Interaction, ticket_id: int | None = None):
        row = await self.resolve_ticket(interaction, ticket_id)
        if row is None:
            await interaction.response.send_message(
                embed=embeds.err("Тикет не найден."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        base = f"ticket-{row['id']:04d}"
        path = config.TRANSCRIPT_DIR / f"{base}.html"
        if path.exists():
            data = path.read_bytes()
        else:
            channel = interaction.guild.get_channel(row["channel_id"])
            if channel is None:
                await interaction.followup.send(
                    embed=embeds.err("Файл транскрипта не сохранился, а канал тикета уже удалён."),
                    ephemeral=True,
                )
                return
            _, data, base = await self.build_transcript(channel, row)
        await interaction.followup.send(
            embed=embeds.ok(f"Транскрипт тикета #{row['id']:04d}."),
            file=discord.File(io.BytesIO(data), filename=f"{base}.html"),
            ephemeral=True,
        )

    @ticket.command(name="stats", description="Статистика по тикетам")
    @app_commands.describe(period_days="За сколько последних дней считать (по умолчанию 30)")
    @access("ticket_manage")
    async def stats(self, interaction: discord.Interaction,
                    period_days: app_commands.Range[int, 1, 365] = 30):
        gid = interaction.guild.id
        since = int(now_ts()) - period_days * 86400
        db = self.bot.db

        async def scalar(sql, params):
            row = await db.fetchone(sql, params)
            return row["v"] if row else None

        opened = await scalar(
            "SELECT COUNT(*) AS v FROM tickets WHERE guild_id=? AND created_at>=?", (gid, since)
        )
        closed = await scalar(
            "SELECT COUNT(*) AS v FROM tickets WHERE guild_id=? AND status='closed' AND closed_at>=?",
            (gid, since),
        )
        open_now = await scalar(
            "SELECT COUNT(*) AS v FROM tickets WHERE guild_id=? AND status='open'", (gid,)
        )
        reply_avg = await scalar(
            "SELECT AVG(first_reply_at - created_at) AS v FROM tickets "
            "WHERE guild_id=? AND created_at>=? AND first_reply_at IS NOT NULL", (gid, since)
        )
        close_avg = await scalar(
            "SELECT AVG(closed_at - created_at) AS v FROM tickets "
            "WHERE guild_id=? AND created_at>=? AND closed_at IS NOT NULL", (gid, since)
        )

        embed = embeds.make(f"📊 Статистика тикетов за {period_days} дн.")
        embed.add_field(name="Открыто", value=str(opened or 0), inline=True)
        embed.add_field(name="Закрыто", value=str(closed or 0), inline=True)
        embed.add_field(name="Открыто сейчас", value=str(open_now or 0), inline=True)
        embed.add_field(name="Среднее до первого ответа", value=fmt_duration(reply_avg), inline=True)
        embed.add_field(name="Среднее до закрытия", value=fmt_duration(close_avg), inline=True)

        top = await db.fetchall(
            "SELECT closed_by, COUNT(*) AS n, AVG(rating) AS r FROM tickets "
            "WHERE guild_id=? AND status='closed' AND closed_at>=? AND closed_by IS NOT NULL "
            "GROUP BY closed_by ORDER BY n DESC LIMIT 10",
            (gid, since),
        )
        if top:
            lines = []
            for place, row in enumerate(top, start=1):
                rating = f" · ⭐ {row['r']:.1f}" if row["r"] else ""
                lines.append(f"`{place}.` <@{row['closed_by']}> — {row['n']} закрыто{rating}")
            embed.add_field(name="🏅 Топ поддержки", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="🏅 Топ поддержки", value="Пока никто не закрывал тикеты.",
                            inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
''',
    'vex.cogs.wipe': r'''"""Вайп-реакты: событие с кнопками «Приду / Не приду / Опоздаю», /noreact и статистика явки."""
import re
from datetime import datetime
from time import time as now_ts
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import config, embeds
from ..checks import access, member_has_access

TZ = ZoneInfo(config.TIMEZONE)
LINK_RE = re.compile(r"channels/(?:\d+|@me)/(\d+)/(\d+)")
STATUSES = {
    "accepted": ("✅", "Придут"),
    "declined": ("❌", "Не придут"),
    "late": ("🕒", "Опоздают"),
}
REMIND_BEFORE = 15 * 60  # за сколько секунд напоминать участникам


# --------------------------------------------------------------------------- утилиты
def parse_datetime(date_s, time_s):
    """'25.11.2026' или '25.11' + '19:00' -> datetime в часовом поясе бота (или None)."""
    now = datetime.now(TZ)
    try:
        parts = [int(p) for p in re.split(r"[./-]", date_s.strip())]
        hour, minute = [int(p) for p in re.split(r"[:.]", time_s.strip())]
        if len(parts) == 2:
            day, month = parts
            dt = datetime(now.year, month, day, hour, minute, tzinfo=TZ)
            if dt < now:
                dt = dt.replace(year=now.year + 1)
        elif len(parts) == 3:
            day, month, year = parts
            if year < 100:
                year += 2000
            dt = datetime(year, month, day, hour, minute, tzinfo=TZ)
        else:
            return None
    except ValueError:
        return None
    return dt


def render_list(rows, status):
    lines = []
    for row in rows:
        if row["status"] != status:
            continue
        line = f"<@{row['user_id']}>"
        if row["reason"]:
            line += f" — {discord.utils.escape_markdown(row['reason'])}"
        lines.append(line)
    text = ""
    shown = 0
    for line in lines:
        if len(text) + len(line) + 1 > 1000:
            text += f"\n…и ещё {len(lines) - shown}"
            break
        text += ("\n" if text else "") + line
        shown += 1
    return len(lines), text or "—"


def build_embed(ev, rows):
    closed = bool(ev["closed"])
    embed = embeds.make(
        title=f"{'🔒' if closed else '📝'} {ev['title']}",
        description=ev["description"] or None,
        color=config.COLOR_DARK if closed else config.COLOR_MAIN,
        footer=False,
    )
    ts = int(ev["ts"])
    embed.add_field(
        name="📅 Дата и время",
        value=f"<t:{ts}:F>\n<t:{ts}:R>\n*(указано по {config.TIMEZONE})*",
        inline=False,
    )
    embed.add_field(name="🗺️ Сервер", value=ev["server"] or "—", inline=False)
    for status, (emoji, label) in STATUSES.items():
        count, text = render_list(rows, status)
        embed.add_field(name=f"{emoji} {label} ({count})", value=text, inline=True)
    note = " • приём ответов закрыт" if closed else ""
    embed.set_footer(text=f"Создал: {ev['creator_name']} • {config.BRAND}{note}")
    return embed


def chunk_mentions(members, limit=1800):
    chunks, current = [], ""
    for member in members:
        piece = member.mention + " "
        if len(current) + len(piece) > limit:
            chunks.append(current.strip())
            current = ""
        current += piece
    if current.strip():
        chunks.append(current.strip())
    return chunks


# --------------------------------------------------------------------------- интерфейс
class ReasonModal(discord.ui.Modal):
    def __init__(self, cog, ev, status, message):
        super().__init__(title="Укажи причину" if status == "declined" else "Во сколько будешь?")
        self.cog = cog
        self.ev_id = ev["message_id"]
        self.status = status
        self.message = message
        self.reason = discord.ui.TextInput(
            label="Причина" if status == "declined" else "Комментарий",
            placeholder="Например: работа / нет интернета / буду к 20:00",
            required=False,
            max_length=100,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction):
        await self.cog.save_response(self.ev_id, interaction.user.id, self.status, str(self.reason).strip())
        await interaction.response.defer()
        await self.cog.refresh_message(self.message, self.ev_id)


class EditModal(discord.ui.Modal):
    def __init__(self, cog, ev, message):
        super().__init__(title="Редактировать событие")
        self.cog = cog
        self.ev_id = ev["message_id"]
        self.message = message
        dt = datetime.fromtimestamp(ev["ts"], TZ)
        self.title_in = discord.ui.TextInput(label="Название", default=ev["title"], max_length=100)
        self.desc_in = discord.ui.TextInput(
            label="Описание", default=ev["description"] or "", style=discord.TextStyle.paragraph,
            required=False, max_length=1000,
        )
        self.date_in = discord.ui.TextInput(label="Дата (ДД.ММ.ГГГГ)", default=dt.strftime("%d.%m.%Y"),
                                            max_length=10)
        self.time_in = discord.ui.TextInput(label="Время (ЧЧ:ММ)", default=dt.strftime("%H:%M"), max_length=5)
        for item in (self.title_in, self.desc_in, self.date_in, self.time_in):
            self.add_item(item)

    async def on_submit(self, interaction):
        dt = parse_datetime(str(self.date_in), str(self.time_in))
        if dt is None:
            await interaction.response.send_message(
                embed=embeds.err("Не понял дату или время. Формат: `25.11.2026` и `19:00`."), ephemeral=True
            )
            return
        await self.cog.bot.db.execute(
            "UPDATE wipe_events SET title=?, description=?, ts=?, reminded=0 WHERE message_id=?",
            (str(self.title_in), str(self.desc_in), int(dt.timestamp()), self.ev_id),
        )
        await interaction.response.defer()
        await self.cog.refresh_message(self.message, self.ev_id)


class WipeView(discord.ui.View):
    def __init__(self, closed=False):
        super().__init__(timeout=None)
        if closed:
            for child in self.children:
                if getattr(child, "custom_id", None) != "vex:wipe:settings":
                    child.disabled = True

    @discord.ui.button(label="Приду", emoji="✅", style=discord.ButtonStyle.success, custom_id="vex:wipe:accepted")
    async def accept(self, interaction, button):
        await interaction.client.get_cog("Wipe").handle_response(interaction, "accepted")

    @discord.ui.button(label="Не приду", emoji="❌", style=discord.ButtonStyle.danger, custom_id="vex:wipe:declined")
    async def decline(self, interaction, button):
        await interaction.client.get_cog("Wipe").handle_response(interaction, "declined")

    @discord.ui.button(label="Опоздаю", emoji="🕒", style=discord.ButtonStyle.secondary, custom_id="vex:wipe:late")
    async def late(self, interaction, button):
        await interaction.client.get_cog("Wipe").handle_response(interaction, "late")

    @discord.ui.button(emoji="📝", style=discord.ButtonStyle.secondary, custom_id="vex:wipe:edit")
    async def edit(self, interaction, button):
        await interaction.client.get_cog("Wipe").handle_edit(interaction)

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.primary, custom_id="vex:wipe:settings")
    async def settings(self, interaction, button):
        await interaction.client.get_cog("Wipe").handle_settings(interaction)


class SettingsView(discord.ui.View):
    def __init__(self, cog, ev_id, message):
        super().__init__(timeout=120)
        self.cog = cog
        self.ev_id = ev_id
        self.message = message

    @discord.ui.button(label="Закрыть / открыть приём", emoji="🔒", style=discord.ButtonStyle.secondary)
    async def toggle(self, interaction, button):
        ev = await self.cog.get_event(self.ev_id)
        new_state = 0 if ev["closed"] else 1
        await self.cog.bot.db.execute("UPDATE wipe_events SET closed=? WHERE message_id=?",
                                      (new_state, self.ev_id))
        await self.cog.refresh_message(self.message, self.ev_id)
        text = "Приём ответов закрыт." if new_state else "Приём ответов снова открыт."
        await interaction.response.edit_message(embed=embeds.ok(text), view=None)

    @discord.ui.button(label="Напомнить не ответившим", emoji="🔔", style=discord.ButtonStyle.primary)
    async def remind(self, interaction, button):
        ev = await self.cog.get_event(self.ev_id)
        pending = await self.cog.pending_members(interaction.guild, self.message.channel, ev)
        if not pending:
            await interaction.response.edit_message(embed=embeds.ok("Все уже ответили."), view=None)
            return
        await interaction.response.edit_message(
            embed=embeds.ok(f"Напоминаю {len(pending)} участникам."), view=None
        )
        for chunk in chunk_mentions(pending):
            await self.message.reply(
                f"🔔 Отметьтесь, пожалуйста, под событием!\n{chunk}",
                allowed_mentions=discord.AllowedMentions(users=True),
            )

    @discord.ui.button(label="Удалить событие", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def delete(self, interaction, button):
        db = self.cog.bot.db
        await db.execute("DELETE FROM wipe_responses WHERE message_id=?", (self.ev_id,))
        await db.execute("DELETE FROM wipe_events WHERE message_id=?", (self.ev_id,))
        try:
            await self.message.delete()
        except discord.HTTPException:
            pass
        await interaction.response.edit_message(embed=embeds.ok("Событие удалено."), view=None)


# --------------------------------------------------------------------------- модуль
class Wipe(commands.Cog):
    wipe = app_commands.Group(name="wipe", description="Вайп-события клана", guild_only=True)

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(WipeView())
        self.reminder_loop.start()

    async def cog_unload(self):
        self.reminder_loop.cancel()

    # ---- данные
    async def get_event(self, message_id):
        return await self.bot.db.fetchone("SELECT * FROM wipe_events WHERE message_id=?", (message_id,))

    async def get_rows(self, message_id):
        return await self.bot.db.fetchall(
            "SELECT user_id, status, reason FROM wipe_responses WHERE message_id=? ORDER BY rowid",
            (message_id,),
        )

    async def save_response(self, message_id, user_id, status, reason):
        await self.bot.db.execute(
            "INSERT INTO wipe_responses(message_id, user_id, status, reason) VALUES(?,?,?,?) "
            "ON CONFLICT(message_id, user_id) DO UPDATE SET status=excluded.status, reason=excluded.reason",
            (message_id, user_id, status, reason or None),
        )

    async def refresh_message(self, message, message_id):
        ev = await self.get_event(message_id)
        if ev is None:
            return
        rows = await self.get_rows(message_id)
        try:
            await message.edit(embed=build_embed(ev, rows), view=WipeView(closed=bool(ev["closed"])))
        except discord.HTTPException:
            pass

    # ---- действия для сайта
    async def fetch_event_message(self, ev):
        channel = self.bot.get_channel(ev["channel_id"])
        if channel is None:
            return None
        try:
            return await channel.fetch_message(ev["message_id"])
        except discord.HTTPException:
            return None

    async def set_closed(self, message_id, closed):
        await self.bot.db.execute("UPDATE wipe_events SET closed=? WHERE message_id=?", (int(closed), message_id))
        ev = await self.get_event(message_id)
        message = await self.fetch_event_message(ev) if ev else None
        if message:
            await self.refresh_message(message, message_id)

    async def delete_event(self, message_id):
        ev = await self.get_event(message_id)
        message = await self.fetch_event_message(ev) if ev else None
        await self.bot.db.execute("DELETE FROM wipe_responses WHERE message_id=?", (message_id,))
        await self.bot.db.execute("DELETE FROM wipe_events WHERE message_id=?", (message_id,))
        if message:
            try:
                await message.delete()
            except discord.HTTPException:
                pass

    async def remind_pending(self, message_id):
        """Упоминает не ответивших под событием. Возвращает, скольким напомнили."""
        ev = await self.get_event(message_id)
        message = await self.fetch_event_message(ev) if ev else None
        if message is None:
            return 0
        pending = await self.pending_members(message.guild, message.channel, ev)
        for chunk in chunk_mentions(pending):
            await message.reply(
                f"🔔 Отметьтесь, пожалуйста, под событием!\n{chunk}",
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        return len(pending)

    async def can_manage(self, member, ev):
        return member.id == ev["creator_id"] or await member_has_access(self.bot, member, "wipe")

    async def pending_members(self, guild, channel, ev, role=None):
        rows = await self.get_rows(ev["message_id"]) if ev else []
        responded = {r["user_id"] for r in rows}
        if role is None and ev and ev["ping_role_id"]:
            role = guild.get_role(ev["ping_role_id"])
        base = role.members if role else channel.members
        return [m for m in base if not m.bot and m.id not in responded]

    # ---- кнопки
    async def handle_response(self, interaction, status):
        ev = await self.get_event(interaction.message.id)
        if ev is None:
            await interaction.response.send_message(
                embed=embeds.err("Это событие уже не отслеживается."), ephemeral=True
            )
            return
        if ev["closed"]:
            await interaction.response.send_message(
                embed=embeds.warn("Приём ответов закрыт."), ephemeral=True
            )
            return

        existing = await self.bot.db.fetchone(
            "SELECT status FROM wipe_responses WHERE message_id=? AND user_id=?",
            (ev["message_id"], interaction.user.id),
        )
        if existing and existing["status"] == status:  # повторное нажатие снимает ответ
            await self.bot.db.execute(
                "DELETE FROM wipe_responses WHERE message_id=? AND user_id=?",
                (ev["message_id"], interaction.user.id),
            )
        elif status != "accepted" and ev["ask_reason"]:
            await interaction.response.send_modal(ReasonModal(self, ev, status, interaction.message))
            return
        else:
            await self.save_response(ev["message_id"], interaction.user.id, status, None)

        rows = await self.get_rows(ev["message_id"])
        await interaction.response.edit_message(embed=build_embed(ev, rows), view=WipeView())

    async def handle_edit(self, interaction):
        ev = await self.get_event(interaction.message.id)
        if ev is None:
            await interaction.response.send_message(embed=embeds.err("Событие не найдено."), ephemeral=True)
            return
        if not await self.can_manage(interaction.user, ev):
            await interaction.response.send_message(
                embed=embeds.err("Редактировать может автор события или модерация."), ephemeral=True
            )
            return
        await interaction.response.send_modal(EditModal(self, ev, interaction.message))

    async def handle_settings(self, interaction):
        ev = await self.get_event(interaction.message.id)
        if ev is None:
            await interaction.response.send_message(embed=embeds.err("Событие не найдено."), ephemeral=True)
            return
        if not await self.can_manage(interaction.user, ev):
            await interaction.response.send_message(
                embed=embeds.err("Настройки доступны автору события и модерации."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=embeds.info("Что сделать с событием?", "⚙️ Настройки события"),
            view=SettingsView(self, ev["message_id"], interaction.message),
            ephemeral=True,
        )

    # ---- напоминание за 15 минут
    @tasks.loop(minutes=1)
    async def reminder_loop(self):
        try:
            now = int(now_ts())
            events = await self.bot.db.fetchall(
                "SELECT * FROM wipe_events WHERE closed=0 AND reminded=0 AND ts > ? AND ts <= ?",
                (now, now + REMIND_BEFORE),
            )
            for ev in events:
                await self.bot.db.execute(
                    "UPDATE wipe_events SET reminded=1 WHERE message_id=?", (ev["message_id"],)
                )
                channel = self.bot.get_channel(ev["channel_id"])
                if channel is None:
                    continue
                rows = await self.get_rows(ev["message_id"])
                ids = [r["user_id"] for r in rows if r["status"] in ("accepted", "late")]
                if not ids:
                    continue
                embed = embeds.make(
                    f"⏰ Скоро начало: {ev['title']}",
                    f"Старт <t:{ev['ts']}:R>. Все, кто отметился, — на связь!",
                )
                mentions = " ".join(f"<@{i}>" for i in ids)[:1900]
                await channel.send(
                    content=mentions, embed=embed, allowed_mentions=discord.AllowedMentions(users=True)
                )
        except Exception:  # цикл не должен умирать из-за одной ошибки
            import logging

            logging.getLogger("vex").exception("Ошибка в цикле напоминаний")

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    # ---- команды
    @app_commands.command(name="wipereact", description="Создать событие с реакциями (вайп, рейд, сбор)")
    @app_commands.describe(
        title="Название события",
        description="Описание (\\n — перенос строки)",
        date="Дата: ДД.ММ.ГГГГ или ДД.ММ",
        time="Время: ЧЧ:ММ",
        ask_for_reason="Спрашивать причину при «Не приду» и «Опоздаю»",
        server="Сервер Rust / IP (необязательно)",
        ping_role="Роль, которую упомянуть в сообщении (необязательно)",
    )
    @app_commands.guild_only()
    @access("wipe")
    async def wipereact(self, interaction: discord.Interaction,
                        title: app_commands.Range[str, 1, 100],
                        description: str,
                        date: str, time: str,
                        ask_for_reason: bool = False,
                        server: str | None = None,
                        ping_role: discord.Role | None = None):
        dt = parse_datetime(date, time)
        if dt is None:
            await interaction.response.send_message(
                embed=embeds.err("Не понял дату или время. Пример: дата `25.11.2026`, время `19:00`."),
                ephemeral=True,
            )
            return
        if dt < datetime.now(TZ):
            await interaction.response.send_message(
                embed=embeds.err("Эта дата уже в прошлом."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        ev = {
            "title": title,
            "description": description.replace("\\n", "\n")[:1000],
            "server": server[:200] if server else None,
            "ts": int(dt.timestamp()),
            "closed": 0,
            "creator_name": interaction.user.display_name,
        }
        try:
            message = await interaction.channel.send(
                content=ping_role.mention if ping_role else None,
                embed=build_embed(ev, []),
                view=WipeView(),
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=embeds.err("У меня нет прав писать в этот канал."), ephemeral=True
            )
            return

        await self.bot.db.execute(
            "INSERT INTO wipe_events(message_id, guild_id, channel_id, creator_id, creator_name, title, "
            "description, server, ts, ask_reason, ping_role_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (message.id, interaction.guild.id, message.channel.id, interaction.user.id,
             ev["creator_name"], ev["title"], ev["description"], ev["server"], ev["ts"],
             int(ask_for_reason), ping_role.id if ping_role else None),
        )
        await interaction.followup.send(embed=embeds.ok("Событие создано."), ephemeral=True)

    @app_commands.command(name="noreact", description="Показать, кто не отреагировал на сообщение")
    @app_commands.describe(
        message="Ссылка на сообщение или его ID",
        role="Проверять только участников этой роли (по умолчанию — все, кто видит канал)",
        ping="Сразу упомянуть всех не ответивших",
    )
    @app_commands.guild_only()
    @access("wipe")
    async def noreact(self, interaction: discord.Interaction, message: str,
                      role: discord.Role | None = None, ping: bool = False):
        guild = interaction.guild
        match = LINK_RE.search(message)
        if match:
            channel_id, message_id = int(match.group(1)), int(match.group(2))
        elif message.strip().isdigit():
            channel_id, message_id = None, int(message.strip())
        else:
            await interaction.response.send_message(
                embed=embeds.err("Пришли ссылку на сообщение или его ID."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=not ping)

        ev = await self.get_event(message_id)
        if channel_id is None:
            channel_id = ev["channel_id"] if ev else interaction.channel.id
        channel = guild.get_channel_or_thread(channel_id)
        if channel is None:
            await interaction.followup.send(embed=embeds.err("Не нашёл такой канал."), ephemeral=True)
            return
        try:
            target = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            await interaction.followup.send(
                embed=embeds.err("Не нашёл сообщение. Если оно в другом канале — пришли ссылку."),
                ephemeral=True,
            )
            return

        if ev:
            missing = await self.pending_members(guild, channel, ev, role)
        else:
            responded = set()
            for reaction in target.reactions:
                async for user in reaction.users():
                    responded.add(user.id)
            base = role.members if role else channel.members
            missing = [m for m in base if not m.bot and m.id not in responded]

        if not missing:
            await interaction.followup.send(embed=embeds.ok("Все уже отреагировали 🎉"))
            return

        if ping:
            chunks = chunk_mentions(missing)
            await interaction.followup.send(
                content=f"🔔 Не отреагировали ({len(missing)}) — отметьтесь здесь: {target.jump_url}\n{chunks[0]}",
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            for chunk in chunks[1:]:
                await interaction.followup.send(
                    content=chunk, allowed_mentions=discord.AllowedMentions(users=True)
                )
            return

        listing = ""
        shown = 0
        for member in missing:
            piece = member.mention + "\n"
            if len(listing) + len(piece) > 3800:
                listing += f"…и ещё {len(missing) - shown}"
                break
            listing += piece
            shown += 1
        embed = embeds.make(f"🔍 Не отреагировали ({len(missing)})", listing)
        embed.add_field(name="Сообщение", value=f"[Перейти]({target.jump_url})", inline=False)
        await interaction.followup.send(embed=embed)

    @wipe.command(name="stats", description="Кто чаще всех ходит на вайпы")
    @app_commands.describe(days="За сколько последних дней считать (по умолчанию 30)")
    @access("wipe")
    async def wipe_stats(self, interaction: discord.Interaction,
                         days: app_commands.Range[int, 1, 365] = 30):
        gid = interaction.guild.id
        since = int(now_ts()) - days * 86400
        db = self.bot.db

        total_row = await db.fetchone(
            "SELECT COUNT(*) AS n FROM wipe_events WHERE guild_id=? AND ts>=?", (gid, since)
        )
        events = total_row["n"] if total_row else 0
        if not events:
            await interaction.response.send_message(
                embed=embeds.info(f"За последние {days} дн. событий не было.", "📊 Явка на вайпы"),
                ephemeral=True,
            )
            return

        rows = await db.fetchall(
            "SELECT r.user_id AS user_id, "
            "SUM(CASE WHEN r.status='accepted' THEN 1 ELSE 0 END) AS came, "
            "SUM(CASE WHEN r.status='late' THEN 1 ELSE 0 END) AS late, "
            "SUM(CASE WHEN r.status='declined' THEN 1 ELSE 0 END) AS skipped "
            "FROM wipe_responses r JOIN wipe_events e ON e.message_id = r.message_id "
            "WHERE e.guild_id=? AND e.ts>=? "
            "GROUP BY r.user_id ORDER BY came DESC, late DESC LIMIT 15",
            (gid, since),
        )

        embed = embeds.make(f"📊 Явка на вайпы за {days} дн.")
        embed.add_field(name="Событий", value=str(events), inline=True)
        embed.add_field(name="Отметившихся", value=str(len(rows)), inline=True)
        if rows:
            lines = []
            for place, row in enumerate(rows, start=1):
                percent = row["came"] * 100 // events
                lines.append(
                    f"`{place:>2}.` <@{row['user_id']}> — ✅ {row['came']} · 🕒 {row['late']} · "
                    f"❌ {row['skipped']} · явка **{percent}%**"
                )
            embed.add_field(name="🏅 Топ участников", value="\n".join(lines)[:1024], inline=False)
        else:
            embed.add_field(name="🏅 Топ участников", value="Никто ещё не отметился.", inline=False)
        embed.set_footer(text=f"{config.FOOTER} • явка = «приду» от общего числа событий")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Wipe(bot))
''',
    'vex.cogs.automod': r'''"""Автомодерация: защита от нежелательных ссылок и инвайтов."""
import logging
import re
from datetime import timedelta
from time import time as now_ts

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, embeds
from ..checks import access

log = logging.getLogger("vex")

TLDS = (
    "com|net|org|ru|su|ua|by|kz|gg|io|me|tv|xyz|ly|cc|info|biz|pro|club|online|site|link|"
    "store|shop|app|dev|fun|top|vip|ws|gl|gd"
)
URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>()\[\]]+"
    r"|(?:discord\.gg|discord(?:app)?\.com/invite)/[^\s<>()\[\]]+"
    r"|\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+(?:" + TLDS + r")\b(?:/[^\s<>()\[\]]*)?",
    re.IGNORECASE,
)
STRIKE_WINDOW = 10 * 60  # секунд: сколько «живёт» нарушение


def extract_host(link):
    host = re.sub(r"^(?:https?://)?(?:www\.)?", "", link.strip().lower())
    host = host.split("/")[0].split("?")[0].split("#")[0]
    host = host.split("@")[-1].split(":")[0]
    return host


def normalize_domain(text):
    return extract_host(text).strip(".")


def find_violation(content, allowed):
    """Возвращает первую запрещённую ссылку в тексте или None."""
    for match in URL_RE.finditer(content):
        raw = match.group(0)
        host = extract_host(raw)
        if not host:
            continue
        if host in ("discord.com", "discordapp.com") and "/channels/" in raw.lower():
            continue  # ссылки на сообщения Discord
        if any(host == d or host.endswith("." + d) for d in allowed):
            continue
        return raw
    return None


class AutoMod(commands.Cog):
    automod = app_commands.Group(
        name="automod", description="Автомодерация ссылок", guild_only=True
    )

    def __init__(self, bot):
        self.bot = bot
        self.strikes = {}  # (guild_id, user_id) -> [timestamps]

    # ---- данные
    async def allowed_domains(self, guild_id):
        rows = await self.bot.db.fetchall("SELECT domain FROM allowed_domains WHERE guild_id=?", (guild_id,))
        return set(config.DEFAULT_ALLOWED_DOMAINS) | {r["domain"] for r in rows}

    async def is_exempt(self, message):
        member = message.author
        perms = member.guild_permissions
        if perms.administrator or perms.manage_messages:
            return True
        guild_id = message.guild.id
        bypass = await self.bot.db.get_targets(guild_id, "automod_bypass")
        if any(role.id in bypass for role in member.roles):
            return True
        ignored = await self.bot.db.get_targets(guild_id, "automod_ignore_channel")
        return message.channel.id in ignored

    # ---- проверка сообщений
    async def check_message(self, message):
        if message.guild is None or message.author.bot or not message.content:
            return
        if not isinstance(message.author, discord.Member):
            return
        if not URL_RE.search(message.content):
            return  # дёшево отсекаем почти все сообщения без обращения к базе

        guild_id = message.guild.id
        if await self.bot.db.get_setting(guild_id, "automod_enabled", "1") == "0":
            return
        if await self.is_exempt(message):
            return
        link = find_violation(message.content, await self.allowed_domains(guild_id))
        if link is None:
            return
        await self.punish(message, link)

    async def punish(self, message, link):
        guild = message.guild
        member = message.author
        db = self.bot.db

        deleted = True
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            deleted = False

        max_strikes = int(await db.get_setting(guild.id, "automod_strikes", "3"))
        timeout_minutes = int(await db.get_setting(guild.id, "automod_timeout", "10"))
        key = (guild.id, member.id)
        now = now_ts()
        history = [t for t in self.strikes.get(key, []) if now - t < STRIKE_WINDOW] + [now]
        self.strikes[key] = history

        await db.execute(
            "INSERT INTO automod_log(guild_id, user_id, channel_id, link, ts) VALUES(?,?,?,?,?)",
            (guild.id, member.id, message.channel.id, link[:200], int(now)),
        )
        await db.execute(  # храним последние 200 записей на сервер
            "DELETE FROM automod_log WHERE guild_id=? AND id NOT IN "
            "(SELECT id FROM automod_log WHERE guild_id=? ORDER BY id DESC LIMIT 200)",
            (guild.id, guild.id),
        )

        action = "Сообщение удалено" if deleted else "❗ Не удалось удалить (нет прав Manage Messages)"
        timed_out = False
        if len(history) >= max_strikes and timeout_minutes > 0:
            try:
                await member.timeout(timedelta(minutes=timeout_minutes), reason="VEX AutoMod: ссылки")
                timed_out = True
                self.strikes.pop(key, None)
                action += f" • тайм-аут на {timeout_minutes} мин."
            except (discord.Forbidden, discord.HTTPException):
                action += " • тайм-аут выдать не удалось (роль бота ниже участника)"

        try:
            warning = embeds.warn(
                f"{member.mention}, отправка ссылок здесь запрещена.\n"
                "Если ссылка нужна — напиши модераторам или открой тикет.",
                "Ссылка удалена",
            )
            if timed_out:
                warning.add_field(name="Наказание", value=f"Тайм-аут на {timeout_minutes} мин.")
            await message.channel.send(embed=warning, delete_after=10)
        except discord.HTTPException:
            pass

        log_embed = embeds.make("🛡️ AutoMod: нежелательная ссылка", color=config.COLOR_WARN)
        log_embed.add_field(name="Участник", value=f"{member.mention} (`{member.id}`)", inline=True)
        log_embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        log_embed.add_field(name="Ссылка", value=f"`{link[:200]}`", inline=False)
        log_embed.add_field(name="Действие", value=action, inline=False)
        log_embed.add_field(name="Нарушений за 10 мин", value=str(len(history)), inline=True)
        await self.bot.send_log(guild, log_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.check_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            await self.check_message(after)

    # ---- команды
    @automod.command(name="status", description="Текущие настройки автомодерации")
    @access("automod")
    async def status(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        db = self.bot.db
        enabled = await db.get_setting(gid, "automod_enabled", "1") != "0"
        strikes = await db.get_setting(gid, "automod_strikes", "3")
        timeout = await db.get_setting(gid, "automod_timeout", "10")
        domains = sorted(await self.allowed_domains(gid))
        bypass = await db.get_targets(gid, "automod_bypass")
        ignored = await db.get_targets(gid, "automod_ignore_channel")
        embed = embeds.make("🛡️ Автомодерация ссылок")
        embed.add_field(name="Состояние", value="🟢 Включена" if enabled else "🔴 Выключена", inline=True)
        embed.add_field(name="Тайм-аут", value=f"после {strikes} нарушений • {timeout} мин.", inline=True)
        embed.add_field(name="Разрешённые домены", value="\n".join(f"`{d}`" for d in domains)[:1000] or "—",
                        inline=False)
        embed.add_field(name="Игнорируемые роли",
                        value=" ".join(f"<@&{r}>" for r in bypass) or "— (модераторы с Manage Messages и админы не проверяются)",
                        inline=False)
        embed.add_field(name="Игнорируемые каналы", value=" ".join(f"<#{c}>" for c in ignored) or "—",
                        inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @automod.command(name="toggle", description="Включить или выключить автомодерацию")
    @app_commands.describe(enabled="True — включить, False — выключить")
    @access("automod")
    async def toggle(self, interaction: discord.Interaction, enabled: bool):
        await self.bot.db.set_setting(interaction.guild.id, "automod_enabled", "1" if enabled else "0")
        text = "Автомодерация включена." if enabled else "Автомодерация выключена."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @automod.command(name="allow", description="Разрешить домен (например youtube.com)")
    @app_commands.describe(domain="Домен или ссылка")
    @access("automod")
    async def allow(self, interaction: discord.Interaction, domain: str):
        domain = normalize_domain(domain)
        if "." not in domain:
            await interaction.response.send_message(embed=embeds.err("Это не похоже на домен."), ephemeral=True)
            return
        changed = await self.bot.db.execute(
            "INSERT OR IGNORE INTO allowed_domains(guild_id, domain) VALUES(?,?)", (interaction.guild.id, domain)
        )
        text = f"`{domain}` разрешён (вместе с поддоменами)." if changed else f"`{domain}` уже разрешён."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @automod.command(name="disallow", description="Убрать домен из разрешённых")
    @app_commands.describe(domain="Домен или ссылка")
    @access("automod")
    async def disallow(self, interaction: discord.Interaction, domain: str):
        domain = normalize_domain(domain)
        changed = await self.bot.db.execute(
            "DELETE FROM allowed_domains WHERE guild_id=? AND domain=?", (interaction.guild.id, domain)
        )
        if changed:
            text = f"`{domain}` больше не разрешён."
        elif domain in config.DEFAULT_ALLOWED_DOMAINS:
            text = f"`{domain}` — встроенный домен, его можно изменить только в `vex/config.py`."
        else:
            text = f"`{domain}` не был в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @automod.command(name="bypass", description="Роль, которую автомодерация не проверяет")
    @app_commands.describe(role="Роль", enabled="True — не проверять, False — снова проверять")
    @access("automod")
    async def bypass(self, interaction: discord.Interaction, role: discord.Role, enabled: bool = True):
        gid = interaction.guild.id
        if enabled:
            await self.bot.db.add_target(gid, "automod_bypass", role.id)
            text = f"{role.mention} теперь не проверяется."
        else:
            await self.bot.db.remove_target(gid, "automod_bypass", role.id)
            text = f"{role.mention} снова проверяется."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @automod.command(name="ignore_channel", description="Канал, где ссылки разрешены")
    @app_commands.describe(channel="Канал", enabled="True — разрешить ссылки, False — снова проверять")
    @access("automod")
    async def ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel,
                             enabled: bool = True):
        gid = interaction.guild.id
        if enabled:
            await self.bot.db.add_target(gid, "automod_ignore_channel", channel.id)
            text = f"В {channel.mention} ссылки разрешены."
        else:
            await self.bot.db.remove_target(gid, "automod_ignore_channel", channel.id)
            text = f"В {channel.mention} ссылки снова проверяются."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @automod.command(name="punishment", description="Сколько нарушений до тайм-аута и на сколько минут")
    @app_commands.describe(strikes="Нарушений за 10 минут до тайм-аута",
                           timeout_minutes="Длительность тайм-аута в минутах (0 — не выдавать)")
    @access("automod")
    async def punishment(self, interaction: discord.Interaction, strikes: app_commands.Range[int, 1, 10],
                         timeout_minutes: app_commands.Range[int, 0, 1440]):
        gid = interaction.guild.id
        await self.bot.db.set_setting(gid, "automod_strikes", strikes)
        await self.bot.db.set_setting(gid, "automod_timeout", timeout_minutes)
        text = (f"После **{strikes}** нарушений за 10 минут — тайм-аут на **{timeout_minutes}** мин."
                if timeout_minutes else "Тайм-ауты отключены, ссылки только удаляются.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
''',
    'vex.cogs.roles': r'''"""Роли: выдача/снятие командой с проверкой иерархии и авто-выдача при заходе."""
import discord
from discord import app_commands
from discord.ext import commands

from .. import config, embeds
from ..checks import access, is_admin

TARGET_CHOICES = [
    app_commands.Choice(name="Участники", value="member"),
    app_commands.Choice(name="Боты", value="bot"),
]


class RoleTools(commands.Cog):
    role = app_commands.Group(name="role", description="Управление ролями", guild_only=True)

    def __init__(self, bot):
        self.bot = bot

    async def check_assignable(self, interaction, member, role):
        """Текст ошибки или None, если менять эту роль можно."""
        guild = interaction.guild
        invoker = interaction.user
        if role.is_default():
            return "Роль @everyone менять нельзя."
        if role.managed:
            return "Эта роль управляется интеграцией (ботом или бустом) — вручную её не выдать."
        if role >= guild.me.top_role:
            return f"Роль {role.mention} выше моей высшей роли или равна ей. Подними роль VEX в настройках сервера."
        if is_admin(invoker):
            return None
        if role >= invoker.top_role:
            return "Эта роль не ниже твоей высшей роли — выдавать её нельзя."
        if member.id != invoker.id and member.top_role >= invoker.top_role:
            return "Нельзя менять роли участника, который не ниже тебя по иерархии."
        perms = role.permissions
        if perms.administrator or perms.manage_roles or perms.manage_guild:
            return "Роли с опасными правами может выдавать только администратор."
        allowed = await self.bot.db.get_targets(guild.id, "manageable")
        if allowed and role.id not in allowed:
            return "Эта роль не входит в список ролей, которые разрешено выдавать (`/role allowed`)."
        return None

    async def _change(self, interaction, member, role, reason, give):
        error = await self.check_assignable(interaction, member, role)
        if error:
            await interaction.response.send_message(embed=embeds.err(error), ephemeral=True)
            return
        has_role = role in member.roles
        if give and has_role:
            await interaction.response.send_message(
                embed=embeds.info(f"У {member.mention} уже есть {role.mention}."), ephemeral=True
            )
            return
        if not give and not has_role:
            await interaction.response.send_message(
                embed=embeds.info(f"У {member.mention} нет роли {role.mention}."), ephemeral=True
            )
            return

        audit = f"{interaction.user} через VEX" + (f": {reason}" if reason else "")
        try:
            if give:
                await member.add_roles(role, reason=audit)
            else:
                await member.remove_roles(role, reason=audit)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=embeds.err("У меня не хватает прав (Manage Roles) или роль выше моей."), ephemeral=True
            )
            return

        verb = "выдана" if give else "снята"
        text = f"Роль {role.mention} {verb}: {member.mention}"
        await interaction.response.send_message(
            embed=embeds.ok(text), allowed_mentions=discord.AllowedMentions.none()
        )

        log = embeds.make(f"🎭 Роль {verb}", color=config.COLOR_MAIN)
        log.add_field(name="Участник", value=member.mention, inline=True)
        log.add_field(name="Роль", value=role.mention, inline=True)
        log.add_field(name="Кто", value=interaction.user.mention, inline=True)
        if reason:
            log.add_field(name="Причина", value=reason[:500], inline=False)
        await self.bot.send_log(interaction.guild, log)

    @role.command(name="add", description="Выдать роль участнику")
    @app_commands.describe(member="Кому", role="Какую роль", reason="Причина (попадёт в журнал аудита)")
    @access("role")
    async def add(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role,
                  reason: str | None = None):
        await self._change(interaction, member, role, reason, give=True)

    @role.command(name="remove", description="Снять роль с участника")
    @app_commands.describe(member="С кого", role="Какую роль", reason="Причина (попадёт в журнал аудита)")
    @access("role")
    async def remove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role,
                     reason: str | None = None):
        await self._change(interaction, member, role, reason, give=False)

    @role.command(name="allow", description="Разрешить модераторам выдавать эту роль")
    @app_commands.describe(role="Роль")
    @access("role_admin")
    async def allow(self, interaction: discord.Interaction, role: discord.Role):
        added = await self.bot.db.add_target(interaction.guild.id, "manageable", role.id)
        text = f"{role.mention} добавлена в список выдаваемых." if added else f"{role.mention} уже в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @role.command(name="deny", description="Убрать роль из списка выдаваемых")
    @app_commands.describe(role="Роль")
    @access("role_admin")
    async def deny(self, interaction: discord.Interaction, role: discord.Role):
        removed = await self.bot.db.remove_target(interaction.guild.id, "manageable", role.id)
        text = f"{role.mention} убрана из списка." if removed else f"{role.mention} не была в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @role.command(name="allowed", description="Список ролей, которые разрешено выдавать")
    @access("role_admin")
    async def allowed(self, interaction: discord.Interaction):
        ids = await self.bot.db.get_targets(interaction.guild.id, "manageable")
        if ids:
            text = "\n".join(f"• <@&{i}>" for i in ids)
        else:
            text = ("Список пуст — модераторы могут выдавать любые роли ниже своей "
                    "(кроме ролей с опасными правами).")
        await interaction.response.send_message(embed=embeds.info(text, "🎭 Выдаваемые роли"), ephemeral=True)


class AutoRole(commands.Cog):
    autorole = app_commands.Group(name="autorole", description="Авто-выдача ролей при заходе", guild_only=True)

    def __init__(self, bot):
        self.bot = bot

    async def apply(self, member):
        kind = "autorole_bot" if member.bot else "autorole_member"
        ids = await self.bot.db.get_targets(member.guild.id, kind)
        me = member.guild.me
        roles = []
        for role_id in ids:
            role = member.guild.get_role(role_id)
            if role and not role.managed and role < me.top_role and role not in member.roles:
                roles.append(role)
        if not roles:
            return
        try:
            await member.add_roles(*roles, reason="VEX: авто-выдача ролей")
        except discord.HTTPException:
            return
        log = embeds.make("🎭 Авто-роль выдана", color=config.COLOR_MAIN)
        log.add_field(name="Участник", value=member.mention, inline=True)
        log.add_field(name="Роли", value=" ".join(r.mention for r in roles), inline=True)
        await self.bot.send_log(member.guild, log)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.pending:  # если включена проверка (screening) — ждём её завершения
            await self.apply(member)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.pending and not after.pending:
            await self.apply(after)

    @autorole.command(name="add", description="Добавить роль, выдаваемую при заходе")
    @app_commands.describe(role="Роль", target="Кому выдавать")
    @app_commands.choices(target=TARGET_CHOICES)
    @access("autorole")
    async def add(self, interaction: discord.Interaction, role: discord.Role,
                  target: app_commands.Choice[str]):
        if role.managed or role.is_default() or role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                embed=embeds.err("Эту роль я выдать не смогу: она выше моей, управляется интеграцией или это @everyone."),
                ephemeral=True,
            )
            return
        kind = "autorole_bot" if target.value == "bot" else "autorole_member"
        added = await self.bot.db.add_target(interaction.guild.id, kind, role.id)
        text = (f"{role.mention} будет выдаваться при заходе ({target.name.lower()})."
                if added else f"{role.mention} уже в списке.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @autorole.command(name="remove", description="Убрать роль из авто-выдачи")
    @app_commands.describe(role="Роль", target="Кому выдавалась")
    @app_commands.choices(target=TARGET_CHOICES)
    @access("autorole")
    async def remove(self, interaction: discord.Interaction, role: discord.Role,
                     target: app_commands.Choice[str]):
        kind = "autorole_bot" if target.value == "bot" else "autorole_member"
        removed = await self.bot.db.remove_target(interaction.guild.id, kind, role.id)
        text = f"{role.mention} убрана из авто-выдачи." if removed else f"{role.mention} не была в списке."
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @autorole.command(name="list", description="Какие роли выдаются при заходе")
    @access("autorole")
    async def list_roles(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        members = await self.bot.db.get_targets(gid, "autorole_member")
        bots = await self.bot.db.get_targets(gid, "autorole_bot")
        embed = embeds.make("🎭 Авто-выдача ролей")
        embed.add_field(name="Участникам", value=" ".join(f"<@&{i}>" for i in members) or "—", inline=False)
        embed.add_field(name="Ботам", value=" ".join(f"<@&{i}>" for i in bots) or "—", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RoleTools(bot))
    await bot.add_cog(AutoRole(bot))
''',
    'vex.cogs.staff': r'''"""Сообщения от имени бота: простой текст и полноценный конструктор эмбедов."""
import json
import re
from dataclasses import dataclass, field

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, embeds
from ..checks import access

URL_RE = re.compile(r"^https?://", re.IGNORECASE)
BUILDER_TIMEOUT = 900  # 15 минут на сборку сообщения


def parse_color(raw):
    """'#8B5CF6', '8b5cf6', 'purple', 'random' -> int. None, если не разобрали."""
    raw = (raw or "").strip().lower()
    if not raw:
        return None
    if raw == "random":
        return discord.Colour.random().value
    if raw in config.NAMED_COLORS:
        return config.NAMED_COLORS[raw]
    cleaned = raw.lstrip("#")
    if cleaned.startswith("0x"):
        cleaned = cleaned[2:]
    try:
        return int(cleaned, 16) & 0xFFFFFF
    except ValueError:
        return None


def valid_url(value, allow_attachment=False):
    """Пускаем только http/https (и attachment:// для вложений)."""
    if not value:
        return True
    if allow_attachment and value.startswith("attachment://"):
        return True
    return bool(URL_RE.match(value))


# --------------------------------------------------------------------------- черновик
@dataclass
class EmbedDraft:
    """Все поля эмбеда Discord в одном месте + текст вне эмбеда."""

    content: str = ""
    title: str = ""
    url: str = ""
    description: str = ""
    color: int = config.COLOR_MAIN
    author_name: str = ""
    author_icon: str = ""
    author_url: str = ""
    footer_text: str = ""
    footer_icon: str = ""
    thumbnail: str = ""
    image: str = ""
    timestamp: bool = False
    fields: list = field(default_factory=list)
    ping_role_id: int = 0

    # ---- вывод
    def has_embed(self):
        return any([self.title, self.description, self.author_name, self.footer_text,
                    self.thumbnail, self.image, self.fields])

    def is_empty(self):
        return not self.has_embed() and not self.content

    def to_embed(self):
        if not self.has_embed():
            return None
        embed = discord.Embed(
            title=self.title[:256] or None,
            url=self.url or None,
            description=self.description[:4000] or None,
            color=self.color,
        )
        if self.timestamp:
            embed.timestamp = discord.utils.utcnow()
        if self.author_name:
            embed.set_author(name=self.author_name[:256],
                             icon_url=self.author_icon or None,
                             url=self.author_url or None)
        if self.footer_text:
            embed.set_footer(text=self.footer_text[:2048], icon_url=self.footer_icon or None)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        if self.image:
            embed.set_image(url=self.image)
        for item in self.fields[:25]:
            embed.add_field(name=str(item.get("name", "—"))[:256],
                            value=str(item.get("value", "—"))[:1024],
                            inline=bool(item.get("inline")))
        return embed

    def full_content(self):
        """Текст сообщения вместе с пингом роли, если он выбран."""
        parts = []
        if self.ping_role_id:
            parts.append(f"<@&{self.ping_role_id}>")
        if self.content:
            parts.append(self.content)
        return " ".join(parts)[:2000] or None

    # ---- JSON (формат Discord: {"content": ..., "embeds": [ {...} ]})
    def to_json(self):
        data = {}
        if self.content:
            data["content"] = self.content
        body = {}
        if self.title:
            body["title"] = self.title
        if self.url:
            body["url"] = self.url
        if self.description:
            body["description"] = self.description
        body["color"] = self.color
        if self.timestamp:
            body["timestamp"] = discord.utils.utcnow().isoformat()
        if self.author_name:
            author = {"name": self.author_name}
            if self.author_icon:
                author["icon_url"] = self.author_icon
            if self.author_url:
                author["url"] = self.author_url
            body["author"] = author
        if self.footer_text:
            footer = {"text": self.footer_text}
            if self.footer_icon:
                footer["icon_url"] = self.footer_icon
            body["footer"] = footer
        if self.thumbnail:
            body["thumbnail"] = {"url": self.thumbnail}
        if self.image:
            body["image"] = {"url": self.image}
        if self.fields:
            body["fields"] = [
                {"name": f.get("name", "—"), "value": f.get("value", "—"),
                 "inline": bool(f.get("inline"))}
                for f in self.fields
            ]
        if self.has_embed():
            data["embeds"] = [body]
        if self.ping_role_id:
            data["ping_role_id"] = self.ping_role_id
        return data

    def to_json_text(self):
        return json.dumps(self.to_json(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, data):
        """Понимает и {'content':..,'embeds':[..]}, и просто словарь эмбеда."""
        if not isinstance(data, dict):
            raise ValueError("Ожидается JSON-объект")
        draft = cls()
        draft.content = str(data.get("content") or "")[:2000]
        try:
            draft.ping_role_id = int(data.get("ping_role_id") or 0)
        except (TypeError, ValueError):
            draft.ping_role_id = 0

        body = None
        if isinstance(data.get("embeds"), list) and data["embeds"]:
            body = data["embeds"][0]
        elif isinstance(data.get("embed"), dict):
            body = data["embed"]
        elif any(k in data for k in ("title", "description", "fields", "author", "footer",
                                     "image", "thumbnail")):
            body = data
        if not isinstance(body, dict):
            return draft

        draft.title = str(body.get("title") or "")[:256]
        draft.url = str(body.get("url") or "")
        draft.description = str(body.get("description") or "")[:4000]
        color = body.get("color")
        if isinstance(color, str):
            draft.color = parse_color(color) or config.COLOR_MAIN
        elif isinstance(color, int):
            draft.color = color & 0xFFFFFF
        draft.timestamp = bool(body.get("timestamp"))

        author = body.get("author") or {}
        if isinstance(author, dict):
            draft.author_name = str(author.get("name") or "")[:256]
            draft.author_icon = str(author.get("icon_url") or author.get("iconURL") or "")
            draft.author_url = str(author.get("url") or "")
        footer = body.get("footer") or {}
        if isinstance(footer, dict):
            draft.footer_text = str(footer.get("text") or "")[:2048]
            draft.footer_icon = str(footer.get("icon_url") or footer.get("iconURL") or "")
        thumb = body.get("thumbnail") or {}
        if isinstance(thumb, dict):
            draft.thumbnail = str(thumb.get("url") or "")
        elif isinstance(thumb, str):
            draft.thumbnail = thumb
        image = body.get("image") or {}
        if isinstance(image, dict):
            draft.image = str(image.get("url") or "")
        elif isinstance(image, str):
            draft.image = image

        for item in (body.get("fields") or [])[:25]:
            if isinstance(item, dict) and item.get("name") and item.get("value"):
                draft.fields.append({
                    "name": str(item["name"])[:256],
                    "value": str(item["value"])[:1024],
                    "inline": bool(item.get("inline")),
                })
        return draft

    @classmethod
    def from_message(cls, message):
        draft = cls()
        draft.content = (message.content or "")[:2000]
        if message.embeds:
            source = message.embeds[0].to_dict()
            loaded = cls.from_json({"embeds": [source]})
            loaded.content = draft.content
            return loaded
        return draft


# --------------------------------------------------------------------------- модалки
class MainModal(discord.ui.Modal, title="Основное"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        draft = view.draft
        self.f_title = discord.ui.TextInput(label="Заголовок", required=False, max_length=256,
                                            default=draft.title or None)
        self.f_url = discord.ui.TextInput(label="Ссылка заголовка", required=False,
                                          placeholder="https://…", default=draft.url or None)
        self.f_desc = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph,
                                           required=False, max_length=4000,
                                           default=draft.description or None)
        self.f_color = discord.ui.TextInput(
            label="Цвет", required=False, max_length=20,
            placeholder="#8B5CF6, purple, green, red, orange, blue, blurple, random",
            default=f"#{draft.color:06X}",
        )
        for item in (self.f_title, self.f_url, self.f_desc, self.f_color):
            self.add_item(item)

    async def on_submit(self, interaction):
        draft = self.view_ref.draft
        url = str(self.f_url).strip()
        if not valid_url(url):
            await self.view_ref.fail(interaction, "Ссылка заголовка должна начинаться с http:// или https://")
            return
        color = parse_color(str(self.f_color))
        if str(self.f_color).strip() and color is None:
            await self.view_ref.fail(interaction, "Не понял цвет. Примеры: `#8B5CF6`, `purple`, `random`.")
            return
        draft.title = str(self.f_title).strip()
        draft.url = url
        draft.description = str(self.f_desc)
        if color is not None:
            draft.color = color
        await self.view_ref.refresh(interaction)


class AuthorModal(discord.ui.Modal, title="Автор эмбеда"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        draft = view.draft
        self.f_name = discord.ui.TextInput(label="Имя", required=False, max_length=256,
                                           default=draft.author_name or None)
        self.f_icon = discord.ui.TextInput(label="Иконка (URL)", required=False,
                                           placeholder="https://…", default=draft.author_icon or None)
        self.f_url = discord.ui.TextInput(label="Ссылка", required=False,
                                          placeholder="https://…", default=draft.author_url or None)
        for item in (self.f_name, self.f_icon, self.f_url):
            self.add_item(item)

    async def on_submit(self, interaction):
        icon, url = str(self.f_icon).strip(), str(self.f_url).strip()
        if not valid_url(icon) or not valid_url(url):
            await self.view_ref.fail(interaction, "Ссылки должны начинаться с http:// или https://")
            return
        draft = self.view_ref.draft
        draft.author_name = str(self.f_name).strip()
        draft.author_icon = icon
        draft.author_url = url
        await self.view_ref.refresh(interaction)


class FooterModal(discord.ui.Modal, title="Футер эмбеда"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        draft = view.draft
        self.f_text = discord.ui.TextInput(label="Текст", required=False, max_length=2048,
                                           default=draft.footer_text or None)
        self.f_icon = discord.ui.TextInput(label="Иконка (URL)", required=False,
                                           placeholder="https://…", default=draft.footer_icon or None)
        self.f_time = discord.ui.TextInput(
            label="Показывать время? (да/нет)", required=False, max_length=5,
            default="да" if draft.timestamp else "нет",
        )
        for item in (self.f_text, self.f_icon, self.f_time):
            self.add_item(item)

    async def on_submit(self, interaction):
        icon = str(self.f_icon).strip()
        if not valid_url(icon):
            await self.view_ref.fail(interaction, "Иконка футера должна быть http/https ссылкой.")
            return
        draft = self.view_ref.draft
        draft.footer_text = str(self.f_text).strip()
        draft.footer_icon = icon
        draft.timestamp = str(self.f_time).strip().lower() in ("да", "yes", "true", "1", "+")
        await self.view_ref.refresh(interaction)


class ImagesModal(discord.ui.Modal, title="Картинки"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        draft = view.draft
        self.f_thumb = discord.ui.TextInput(label="Миниатюра (thumbnail)", required=False,
                                            placeholder="https://…", default=draft.thumbnail or None)
        self.f_image = discord.ui.TextInput(label="Большая картинка (image)", required=False,
                                            placeholder="https://…", default=draft.image or None)
        for item in (self.f_thumb, self.f_image):
            self.add_item(item)

    async def on_submit(self, interaction):
        thumb, image = str(self.f_thumb).strip(), str(self.f_image).strip()
        if not valid_url(thumb, True) or not valid_url(image, True):
            await self.view_ref.fail(interaction, "Ссылки на картинки должны быть http/https.")
            return
        draft = self.view_ref.draft
        draft.thumbnail = thumb
        draft.image = image
        await self.view_ref.refresh(interaction)


class ContentModal(discord.ui.Modal, title="Текст вне эмбеда"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        self.f_content = discord.ui.TextInput(
            label="Текст (до 2000 символов)", style=discord.TextStyle.paragraph,
            required=False, max_length=2000, default=view.draft.content or None,
        )
        self.add_item(self.f_content)

    async def on_submit(self, interaction):
        self.view_ref.draft.content = str(self.f_content)
        await self.view_ref.refresh(interaction)


class FieldModal(discord.ui.Modal):
    def __init__(self, view, index=None):
        super().__init__(title="Поле эмбеда" if index is None else "Изменить поле")
        self.view_ref = view
        self.index = index
        current = view.draft.fields[index] if index is not None else {}
        self.f_name = discord.ui.TextInput(label="Название", max_length=256,
                                           default=current.get("name") or None)
        self.f_value = discord.ui.TextInput(label="Текст", style=discord.TextStyle.paragraph,
                                            max_length=1024, default=current.get("value") or None)
        self.f_inline = discord.ui.TextInput(
            label="В строку с другими? (да/нет)", required=False, max_length=5,
            default="да" if current.get("inline") else "нет",
        )
        for item in (self.f_name, self.f_value, self.f_inline):
            self.add_item(item)

    async def on_submit(self, interaction):
        draft = self.view_ref.draft
        item = {
            "name": str(self.f_name).strip()[:256],
            "value": str(self.f_value)[:1024],
            "inline": str(self.f_inline).strip().lower() in ("да", "yes", "true", "1", "+"),
        }
        if self.index is None:
            if len(draft.fields) >= 25:
                await self.view_ref.fail(interaction, "В эмбеде может быть максимум 25 полей.")
                return
            draft.fields.append(item)
        else:
            draft.fields[self.index] = item
        await self.view_ref.refresh(interaction)


class JsonModal(discord.ui.Modal, title="JSON эмбеда"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        self.f_json = discord.ui.TextInput(
            label="Вставь JSON (заменит текущий черновик)",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            placeholder='{"content": "", "embeds": [{"title": "Привет", "description": "Текст"}]}',
        )
        self.add_item(self.f_json)

    async def on_submit(self, interaction):
        try:
            data = json.loads(str(self.f_json))
            draft = EmbedDraft.from_json(data)
        except (ValueError, TypeError) as exc:
            await self.view_ref.fail(interaction, f"Не разобрал JSON: `{exc}`")
            return
        self.view_ref.draft = draft
        await self.view_ref.refresh(interaction)


class TemplateNameModal(discord.ui.Modal, title="Сохранить как шаблон"):
    def __init__(self, view):
        super().__init__()
        self.view_ref = view
        self.f_name = discord.ui.TextInput(label="Название шаблона", max_length=64,
                                           placeholder="например: анонс-вайпа")
        self.add_item(self.f_name)

    async def on_submit(self, interaction):
        name = str(self.f_name).strip().lower()[:64]
        if not name:
            await self.view_ref.fail(interaction, "Название шаблона не может быть пустым.")
            return
        await self.view_ref.cog.bot.db.save_template(
            interaction.guild.id, name, self.view_ref.draft.to_json(), interaction.user.id
        )
        await self.view_ref.refresh(interaction, note=f"💾 Шаблон **{name}** сохранён.")


class TemplateJsonModal(discord.ui.Modal, title="Шаблон из JSON"):
    def __init__(self, cog, name):
        super().__init__()
        self.cog = cog
        self.name = name
        self.f_json = discord.ui.TextInput(
            label="JSON шаблона", style=discord.TextStyle.paragraph, max_length=4000,
            placeholder='{"content": "", "embeds": [{"title": "Заголовок"}]}',
        )
        self.add_item(self.f_json)

    async def on_submit(self, interaction):
        try:
            draft = EmbedDraft.from_json(json.loads(str(self.f_json)))
        except (ValueError, TypeError) as exc:
            await interaction.response.send_message(
                embed=embeds.err(f"Не разобрал JSON: `{exc}`"), ephemeral=True
            )
            return
        await self.cog.bot.db.save_template(
            interaction.guild.id, self.name, draft.to_json(), interaction.user.id
        )
        await interaction.response.send_message(
            embed=embeds.ok(f"Шаблон **{self.name}** сохранён."), ephemeral=True
        )


# --------------------------------------------------------------------------- подменю
class FieldsView(discord.ui.View):
    """Подменю полей: живёт в том же ephemeral-сообщении, что и конструктор."""

    def __init__(self, parent):
        super().__init__(timeout=BUILDER_TIMEOUT)
        self.parent = parent
        self.draft = parent.draft
        self.cog = parent.cog
        self.selected = None
        options = [
            discord.SelectOption(label=f"{i + 1}. {f['name'][:60]}", value=str(i))
            for i, f in enumerate(self.draft.fields[:25])
        ]
        if options:
            select = discord.ui.Select(placeholder="Выбери поле…", options=options, row=0)
            select.callback = self._on_select
            self.add_item(select)

    async def interaction_check(self, interaction):
        return await self.parent.interaction_check(interaction)

    async def _on_select(self, interaction):
        self.selected = int(interaction.data["values"][0])
        await self.refresh(interaction)

    def summary(self):
        if not self.draft.fields:
            text = "Полей пока нет."
        else:
            lines = []
            for i, f in enumerate(self.draft.fields):
                mark = "▶️" if i == self.selected else "  "
                flag = " (в строку)" if f.get("inline") else ""
                lines.append(f"{mark} **{i + 1}. {f['name']}**{flag}\n└ {f['value'][:80]}")
            text = "\n".join(lines)[:3800]
        return embeds.info(text, "📋 Поля эмбеда")

    async def refresh(self, interaction, note=None):
        view = FieldsView(self.parent)
        view.selected = self.selected
        embed = view.summary()
        if note:
            embed.add_field(name="​", value=note, inline=False)
        await interaction.response.edit_message(embeds=[embed], view=view)

    async def fail(self, interaction, text):
        await interaction.response.send_message(embed=embeds.err(text), ephemeral=True)

    @discord.ui.button(label="Добавить", emoji="➕", style=discord.ButtonStyle.success, row=1)
    async def add_field(self, interaction, button):
        await interaction.response.send_modal(FieldModal(self))

    @discord.ui.button(label="Изменить", emoji="✏️", style=discord.ButtonStyle.primary, row=1)
    async def edit_field(self, interaction, button):
        if self.selected is None or self.selected >= len(self.draft.fields):
            await self.fail(interaction, "Сначала выбери поле в меню.")
            return
        await interaction.response.send_modal(FieldModal(self, self.selected))

    @discord.ui.button(label="Удалить", emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def delete_field(self, interaction, button):
        if self.selected is None or self.selected >= len(self.draft.fields):
            await self.fail(interaction, "Сначала выбери поле в меню.")
            return
        removed = self.draft.fields.pop(self.selected)
        self.selected = None
        await self.refresh(interaction, note=f"🗑️ Поле «{removed['name']}» удалено.")

    @discord.ui.button(label="Назад", emoji="⬅️", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction, button):
        await self.parent.refresh(interaction)


class ContentView(discord.ui.View):
    """Подменю «текст вне эмбеда»: сам текст и роль для пинга."""

    def __init__(self, parent):
        super().__init__(timeout=BUILDER_TIMEOUT)
        self.parent = parent
        self.draft = parent.draft
        self.cog = parent.cog
        select = discord.ui.RoleSelect(placeholder="Роль для пинга (необязательно)…", row=0,
                                       min_values=0, max_values=1)
        select.callback = self._on_role
        self.add_item(select)

    async def interaction_check(self, interaction):
        return await self.parent.interaction_check(interaction)

    async def _on_role(self, interaction):
        values = interaction.data.get("values") or []
        self.draft.ping_role_id = int(values[0]) if values else 0
        await self.refresh(interaction)

    def summary(self):
        ping = f"<@&{self.draft.ping_role_id}>" if self.draft.ping_role_id else "—"
        text = (f"**Текст:**\n{self.draft.content or '—'}\n\n**Пинг роли:** {ping}")
        return embeds.info(text[:3800], "💬 Текст вне эмбеда")

    async def refresh(self, interaction, note=None):
        view = ContentView(self.parent)
        embed = view.summary()
        if note:
            embed.add_field(name="​", value=note, inline=False)
        await interaction.response.edit_message(embeds=[embed], view=view)

    async def fail(self, interaction, text):
        await interaction.response.send_message(embed=embeds.err(text), ephemeral=True)

    @discord.ui.button(label="Изменить текст", emoji="✏️", style=discord.ButtonStyle.primary, row=1)
    async def edit_text(self, interaction, button):
        await interaction.response.send_modal(ContentModal(self))

    @discord.ui.button(label="Очистить", emoji="🧹", style=discord.ButtonStyle.secondary, row=1)
    async def clear_text(self, interaction, button):
        self.draft.content = ""
        self.draft.ping_role_id = 0
        await self.refresh(interaction, note="🧹 Текст и пинг очищены.")

    @discord.ui.button(label="Назад", emoji="⬅️", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction, button):
        await self.parent.refresh(interaction)


# --------------------------------------------------------------------------- конструктор
class BuilderView(discord.ui.View):
    def __init__(self, cog, author_id, draft, channel, attachment=None, edit_target=None):
        super().__init__(timeout=BUILDER_TIMEOUT)
        self.cog = cog
        self.author_id = author_id
        self.draft = draft
        self.channel = channel
        self.attachment = attachment
        self.edit_target = edit_target  # сообщение бота, которое правим

        picker = discord.ui.ChannelSelect(
            placeholder="Куда отправить…", row=2, min_values=0, max_values=1,
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        )
        picker.callback = self._on_channel
        self.add_item(picker)
        if edit_target is not None:
            picker.disabled = True
            self.send.label = "Сохранить изменения"

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                embed=embeds.err("Это чужой конструктор — вызови `/say embed` сам."), ephemeral=True
            )
            return False
        return True

    async def _on_channel(self, interaction):
        values = interaction.data.get("values") or []
        if values:
            picked = interaction.guild.get_channel(int(values[0]))
            if picked is not None:
                self.channel = picked
        await self.refresh(interaction)

    # ---- отрисовка
    def status_embed(self, note=None):
        draft = self.draft
        where = self.channel.mention if self.channel else "— не выбран —"
        if self.edit_target is not None:
            where = f"правим [сообщение]({self.edit_target.jump_url})"
        ping = f" · пинг <@&{draft.ping_role_id}>" if draft.ping_role_id else ""
        lines = [
            f"**Куда:** {where}{ping}",
            f"**Цвет:** `#{draft.color:06X}` · **Полей:** {len(draft.fields)} · "
            f"**Время:** {'да' if draft.timestamp else 'нет'}",
        ]
        if draft.content:
            lines.append(f"**Текст вне эмбеда:** {draft.content[:120]}")
        if self.attachment is not None:
            lines.append(f"**Вложение:** `{self.attachment.filename}`")
        if note:
            lines.append(f"\n{note}")
        embed = embeds.make("🛠️ Конструктор сообщения", "\n".join(lines))
        embed.set_footer(text=f"{config.FOOTER} • предпросмотр ниже")
        return embed

    def preview(self, note=None):
        result = [self.status_embed(note)]
        body = self.draft.to_embed()
        if body is not None:
            result.append(body)
        return result

    async def refresh(self, interaction, note=None):
        await interaction.response.edit_message(embeds=self.preview(note), view=self)

    async def fail(self, interaction, text):
        await interaction.response.send_message(embed=embeds.err(text), ephemeral=True)

    # ---- кнопки: ряд 0
    @discord.ui.button(label="Основное", emoji="📝", style=discord.ButtonStyle.primary, row=0)
    async def main_btn(self, interaction, button):
        await interaction.response.send_modal(MainModal(self))

    @discord.ui.button(label="Автор", emoji="👤", style=discord.ButtonStyle.secondary, row=0)
    async def author_btn(self, interaction, button):
        await interaction.response.send_modal(AuthorModal(self))

    @discord.ui.button(label="Футер", emoji="🔻", style=discord.ButtonStyle.secondary, row=0)
    async def footer_btn(self, interaction, button):
        await interaction.response.send_modal(FooterModal(self))

    @discord.ui.button(label="Картинки", emoji="🖼️", style=discord.ButtonStyle.secondary, row=0)
    async def images_btn(self, interaction, button):
        await interaction.response.send_modal(ImagesModal(self))

    @discord.ui.button(label="Поля", emoji="📋", style=discord.ButtonStyle.secondary, row=0)
    async def fields_btn(self, interaction, button):
        view = FieldsView(self)
        await interaction.response.edit_message(embeds=[view.summary()], view=view)

    # ---- кнопки: ряд 1
    @discord.ui.button(label="Текст вне эмбеда", emoji="💬", style=discord.ButtonStyle.secondary, row=1)
    async def content_btn(self, interaction, button):
        view = ContentView(self)
        await interaction.response.edit_message(embeds=[view.summary()], view=view)

    @discord.ui.button(label="Вставить JSON", emoji="🧩", style=discord.ButtonStyle.secondary, row=1)
    async def json_btn(self, interaction, button):
        await interaction.response.send_modal(JsonModal(self))

    @discord.ui.button(label="Показать JSON", emoji="👁️", style=discord.ButtonStyle.secondary, row=1)
    async def show_json_btn(self, interaction, button):
        text = self.draft.to_json_text()
        if len(text) > 1900:
            text = text[:1900] + "\n…"
        await interaction.response.send_message(
            embed=embeds.info(f"```json\n{text}\n```", "🧩 Текущий JSON"), ephemeral=True
        )

    # ---- кнопки: ряд 3
    @discord.ui.button(label="Отправить", emoji="✅", style=discord.ButtonStyle.success, row=3)
    async def send(self, interaction, button):
        await self.cog.deliver(interaction, self)

    @discord.ui.button(label="Сохранить как шаблон", emoji="💾", style=discord.ButtonStyle.primary, row=3)
    async def save_btn(self, interaction, button):
        if self.draft.is_empty():
            await self.fail(interaction, "Нечего сохранять — черновик пуст.")
            return
        await interaction.response.send_modal(TemplateNameModal(self))

    @discord.ui.button(label="Сбросить", emoji="♻️", style=discord.ButtonStyle.secondary, row=3)
    async def reset_btn(self, interaction, button):
        self.draft = EmbedDraft()
        await self.refresh(interaction, note="♻️ Черновик очищен.")

    @discord.ui.button(label="Отмена", emoji="✖️", style=discord.ButtonStyle.danger, row=3)
    async def cancel_btn(self, interaction, button):
        await interaction.response.edit_message(
            embeds=[embeds.info("Конструктор закрыт, ничего не отправлено.")], view=None
        )
        self.stop()


# --------------------------------------------------------------------------- простое /say plain
class SayModal(discord.ui.Modal, title="Сообщение от имени VEX"):
    def __init__(self, cog, channel, reply_to, attachment):
        super().__init__()
        self.cog = cog
        self.channel = channel
        self.reply_to = reply_to
        self.attachment = attachment
        self.body = discord.ui.TextInput(
            label="Текст сообщения", style=discord.TextStyle.paragraph,
            required=True, max_length=2000,
        )
        self.add_item(self.body)

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True)
        text = str(self.body)

        file = None
        if self.attachment is not None:
            try:
                file = await self.attachment.to_file()
            except discord.HTTPException:
                file = None

        reference = None
        if self.reply_to:
            try:
                reference = await self.channel.fetch_message(self.reply_to)
            except (discord.NotFound, discord.Forbidden):
                reference = None

        mentions = discord.AllowedMentions(users=True, roles=True, everyone=False,
                                           replied_user=False)
        try:
            sent = await self.channel.send(content=text, file=file, reference=reference,
                                           allowed_mentions=mentions)
        except discord.Forbidden:
            await interaction.followup.send(
                embed=embeds.err(f"У меня нет прав писать в {self.channel.mention}."), ephemeral=True
            )
            return

        await self.cog.log_message(interaction, self.channel, sent, text, action="отправлено")
        await interaction.followup.send(
            embed=embeds.ok(f"Отправлено в {self.channel.mention}."), ephemeral=True
        )


# --------------------------------------------------------------------------- модуль
class Staff(commands.Cog):
    say = app_commands.Group(name="say", description="Сообщения от имени бота", guild_only=True)
    template = app_commands.Group(name="template", description="Шаблоны эмбедов", parent=say)

    def __init__(self, bot):
        self.bot = bot

    # ---- общее
    def check_channel(self, interaction, channel):
        """Проверяет, что в канал вообще можно писать. Возвращает канал или None."""
        channel = channel or interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return None
        if not channel.permissions_for(interaction.guild.me).send_messages:
            return None
        return channel

    async def log_message(self, interaction, channel, message, text, action="отправлено"):
        """Для участников сообщение анонимно, но модерация видит, кто его отправил."""
        entry = embeds.make("🕵️ Сообщение от имени бота", color=config.COLOR_MAIN)
        entry.add_field(name="Действие", value=action, inline=True)
        entry.add_field(name="Отправил",
                        value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=True)
        entry.add_field(name="Канал", value=channel.mention, inline=True)
        if message is not None:
            entry.add_field(name="Сообщение", value=f"[Перейти]({message.jump_url})", inline=True)
        entry.add_field(name="Текст", value=(text or "—")[:1000], inline=False)
        await self.bot.send_log(interaction.guild, entry)

    async def deliver(self, interaction, view):
        """Отправка или сохранение из конструктора."""
        draft = view.draft
        if draft.is_empty():
            await view.fail(interaction, "Сообщение пустое — заполни хотя бы текст или описание.")
            return
        channel = view.channel
        if channel is None:
            await view.fail(interaction, "Выбери канал в меню ниже.")
            return
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await view.fail(interaction, f"У меня нет прав писать в {channel.mention}.")
            return

        await interaction.response.defer(ephemeral=True)
        embed = draft.to_embed()
        content = draft.full_content()
        mentions = discord.AllowedMentions(users=True, roles=True, everyone=False)

        file = None
        if view.attachment is not None:
            try:
                file = await view.attachment.to_file()
            except discord.HTTPException:
                file = None

        try:
            if view.edit_target is not None:
                await view.edit_target.edit(content=content, embed=embed,
                                            allowed_mentions=mentions)
                sent = view.edit_target
                action = "отредактировано"
            else:
                kwargs = {"content": content, "embed": embed, "allowed_mentions": mentions}
                if file is not None:
                    kwargs["file"] = file
                sent = await channel.send(**kwargs)
                action = "отправлено"
        except discord.Forbidden:
            await interaction.followup.send(
                embed=embeds.err(f"У меня нет прав писать в {channel.mention}."), ephemeral=True
            )
            return
        except discord.HTTPException as exc:
            await interaction.followup.send(
                embed=embeds.err(f"Discord отклонил сообщение: `{exc.text or exc}`"), ephemeral=True
            )
            return

        summary = draft.content or draft.title or draft.description or "—"
        await self.log_message(interaction, channel, sent, summary, action=action)
        await interaction.edit_original_response(
            embeds=[embeds.ok(f"{action.capitalize()}: [перейти]({sent.jump_url})", "Готово")],
            view=None,
        )
        view.stop()

    async def open_builder(self, interaction, draft, channel, attachment=None, edit_target=None):
        view = BuilderView(self, interaction.user.id, draft, channel, attachment, edit_target)
        await interaction.response.send_message(embeds=view.preview(), view=view, ephemeral=True)

    async def template_names(self, interaction, current):
        rows = await self.bot.db.list_templates(interaction.guild.id)
        current = (current or "").lower()
        return [
            app_commands.Choice(name=r["name"], value=r["name"])
            for r in rows if current in r["name"].lower()
        ][:25]

    # ---- команды
    @say.command(name="embed", description="Открыть конструктор сообщения с эмбедом")
    @app_commands.describe(channel="Куда отправить (по умолчанию — текущий канал)",
                           template="Начать с сохранённого шаблона",
                           attachment="Прикрепить файл или картинку")
    @app_commands.autocomplete(template=template_names)
    @access("say")
    async def say_embed(self, interaction: discord.Interaction,
                        channel: discord.TextChannel | None = None,
                        template: str | None = None,
                        attachment: discord.Attachment | None = None):
        target = self.check_channel(interaction, channel)
        if target is None:
            await interaction.response.send_message(
                embed=embeds.err("Выбранный канал недоступен для записи."), ephemeral=True
            )
            return
        draft = EmbedDraft()
        if template:
            payload = await self.bot.db.load_template(interaction.guild.id, template.lower())
            if payload is None:
                await interaction.response.send_message(
                    embed=embeds.err(f"Шаблон **{template}** не найден."), ephemeral=True
                )
                return
            draft = EmbedDraft.from_json(payload)
        if attachment is not None and (attachment.content_type or "").startswith("image/"):
            draft.image = f"attachment://{attachment.filename}"
        await self.open_builder(interaction, draft, target, attachment)

    @say.command(name="plain", description="Быстрое текстовое сообщение без эмбеда")
    @app_commands.describe(channel="Куда отправить (по умолчанию — текущий канал)",
                           reply_to="ID сообщения, на которое ответить",
                           attachment="Прикрепить файл или картинку")
    @access("say")
    async def say_plain(self, interaction: discord.Interaction,
                        channel: discord.TextChannel | None = None,
                        reply_to: str | None = None,
                        attachment: discord.Attachment | None = None):
        target = self.check_channel(interaction, channel)
        if target is None:
            await interaction.response.send_message(
                embed=embeds.err("Выбранный канал недоступен для записи."), ephemeral=True
            )
            return
        reply_id = None
        if reply_to:
            if not reply_to.strip().isdigit():
                await interaction.response.send_message(
                    embed=embeds.err("`reply_to` — это числовой ID сообщения."), ephemeral=True
                )
                return
            reply_id = int(reply_to.strip())
        await interaction.response.send_modal(SayModal(self, target, reply_id, attachment))

    @say.command(name="raw", description="Отправить сообщение сразу из готового JSON")
    @app_commands.describe(data="JSON вида {\"content\": \"…\", \"embeds\": [{…}]}",
                           channel="Куда отправить")
    @access("say")
    async def say_raw(self, interaction: discord.Interaction, data: str,
                      channel: discord.TextChannel | None = None):
        target = self.check_channel(interaction, channel)
        if target is None:
            await interaction.response.send_message(
                embed=embeds.err("Выбранный канал недоступен для записи."), ephemeral=True
            )
            return
        try:
            draft = EmbedDraft.from_json(json.loads(data))
        except (ValueError, TypeError) as exc:
            await interaction.response.send_message(
                embed=embeds.err(f"Не разобрал JSON: `{exc}`"), ephemeral=True
            )
            return
        if draft.is_empty():
            await interaction.response.send_message(
                embed=embeds.err("В этом JSON нечего отправлять."), ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        try:
            sent = await target.send(
                content=draft.full_content(), embed=draft.to_embed(),
                allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=False),
            )
        except discord.HTTPException as exc:
            await interaction.followup.send(
                embed=embeds.err(f"Discord отклонил сообщение: `{exc.text or exc}`"), ephemeral=True
            )
            return
        await self.log_message(interaction, target, sent,
                               draft.content or draft.title or draft.description)
        await interaction.followup.send(
            embed=embeds.ok(f"Отправлено: [перейти]({sent.jump_url})"), ephemeral=True
        )

    @say.command(name="edit", description="Изменить сообщение, отправленное ботом")
    @app_commands.describe(message_id="ID сообщения бота", channel="Канал с этим сообщением")
    @access("say")
    async def say_edit(self, interaction: discord.Interaction, message_id: str,
                       channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        if not message_id.strip().isdigit():
            await interaction.response.send_message(
                embed=embeds.err("`message_id` — это числовой ID сообщения."), ephemeral=True
            )
            return
        try:
            message = await target.fetch_message(int(message_id.strip()))
        except (discord.NotFound, discord.Forbidden):
            await interaction.response.send_message(
                embed=embeds.err("Не нашёл сообщение в этом канале."), ephemeral=True
            )
            return
        if message.author.id != self.bot.user.id:
            await interaction.response.send_message(
                embed=embeds.err("Редактировать можно только сообщения, отправленные ботом."),
                ephemeral=True,
            )
            return
        await self.open_builder(interaction, EmbedDraft.from_message(message), target,
                                edit_target=message)

    # ---- шаблоны
    @template.command(name="save", description="Сохранить шаблон эмбеда из JSON")
    @app_commands.describe(name="Название шаблона")
    @access("say")
    async def template_save(self, interaction: discord.Interaction,
                            name: app_commands.Range[str, 1, 64]):
        await interaction.response.send_modal(TemplateJsonModal(self, name.strip().lower()))

    @template.command(name="load", description="Открыть конструктор с сохранённым шаблоном")
    @app_commands.describe(name="Название шаблона", channel="Куда отправлять")
    @app_commands.autocomplete(name=template_names)
    @access("say")
    async def template_load(self, interaction: discord.Interaction, name: str,
                            channel: discord.TextChannel | None = None):
        payload = await self.bot.db.load_template(interaction.guild.id, name.lower())
        if payload is None:
            await interaction.response.send_message(
                embed=embeds.err(f"Шаблон **{name}** не найден."), ephemeral=True
            )
            return
        target = self.check_channel(interaction, channel)
        if target is None:
            await interaction.response.send_message(
                embed=embeds.err("Выбранный канал недоступен для записи."), ephemeral=True
            )
            return
        await self.open_builder(interaction, EmbedDraft.from_json(payload), target)

    @template.command(name="list", description="Список сохранённых шаблонов")
    @access("say")
    async def template_list(self, interaction: discord.Interaction):
        rows = await self.bot.db.list_templates(interaction.guild.id)
        if not rows:
            await interaction.response.send_message(
                embed=embeds.info("Шаблонов пока нет. Сохрани первый из конструктора кнопкой 💾.",
                                  "💾 Шаблоны"),
                ephemeral=True,
            )
            return
        lines = [f"• **{r['name']}** — <@{r['author_id']}>, <t:{r['created_at']}:R>" for r in rows]
        await interaction.response.send_message(
            embed=embeds.info("\n".join(lines)[:4000], "💾 Шаблоны"), ephemeral=True
        )

    @template.command(name="delete", description="Удалить шаблон")
    @app_commands.describe(name="Название шаблона")
    @app_commands.autocomplete(name=template_names)
    @access("say")
    async def template_delete(self, interaction: discord.Interaction, name: str):
        removed = await self.bot.db.delete_template(interaction.guild.id, name.lower())
        message = (embeds.ok(f"Шаблон **{name}** удалён.")
                   if removed else embeds.err(f"Шаблон **{name}** не найден."))
        await interaction.response.send_message(embed=message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Staff(bot))
''',
    'vex.cogs.clan': r'''"""Клан: состав (/roster), карточки участников (/nick) и голосования (/poll)."""
import json
import logging
from time import time as now_ts

import discord
from discord import app_commands
from discord.ext import commands

from .. import config, embeds
from ..checks import access, member_has_access
from .tickets import PageView, paginate

log = logging.getLogger("vex")

NUMBERS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
MAX_OPTIONS = 10
BAR_WIDTH = 12
ROSTER_PAGE = 15


# --------------------------------------------------------------------------- утилиты
def bar(part, total, width=BAR_WIDTH):
    """5 из 12 -> '█████░░░░░░░'."""
    filled = round(width * part / total) if total else 0
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def poll_embed(poll, options, counts, voters):
    total = sum(counts)
    closed = bool(poll["closed"])
    embed = embeds.make(
        f"{'🔒' if closed else '📊'} {poll['question']}",
        color=config.COLOR_DARK if closed else config.COLOR_MAIN,
    )
    lines = []
    for index, option in enumerate(options):
        count = counts[index]
        percent = (count * 100 // total) if total else 0
        lines.append(f"{NUMBERS[index]} **{option}**\n`{bar(count, total)}` {percent}% · {count}")
    embed.description = "\n".join(lines)[:4000]

    mode = ["несколько вариантов" if poll["multi"] else "один вариант",
            "анонимно" if poll["anonymous"] else "открыто"]
    embed.add_field(name="Голосов", value=str(total), inline=True)
    embed.add_field(name="Участников", value=str(voters), inline=True)
    embed.add_field(name="Режим", value=" · ".join(mode), inline=True)
    note = " • голосование закрыто" if closed else ""
    embed.set_footer(text=f"{config.FOOTER}{note}")
    return embed


class PollButton(discord.ui.Button):
    def __init__(self, index, label):
        super().__init__(
            label=label[:80] or f"Вариант {index + 1}",
            emoji=NUMBERS[index],
            style=discord.ButtonStyle.secondary,
            custom_id=f"vex:poll:{index}",
            row=index // 5,
        )
        self.index = index

    async def callback(self, interaction):
        cog = interaction.client.get_cog("Clan")
        if cog is None:
            return
        await cog.handle_vote(interaction, self.index)


class PollView(discord.ui.View):
    """Постоянная вьюха: custom_id vex:poll:<номер>, сам опрос ищется по id сообщения."""

    def __init__(self, labels=None, closed=False):
        super().__init__(timeout=None)
        labels = labels if labels is not None else [f"Вариант {i + 1}" for i in range(MAX_OPTIONS)]
        for index, label in enumerate(labels[:MAX_OPTIONS]):
            button = PollButton(index, label)
            button.disabled = closed
            self.add_item(button)


# --------------------------------------------------------------------------- модуль
class Clan(commands.Cog):
    nick = app_commands.Group(name="nick", description="Карточка участника клана", guild_only=True)
    poll = app_commands.Group(name="poll", description="Голосования", guild_only=True)

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(PollView())

    # ---- состав клана
    @app_commands.command(name="roster", description="Состав клана")
    @app_commands.describe(role="Показать только участников с этой ролью")
    @app_commands.guild_only()
    @access("roster")
    async def roster(self, interaction: discord.Interaction, role: discord.Role | None = None):
        guild = interaction.guild
        cards = {r["user_id"]: r for r in await self.bot.db.list_clan_members(guild.id)}

        def hours_of(member):
            card = cards.get(member.id)
            return (card["hours"] or 0) if card else 0

        if role is not None:
            members = sorted([m for m in role.members if not m.bot], key=hours_of, reverse=True)
            title = f"⚔️ Состав: {role.name}"
        else:
            members = sorted(
                [m for m in (guild.get_member(uid) for uid in cards) if m is not None],
                key=hours_of, reverse=True,
            )
            title = "⚔️ Состав клана"

        if not members:
            await interaction.response.send_message(
                embed=embeds.info(
                    "Пока никто не заполнил карточку. Команда `/nick set` — и ты в списке.", title
                ),
                ephemeral=True,
            )
            return

        def line(member):
            card = cards.get(member.id)
            nick = card["nick"] if card and card["nick"] else member.display_name
            hours = f"{card['hours']} ч" if card and card["hours"] else "— ч"
            timezone = card["timezone"] if card and card["timezone"] else "—"
            return f"• **{nick}** — {member.mention} — {hours} — {timezone}"

        pages = paginate(members, ROSTER_PAGE, f"{title} ({len(members)})", line)
        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0])
            return
        await interaction.response.send_message(
            embed=pages[0], view=PageView(pages, interaction.user.id)
        )

    # ---- карточка участника
    @nick.command(name="set", description="Заполнить свою карточку участника")
    @app_commands.describe(nick="Ник в игре", hours="Часов в Rust",
                           timezone="Часовой пояс, например МСК+2")
    async def nick_set(self, interaction: discord.Interaction,
                       nick: app_commands.Range[str, 1, 64],
                       hours: app_commands.Range[int, 0, 100000] | None = None,
                       timezone: app_commands.Range[str, 1, 32] | None = None):
        await self.bot.db.set_clan_member(
            interaction.guild.id, interaction.user.id, nick=nick, hours=hours, timezone=timezone
        )
        lines = [f"Ник в игре: **{nick}**"]
        if hours is not None:
            lines.append(f"Часов: **{hours}**")
        if timezone:
            lines.append(f"Часовой пояс: **{timezone}**")
        await interaction.response.send_message(
            embed=embeds.ok("\n".join(lines), "Карточка сохранена"), ephemeral=True
        )

    @nick.command(name="show", description="Показать карточку участника")
    @app_commands.describe(user="Чья карточка (по умолчанию — твоя)")
    async def nick_show(self, interaction: discord.Interaction, user: discord.Member | None = None):
        member = user or interaction.user
        card = await self.bot.db.get_clan_member(interaction.guild.id, member.id)
        tickets = await self.bot.db.fetchone(
            "SELECT COUNT(*) AS n FROM tickets WHERE guild_id=? AND user_id=?",
            (interaction.guild.id, member.id),
        )
        embed = embeds.make(f"🎖️ {member.display_name}")
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Ник в игре",
                        value=(card["nick"] if card and card["nick"] else "—"), inline=True)
        embed.add_field(name="Часов в Rust",
                        value=(str(card["hours"]) if card and card["hours"] else "—"), inline=True)
        embed.add_field(name="Часовой пояс",
                        value=(card["timezone"] if card and card["timezone"] else "—"), inline=True)
        embed.add_field(name="Discord", value=f"{member.mention}\n`{member}`", inline=True)
        if member.joined_at:
            embed.add_field(name="В клане с",
                            value=discord.utils.format_dt(member.joined_at, "D"), inline=True)
        embed.add_field(name="Тикетов", value=str(tickets["n"] if tickets else 0), inline=True)
        roles = [r.mention for r in reversed(member.roles) if not r.is_default()]
        embed.add_field(name="Роли", value=" ".join(roles)[:1000] or "—", inline=False)
        if card and card["updated_at"]:
            embed.description = f"Карточка обновлена <t:{card['updated_at']}:R>"
        await interaction.response.send_message(embed=embed)

    @nick.command(name="clear", description="Очистить карточку")
    @app_commands.describe(user="Чью карточку очистить (чужую — только поддержке)")
    async def nick_clear(self, interaction: discord.Interaction, user: discord.Member | None = None):
        target = user or interaction.user
        if target.id != interaction.user.id and not await member_has_access(
            self.bot, interaction.user, "roster"
        ):
            await interaction.response.send_message(
                embed=embeds.err("Чужую карточку может очистить только поддержка."), ephemeral=True
            )
            return
        removed = await self.bot.db.clear_clan_member(interaction.guild.id, target.id)
        text = (f"Карточка {target.mention} очищена."
                if removed else f"У {target.mention} и не было карточки.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    # ---- голосования
    async def get_poll(self, message_id):
        return await self.bot.db.fetchone("SELECT * FROM polls WHERE message_id=?", (message_id,))

    async def poll_state(self, poll):
        """Возвращает (варианты, счётчики, число проголосовавших)."""
        try:
            options = json.loads(poll["options"])
        except (ValueError, TypeError):
            options = []
        counts = [0] * len(options)
        rows = await self.bot.db.fetchall(
            "SELECT user_id, option_index FROM poll_votes WHERE message_id=?", (poll["message_id"],)
        )
        voters = set()
        for row in rows:
            voters.add(row["user_id"])
            if 0 <= row["option_index"] < len(counts):
                counts[row["option_index"]] += 1
        return options, counts, len(voters)

    async def handle_vote(self, interaction, index):
        poll = await self.get_poll(interaction.message.id)
        if poll is None:
            await interaction.response.send_message(
                embed=embeds.err("Это голосование больше не отслеживается."), ephemeral=True
            )
            return
        if poll["closed"]:
            await interaction.response.send_message(
                embed=embeds.warn("Голосование закрыто."), ephemeral=True
            )
            return
        options, _, _ = await self.poll_state(poll)
        if index >= len(options):
            await interaction.response.send_message(
                embed=embeds.err("Такого варианта нет."), ephemeral=True
            )
            return

        db = self.bot.db
        existing = await db.fetchone(
            "SELECT 1 FROM poll_votes WHERE message_id=? AND user_id=? AND option_index=?",
            (poll["message_id"], interaction.user.id, index),
        )
        if existing:  # повторное нажатие снимает голос
            await db.execute(
                "DELETE FROM poll_votes WHERE message_id=? AND user_id=? AND option_index=?",
                (poll["message_id"], interaction.user.id, index),
            )
        else:
            if not poll["multi"]:
                await db.execute(
                    "DELETE FROM poll_votes WHERE message_id=? AND user_id=?",
                    (poll["message_id"], interaction.user.id),
                )
            await db.execute(
                "INSERT OR IGNORE INTO poll_votes(message_id, user_id, option_index) VALUES(?,?,?)",
                (poll["message_id"], interaction.user.id, index),
            )

        options, counts, voters = await self.poll_state(poll)
        await interaction.response.edit_message(
            embed=poll_embed(poll, options, counts, voters), view=PollView(options)
        )

    @poll.command(name="create", description="Создать голосование с кнопками")
    @app_commands.describe(
        question="Вопрос",
        options="Варианты через | — например: Да | Нет | Воздержусь",
        multi="Разрешить выбирать несколько вариантов",
        anonymous="Скрывать, кто за что проголосовал",
        ping_role="Упомянуть роль",
    )
    @access("poll")
    async def poll_create(self, interaction: discord.Interaction,
                          question: app_commands.Range[str, 1, 240],
                          options: str,
                          multi: bool = False,
                          anonymous: bool = True,
                          ping_role: discord.Role | None = None):
        parsed = [o.strip()[:80] for o in options.split("|") if o.strip()]
        if len(parsed) < 2:
            await interaction.response.send_message(
                embed=embeds.err("Нужно минимум два варианта, разделённых `|`."), ephemeral=True
            )
            return
        if len(parsed) > MAX_OPTIONS:
            await interaction.response.send_message(
                embed=embeds.err(f"Максимум {MAX_OPTIONS} вариантов."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        draft = {"question": question, "multi": int(multi), "anonymous": int(anonymous), "closed": 0}
        try:
            message = await interaction.channel.send(
                content=ping_role.mention if ping_role else None,
                embed=poll_embed(draft, parsed, [0] * len(parsed), 0),
                view=PollView(parsed),
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except discord.Forbidden:
            await interaction.followup.send(
                embed=embeds.err("У меня нет прав писать в этот канал."), ephemeral=True
            )
            return

        await self.bot.db.execute(
            "INSERT INTO polls(message_id, guild_id, channel_id, author_id, question, options, "
            "multi, anonymous, closed, created_at) VALUES(?,?,?,?,?,?,?,?,0,?)",
            (message.id, interaction.guild.id, interaction.channel.id, interaction.user.id,
             question, json.dumps(parsed, ensure_ascii=False), int(multi), int(anonymous),
             int(now_ts())),
        )
        await interaction.followup.send(
            embed=embeds.ok(f"Голосование создано: [перейти]({message.jump_url})"), ephemeral=True
        )

    async def fetch_poll_message(self, interaction, message_id):
        """Находит опрос и его сообщение. Возвращает (poll, message) или (None, None)."""
        raw = str(message_id).strip()
        if not raw.isdigit():
            await interaction.response.send_message(
                embed=embeds.err("`message_id` — это числовой ID сообщения с голосованием."),
                ephemeral=True,
            )
            return None, None
        poll = await self.get_poll(int(raw))
        if poll is None or poll["guild_id"] != interaction.guild.id:
            await interaction.response.send_message(
                embed=embeds.err("Голосование не найдено."), ephemeral=True
            )
            return None, None
        channel = interaction.guild.get_channel(poll["channel_id"])
        message = None
        if channel is not None:
            try:
                message = await channel.fetch_message(poll["message_id"])
            except (discord.NotFound, discord.Forbidden):
                message = None
        return poll, message

    @poll.command(name="close", description="Закрыть голосование и показать итог")
    @app_commands.describe(message_id="ID сообщения с голосованием")
    @access("poll")
    async def poll_close(self, interaction: discord.Interaction, message_id: str):
        poll, message = await self.fetch_poll_message(interaction, message_id)
        if poll is None:
            return
        await self.bot.db.execute(
            "UPDATE polls SET closed=1 WHERE message_id=?", (poll["message_id"],)
        )
        poll = await self.get_poll(poll["message_id"])
        options, counts, voters = await self.poll_state(poll)
        if message is not None:
            try:
                await message.edit(embed=poll_embed(poll, options, counts, voters),
                                   view=PollView(options, closed=True))
            except discord.HTTPException:
                pass
        await interaction.response.send_message(
            embed=embeds.ok("Голосование закрыто. Итог обновлён в сообщении."), ephemeral=True
        )

    @poll.command(name="results", description="Кто за что проголосовал")
    @app_commands.describe(message_id="ID сообщения с голосованием")
    @access("poll")
    async def poll_results(self, interaction: discord.Interaction, message_id: str):
        poll, _ = await self.fetch_poll_message(interaction, message_id)
        if poll is None:
            return
        options, counts, voters = await self.poll_state(poll)
        embed = poll_embed(poll, options, counts, voters)
        embed.title = f"📋 Итоги: {poll['question']}"[:256]

        if poll["anonymous"]:
            embed.add_field(name="Голосовавшие",
                            value="Голосование анонимное — списка нет.", inline=False)
        else:
            rows = await self.bot.db.fetchall(
                "SELECT user_id, option_index FROM poll_votes WHERE message_id=? "
                "ORDER BY option_index", (poll["message_id"],)
            )
            by_option = {}
            for row in rows:
                by_option.setdefault(row["option_index"], []).append(row["user_id"])
            for index, option in enumerate(options):
                ids = by_option.get(index, [])
                value = " ".join(f"<@{i}>" for i in ids)[:1000] or "—"
                embed.add_field(name=f"{NUMBERS[index]} {option} ({len(ids)})", value=value,
                                inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Clan(bot))
''',
    'vex.cogs.moderation': r'''"""Модерация: предупреждения, мут, кик, баны (в т.ч. временные), история нарушений, очистка чата."""
import logging
from datetime import timedelta
from time import time as now_ts

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import config, embeds
from ..checks import access
from ..modutil import ACTION_ICONS, ACTION_LABELS, MAX_TIMEOUT, format_duration, hierarchy_error, parse_duration

log = logging.getLogger("vex")

ACTION_COLORS = {
    "warn": config.COLOR_WARN,
    "mute": config.COLOR_ERR,
    "kick": config.COLOR_ERR,
    "ban": config.COLOR_ERR,
    "unmute": config.COLOR_OK,
    "unban": config.COLOR_OK,
}


def case_embed(row):
    action = row["action"]
    embed = embeds.make(
        f"{ACTION_ICONS.get(action, '📌')} {ACTION_LABELS.get(action, action)} · дело #{row['case_no']}",
        color=ACTION_COLORS.get(action, config.COLOR_MAIN),
    )
    embed.add_field(name="Участник", value=f"<@{row['user_id']}> (`{row['user_id']}`)", inline=True)
    embed.add_field(name="Модератор", value=f"<@{row['mod_id']}>", inline=True)
    if row["expires_at"]:
        embed.add_field(name="До", value=f"<t:{row['expires_at']}:f> (<t:{row['expires_at']}:R>)", inline=True)
    embed.add_field(name="Причина", value=(row["reason"] or "—")[:1000], inline=False)
    return embed


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.expire_loop.start()

    async def cog_unload(self):
        self.expire_loop.cancel()

    # ---- общие помощники
    async def make_case(self, guild, user_id, mod_id, action, reason, expires_at=None):
        row = await self.bot.db.add_case(guild.id, user_id, mod_id, action, reason, expires_at)
        await self.bot.send_log(guild, case_embed(row))
        return row

    async def guard(self, interaction, target):
        """Проверка иерархии. Отправляет ошибку и возвращает False, если наказывать нельзя."""
        error = hierarchy_error(interaction.user, target, interaction.guild, interaction.guild.me)
        if error:
            await interaction.response.send_message(embed=embeds.err(error), ephemeral=True)
            return False
        return True

    async def notify(self, user, guild, title, reason, extra=""):
        try:
            text = f"Сервер: **{guild.name}**\nПричина: {reason or '—'}{extra}"
            await user.send(embed=embeds.make(title, text, config.COLOR_WARN))
        except discord.HTTPException:
            pass  # личные сообщения закрыты

    async def active_warns(self, guild_id, user_id):
        row = await self.bot.db.fetchone(
            "SELECT COUNT(*) AS c FROM mod_cases WHERE guild_id=? AND user_id=? AND action='warn' AND active=1",
            (guild_id, user_id),
        )
        return row["c"]

    # ---- предупреждения
    @app_commands.command(name="warn", description="Выдать предупреждение участнику")
    @app_commands.describe(member="Кому", reason="Причина")
    @app_commands.guild_only()
    @access("mod")
    async def warn(self, interaction: discord.Interaction, member: discord.Member,
                   reason: app_commands.Range[str, 1, 500]):
        if not await self.guard(interaction, member):
            return
        await interaction.response.defer()
        guild = interaction.guild
        case = await self.make_case(guild, member.id, interaction.user.id, "warn", reason)
        count = await self.active_warns(guild.id, member.id)
        await self.notify(member, guild, "⚠️ Тебе выдано предупреждение", reason,
                          f"\nВсего предупреждений: **{count}**")
        text = f"{member.mention} получил предупреждение (дело **#{case['case_no']}**). Всего: **{count}**."

        threshold = int(await self.bot.db.get_setting(guild.id, "warn_threshold", "3"))
        minutes = min(int(await self.bot.db.get_setting(guild.id, "warn_timeout", "60")), MAX_TIMEOUT // 60)
        if threshold and minutes > 0 and count % threshold == 0:
            until = int(now_ts()) + minutes * 60
            try:
                await member.timeout(timedelta(minutes=minutes), reason=f"VEX: {count} предупреждений")
            except discord.HTTPException:
                text += "\n⚠️ Автоматический мут выдать не удалось (роль бота ниже или нет права)."
            else:
                await self.make_case(guild, member.id, self.bot.user.id, "mute",
                                     f"Автоматически: {count} предупреждений", until)
                text += f"\n🔇 Автоматический мут на **{format_duration(minutes * 60)}**."
        await interaction.followup.send(embed=embeds.ok(text, "Предупреждение выдано"))

    @app_commands.command(name="unwarn", description="Снять предупреждение (по номеру дела)")
    @app_commands.describe(case="Номер дела из /history")
    @app_commands.guild_only()
    @access("mod")
    async def unwarn(self, interaction: discord.Interaction, case: app_commands.Range[int, 1, 10_000_000]):
        changed = await self.bot.db.execute(
            "UPDATE mod_cases SET active=0 WHERE guild_id=? AND case_no=? AND action='warn' AND active=1",
            (interaction.guild.id, case),
        )
        if not changed:
            await interaction.response.send_message(
                embed=embeds.err(f"Активное предупреждение с номером #{case} не найдено."), ephemeral=True
            )
            return
        await interaction.response.send_message(embed=embeds.ok(f"Предупреждение #{case} снято."))

    # ---- мут
    @app_commands.command(name="mute", description="Отправить участника подумать (тайм-аут)")
    @app_commands.describe(member="Кому", duration="Срок: 30m, 2h, 1d (до 28 дней)", reason="Причина")
    @app_commands.guild_only()
    @access("mod")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: str,
                   reason: app_commands.Range[str, 1, 500]):
        seconds = parse_duration(duration)
        if seconds is None or seconds > MAX_TIMEOUT:
            await interaction.response.send_message(
                embed=embeds.err("Не понял срок. Примеры: `30m`, `2h`, `1d12h`. Максимум — 28 дней."), ephemeral=True
            )
            return
        if not await self.guard(interaction, member):
            return
        await interaction.response.defer()
        try:
            await member.timeout(timedelta(seconds=seconds), reason=f"{interaction.user}: {reason}"[:512])
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не удалось выдать мут: проверь право «Отправлять участников подумать» и роль VEX."),
                ephemeral=True,
            )
            return
        until = int(now_ts()) + seconds
        case = await self.make_case(interaction.guild, member.id, interaction.user.id, "mute", reason, until)
        await self.notify(member, interaction.guild, "🔇 Тебя замутили", reason,
                          f"\nСрок: **{format_duration(seconds)}**")
        await interaction.followup.send(embed=embeds.ok(
            f"{member.mention} замучен на **{format_duration(seconds)}** (дело **#{case['case_no']}**).", "Мут выдан"))

    @app_commands.command(name="unmute", description="Снять мут")
    @app_commands.describe(member="С кого", reason="Причина")
    @app_commands.guild_only()
    @access("mod")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = ""):
        if not member.is_timed_out():
            await interaction.response.send_message(
                embed=embeds.err("У этого участника нет активного мута."), ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            await member.timeout(None, reason=f"{interaction.user}: {reason}"[:512])
        except discord.HTTPException:
            await interaction.followup.send(embed=embeds.err("Не удалось снять мут."), ephemeral=True)
            return
        await self.make_case(interaction.guild, member.id, interaction.user.id, "unmute", reason)
        await interaction.followup.send(embed=embeds.ok(f"Мут с {member.mention} снят."))

    # ---- кик и баны
    @app_commands.command(name="kick", description="Выгнать участника с сервера")
    @app_commands.describe(member="Кого", reason="Причина")
    @app_commands.guild_only()
    @access("mod")
    async def kick(self, interaction: discord.Interaction, member: discord.Member,
                   reason: app_commands.Range[str, 1, 500]):
        if not await self.guard(interaction, member):
            return
        await interaction.response.defer()
        await self.notify(member, interaction.guild, "👢 Тебя выгнали с сервера", reason)
        try:
            await member.kick(reason=f"{interaction.user}: {reason}"[:512])
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не удалось выгнать: проверь право «Выгонять участников» и роль VEX."), ephemeral=True
            )
            return
        case = await self.make_case(interaction.guild, member.id, interaction.user.id, "kick", reason)
        await interaction.followup.send(embed=embeds.ok(
            f"{member} выгнан (дело **#{case['case_no']}**).", "Кик"))

    @app_commands.command(name="ban", description="Забанить пользователя (можно временно)")
    @app_commands.describe(user="Кого", reason="Причина", duration="Срок: 1d, 7d, 2w (пусто — навсегда)",
                           delete_days="Удалить сообщения за последние дни (0–7)")
    @app_commands.guild_only()
    @access("ban")
    async def ban(self, interaction: discord.Interaction, user: discord.User,
                  reason: app_commands.Range[str, 1, 500], duration: str | None = None,
                  delete_days: app_commands.Range[int, 0, 7] = 0):
        seconds = None
        if duration:
            seconds = parse_duration(duration)
            if seconds is None:
                await interaction.response.send_message(
                    embed=embeds.err("Не понял срок. Примеры: `1d`, `7d`, `2w`. Пусто — бан навсегда."), ephemeral=True
                )
                return
        target = interaction.guild.get_member(user.id) or user
        if not await self.guard(interaction, target):
            return
        await interaction.response.defer()
        extra = f"\nСрок: **{format_duration(seconds)}**" if seconds else ""
        if isinstance(target, discord.Member):
            await self.notify(target, interaction.guild, "🔨 Тебя забанили", reason, extra)
        try:
            await interaction.guild.ban(user, reason=f"{interaction.user}: {reason}"[:512],
                                        delete_message_seconds=delete_days * 86400)
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не удалось забанить: проверь право «Банить участников» и роль VEX."), ephemeral=True
            )
            return
        expires = int(now_ts()) + seconds if seconds else None
        case = await self.make_case(interaction.guild, user.id, interaction.user.id, "ban", reason, expires)
        text = f"{user} забанен {'на **' + format_duration(seconds) + '**' if seconds else 'навсегда'} " \
               f"(дело **#{case['case_no']}**)."
        await interaction.followup.send(embed=embeds.ok(text, "Бан"))

    @app_commands.command(name="unban", description="Разбанить пользователя по ID")
    @app_commands.describe(user_id="ID пользователя", reason="Причина")
    @app_commands.guild_only()
    @access("ban")
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = ""):
        if not user_id.strip().isdigit():
            await interaction.response.send_message(
                embed=embeds.err("Нужен числовой ID пользователя (ПКМ по нему → «Копировать ID»)."), ephemeral=True
            )
            return
        uid = int(user_id.strip())
        await interaction.response.defer()
        try:
            await interaction.guild.unban(discord.Object(id=uid), reason=f"{interaction.user}: {reason}"[:512])
        except discord.NotFound:
            await interaction.followup.send(embed=embeds.err("Этого пользователя нет в списке банов."), ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send(embed=embeds.err("Не удалось разбанить."), ephemeral=True)
            return
        await self.bot.db.execute(
            "UPDATE mod_cases SET active=0 WHERE guild_id=? AND user_id=? AND action='ban' AND active=1",
            (interaction.guild.id, uid),
        )
        await self.make_case(interaction.guild, uid, interaction.user.id, "unban", reason)
        await interaction.followup.send(embed=embeds.ok(f"<@{uid}> разбанен."))

    # ---- история и очистка
    @app_commands.command(name="history", description="История наказаний пользователя")
    @app_commands.describe(user="Чья история")
    @app_commands.guild_only()
    @access("mod")
    async def history(self, interaction: discord.Interaction, user: discord.User):
        rows = await self.bot.db.fetchall(
            "SELECT * FROM mod_cases WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT 15",
            (interaction.guild.id, user.id),
        )
        embed = embeds.make(f"📚 История: {user}")
        embed.set_thumbnail(url=user.display_avatar.url)
        if not rows:
            embed.description = "Нарушений нет."
        else:
            lines = []
            for row in rows:
                mark = "" if row["active"] or row["action"] != "warn" else " ~~снято~~"
                lines.append(
                    f"**#{row['case_no']}** {ACTION_ICONS.get(row['action'], '📌')} "
                    f"{ACTION_LABELS.get(row['action'], row['action'])} · <t:{row['created_at']}:d>{mark}\n"
                    f"└ {(row['reason'] or '—')[:90]}"
                )
            embed.description = "\n".join(lines)[:4000]
            warns = await self.active_warns(interaction.guild.id, user.id)
            embed.add_field(name="Активных предупреждений", value=str(warns), inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="purge", description="Удалить последние сообщения в канале")
    @app_commands.describe(amount="Сколько сообщений проверить (1–100)", member="Удалять только сообщения этого участника")
    @app_commands.guild_only()
    @access("mod")
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100],
                    member: discord.Member | None = None):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(embed=embeds.err("Работает только в текстовых каналах."),
                                                    ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        check = (lambda m: m.author.id == member.id) if member else None
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не удалось удалить: проверь право «Управлять сообщениями»."), ephemeral=True
            )
            return
        await interaction.followup.send(embed=embeds.ok(f"Удалено сообщений: **{len(deleted)}**."), ephemeral=True)
        entry = embeds.make("🧹 Очистка чата", color=config.COLOR_MAIN)
        entry.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        entry.add_field(name="Канал", value=interaction.channel.mention, inline=True)
        entry.add_field(name="Удалено", value=str(len(deleted)), inline=True)
        if member:
            entry.add_field(name="Сообщения участника", value=member.mention, inline=True)
        await self.bot.send_log(interaction.guild, entry)

    # ---- истечение временных банов
    @tasks.loop(minutes=1)
    async def expire_loop(self):
        try:
            rows = await self.bot.db.fetchall(
                "SELECT * FROM mod_cases WHERE action='ban' AND active=1 AND expires_at IS NOT NULL AND expires_at<=?",
                (int(now_ts()),),
            )
            for row in rows:
                guild = self.bot.get_guild(row["guild_id"])
                if guild is None:
                    continue
                try:
                    await guild.unban(discord.Object(id=row["user_id"]), reason="VEX: срок бана истёк")
                except discord.NotFound:
                    pass  # уже разбанен вручную
                except discord.HTTPException:
                    continue  # попробуем в следующую минуту
                await self.bot.db.execute("UPDATE mod_cases SET active=0 WHERE id=?", (row["id"],))
                await self.make_case(guild, row["user_id"], self.bot.user.id, "unban", "Срок бана истёк")
        except Exception:
            log.exception("Ошибка в цикле снятия временных банов")

    @expire_loop.before_loop
    async def before_expire_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Moderation(bot))
''',
    'vex.cogs.panels': r'''"""Панели ролей: сообщение с кнопками, по которым участники сами берут и снимают роли.

Панели создаются и редактируются на сайте (раздел «Панели ролей»).
"""
import discord
from discord.ext import commands

from .. import embeds
from ..modutil import dangerous_role


class RoleButton(discord.ui.DynamicItem[discord.ui.Button], template=r"vex:rp:(?P<panel>[0-9]+):(?P<role>[0-9]+)"):
    """Кнопка роли. Работает и после перезапуска бота: всё нужное зашито в custom_id."""

    def __init__(self, panel_id, role_id, label="Роль"):
        super().__init__(discord.ui.Button(
            label=label[:80], style=discord.ButtonStyle.secondary, custom_id=f"vex:rp:{panel_id}:{role_id}"
        ))
        self.panel_id = panel_id
        self.role_id = role_id

    @classmethod
    async def from_custom_id(cls, interaction, item, match, /):
        return cls(int(match["panel"]), int(match["role"]))

    async def callback(self, interaction):
        await interaction.client.get_cog("RolePanels").toggle(interaction, self.panel_id, self.role_id)


class RolePanels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_dynamic_items(RoleButton)

    # ---- нажатие кнопки
    async def toggle(self, interaction, panel_id, role_id):
        db = self.bot.db
        guild = interaction.guild
        member = interaction.user
        panel = await db.fetchone("SELECT * FROM role_panels WHERE id=? AND guild_id=?", (panel_id, guild.id))
        rows = await db.fetchall(
            "SELECT role_id FROM role_panel_roles WHERE panel_id=? ORDER BY position", (panel_id,)
        )
        panel_roles = [r["role_id"] for r in rows]
        if panel is None or role_id not in panel_roles:
            await interaction.response.send_message(
                embed=embeds.err("Эта панель устарела. Попроси администратора обновить её."), ephemeral=True
            )
            return
        role = guild.get_role(role_id)
        if role is None or role.managed or role >= guild.me.top_role or dangerous_role(role):
            await interaction.response.send_message(
                embed=embeds.err("Эту роль сейчас выдать нельзя. Сообщи администратору."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            if role in member.roles:
                await member.remove_roles(role, reason="VEX: панель ролей")
                text = f"Роль {role.mention} снята."
            else:
                to_remove = []
                if panel["exclusive"]:
                    for other_id in panel_roles:
                        other = guild.get_role(other_id)
                        if other and other != role and other in member.roles:
                            to_remove.append(other)
                await member.add_roles(role, reason="VEX: панель ролей")
                if to_remove:
                    await member.remove_roles(*to_remove, reason="VEX: панель ролей (одна роль на выбор)")
                text = f"Роль {role.mention} выдана."
        except discord.HTTPException:
            await interaction.followup.send(
                embed=embeds.err("Не получилось изменить роль. Сообщи администратору."), ephemeral=True
            )
            return
        await interaction.followup.send(embed=embeds.ok(text), ephemeral=True,
                                        allowed_mentions=discord.AllowedMentions.none())

    # ---- сборка сообщения (используется сайтом)
    async def build(self, panel):
        guild = self.bot.get_guild(panel["guild_id"])
        rows = await self.bot.db.fetchall(
            "SELECT role_id FROM role_panel_roles WHERE panel_id=? ORDER BY position", (panel["id"],)
        )
        embed = embeds.make(panel["title"], panel["description"] or None)
        if panel["exclusive"]:
            embed.add_field(name="ℹ️", value="Можно выбрать только одну роль из списка.", inline=False)
        view = discord.ui.View(timeout=None)
        for row in rows[:25]:
            role = guild.get_role(row["role_id"]) if guild else None
            if role is not None:
                view.add_item(RoleButton(panel["id"], role.id, role.name))
        return embed, view

    async def fetch_message(self, panel):
        channel = self.bot.get_channel(panel["channel_id"])
        if channel is None or not panel["message_id"]:
            return None
        try:
            return await channel.fetch_message(panel["message_id"])
        except discord.HTTPException:
            return None

    async def publish(self, panel_id):
        """Отправляет сообщение панели или обновляет уже отправленное."""
        db = self.bot.db
        panel = await db.fetchone("SELECT * FROM role_panels WHERE id=?", (panel_id,))
        channel = self.bot.get_channel(panel["channel_id"])
        embed, view = await self.build(panel)
        message = await self.fetch_message(panel)
        if message is not None:
            await message.edit(embed=embed, view=view)
            return message
        message = await channel.send(embed=embed, view=view)
        await db.execute("UPDATE role_panels SET message_id=? WHERE id=?", (message.id, panel_id))
        return message

    async def remove_message(self, panel):
        message = await self.fetch_message(panel)
        if message is not None:
            try:
                await message.delete()
            except discord.HTTPException:
                pass

    async def delete_panel(self, panel_id):
        db = self.bot.db
        panel = await db.fetchone("SELECT * FROM role_panels WHERE id=?", (panel_id,))
        if panel is None:
            return
        await self.remove_message(panel)
        await db.execute("DELETE FROM role_panel_roles WHERE panel_id=?", (panel_id,))
        await db.execute("DELETE FROM role_panels WHERE id=?", (panel_id,))


async def setup(bot):
    await bot.add_cog(RolePanels(bot))
''',
    'vex.cogs.logs': r'''"""Логи сервера: сообщения, участники, голосовые каналы, изменения сервера."""
import discord
from discord.ext import commands

from .. import config, embeds
from ..modutil import LOG_CATEGORIES as CATEGORIES


def clip(text, limit=900):
    text = text or ""
    return text if len(text) <= limit else text[:limit - 1] + "…"


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def emit(self, guild, category, embed):
        enabled = await self.bot.db.get_setting(guild.id, f"log_on_{category}", "1" if CATEGORIES[category][2] else "0")
        if enabled == "0":
            return
        await self.bot.send_log(guild, embed, key=f"log_ch_{category}")

    # ---- сообщения
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None or message.author.bot:
            return
        embed = embeds.make("🗑️ Сообщение удалено", color=config.COLOR_ERR)
        embed.add_field(name="Автор", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
        embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        embed.add_field(name="Текст", value=clip(message.content) or "*без текста*", inline=False)
        if message.attachments:
            embed.add_field(name="Вложения", value=clip("\n".join(a.filename for a in message.attachments), 500),
                            inline=False)
        await self.emit(message.guild, "messages", embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages or messages[0].guild is None:
            return
        embed = embeds.make("🧹 Массовое удаление сообщений", color=config.COLOR_ERR)
        embed.add_field(name="Канал", value=messages[0].channel.mention, inline=True)
        embed.add_field(name="Сообщений", value=str(len(messages)), inline=True)
        await self.emit(messages[0].guild, "messages", embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.guild is None or after.author.bot or before.content == after.content:
            return
        embed = embeds.make("✏️ Сообщение изменено", color=config.COLOR_WARN)
        embed.add_field(name="Автор", value=f"{after.author.mention} (`{after.author.id}`)", inline=True)
        embed.add_field(name="Канал", value=after.channel.mention, inline=True)
        embed.add_field(name="Было", value=clip(before.content, 700) or "—", inline=False)
        embed.add_field(name="Стало", value=clip(after.content, 700) or "—", inline=False)
        embed.add_field(name="Ссылка", value=f"[Перейти]({after.jump_url})", inline=True)
        await self.emit(after.guild, "messages", embed)

    # ---- участники
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = embeds.make("📥 Участник зашёл", color=config.COLOR_OK)
        embed.add_field(name="Участник", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="Аккаунт создан", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.emit(member.guild, "members", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = embeds.make("📤 Участник вышел", color=config.COLOR_ERR)
        embed.add_field(name="Участник", value=f"{member} (`{member.id}`)", inline=True)
        roles = " ".join(r.mention for r in member.roles if not r.is_default())
        embed.add_field(name="Роли", value=clip(roles, 900) or "—", inline=False)
        await self.emit(member.guild, "members", embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            embed = embeds.make("🎭 Роли участника изменены", color=config.COLOR_MAIN)
            embed.add_field(name="Участник", value=f"{after.mention} (`{after.id}`)", inline=False)
            if added:
                embed.add_field(name="Выданы", value=" ".join(r.mention for r in added), inline=True)
            if removed:
                embed.add_field(name="Сняты", value=" ".join(r.mention for r in removed), inline=True)
            await self.emit(after.guild, "members", embed)
        if before.nick != after.nick:
            embed = embeds.make("📝 Ник изменён", color=config.COLOR_MAIN)
            embed.add_field(name="Участник", value=f"{after.mention} (`{after.id}`)", inline=False)
            embed.add_field(name="Было", value=before.nick or "—", inline=True)
            embed.add_field(name="Стало", value=after.nick or "—", inline=True)
            await self.emit(after.guild, "members", embed)

    # ---- голос
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if before.channel is None:
            title, text = "🔊 Зашёл в голосовой канал", after.channel.mention
        elif after.channel is None:
            title, text = "🔇 Вышел из голосового канала", before.channel.mention
        else:
            title, text = "🔀 Перешёл между каналами", f"{before.channel.mention} → {after.channel.mention}"
        embed = embeds.make(title, color=config.COLOR_MAIN)
        embed.add_field(name="Участник", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="Канал", value=text, inline=True)
        await self.emit(member.guild, "voice", embed)

    # ---- сервер
    async def is_ticket_channel(self, channel):
        """Каналы тикетов создаются и удаляются постоянно — их в логах не показываем."""
        category = await self.bot.db.get_setting(channel.guild.id, "ticket_category")
        return bool(category) and str(getattr(channel, "category_id", "")) == category

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if await self.is_ticket_channel(channel):
            return
        embed = embeds.make("➕ Канал создан", f"{channel.mention} (`{channel.name}`)", config.COLOR_OK)
        await self.emit(channel.guild, "server", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if await self.is_ticket_channel(channel):
            return
        embed = embeds.make("➖ Канал удалён", f"`{channel.name}`", config.COLOR_ERR)
        await self.emit(channel.guild, "server", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = embeds.make("➕ Роль создана", f"{role.mention} (`{role.name}`)", config.COLOR_OK)
        await self.emit(role.guild, "server", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = embeds.make("➖ Роль удалена", f"`{role.name}`", config.COLOR_ERR)
        await self.emit(role.guild, "server", embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))
''',
    'vex.cogs.admin': r'''"""Администрирование: доступ к командам по ролям (/perms), настройки (/config), логи, приветствие, /help."""
import discord
from discord import app_commands
from discord.ext import commands

from .. import config, embeds
from ..checks import access, admin_only

KEY_CHOICES = [
    app_commands.Choice(name=f"{key} — {desc}"[:100], value=key)
    for key, desc in config.COMMAND_KEYS.items()
]

DEFAULT_WELCOME = (
    "Привет, {user}! Добро пожаловать на **{server}**.\n"
    "Загляни в правила, а если хочешь вступить в клан — открой тикет."
)


class Permissions(commands.Cog):
    perms = app_commands.Group(
        name="perms",
        description="Какие роли имеют доступ к каким командам бота",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    def __init__(self, bot):
        self.bot = bot

    @perms.command(name="grant", description="Дать роли доступ к группе команд")
    @app_commands.describe(command="Группа команд", role="Роль")
    @app_commands.choices(command=KEY_CHOICES)
    @admin_only()
    async def grant(self, interaction: discord.Interaction, command: app_commands.Choice[str],
                    role: discord.Role):
        added = await self.bot.db.add_target(interaction.guild.id, f"cmd:{command.value}", role.id)
        text = (f"{role.mention} теперь имеет доступ: **{command.value}**."
                if added else f"{role.mention} уже имеет доступ к **{command.value}**.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @perms.command(name="revoke", description="Забрать у роли доступ к группе команд")
    @app_commands.describe(command="Группа команд", role="Роль")
    @app_commands.choices(command=KEY_CHOICES)
    @admin_only()
    async def revoke(self, interaction: discord.Interaction, command: app_commands.Choice[str],
                     role: discord.Role):
        removed = await self.bot.db.remove_target(interaction.guild.id, f"cmd:{command.value}", role.id)
        text = (f"У {role.mention} больше нет доступа к **{command.value}**."
                if removed else f"У {role.mention} и не было доступа к **{command.value}**.")
        await interaction.response.send_message(embed=embeds.ok(text), ephemeral=True)

    @perms.command(name="reset", description="Сбросить доступ группы команд (останутся только администраторы)")
    @app_commands.describe(command="Группа команд")
    @app_commands.choices(command=KEY_CHOICES)
    @admin_only()
    async def reset(self, interaction: discord.Interaction, command: app_commands.Choice[str]):
        await self.bot.db.clear_targets(interaction.guild.id, f"cmd:{command.value}")
        await interaction.response.send_message(
            embed=embeds.ok(f"Доступ к **{command.value}** сброшен — только администраторы."), ephemeral=True
        )

    @perms.command(name="list", description="Показать, кто к чему имеет доступ")
    @admin_only()
    async def list_perms(self, interaction: discord.Interaction):
        embed = embeds.make("🔐 Доступ к командам", "Администраторы имеют доступ ко всему.")
        for key, desc in config.COMMAND_KEYS.items():
            ids = await self.bot.db.get_targets(interaction.guild.id, f"cmd:{key}")
            roles = " ".join(f"<@&{i}>" for i in ids) or "*только администраторы*"
            embed.add_field(name=f"`{key}`", value=f"{desc}\n└ {roles}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ServerConfig(commands.Cog):
    config_group = app_commands.Group(
        name="config",
        description="Настройки бота на сервере",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    def __init__(self, bot):
        self.bot = bot

    # ---- команды
    @config_group.command(name="log_channel", description="Канал для логов модерации и действий бота")
    @app_commands.describe(channel="Приватный канал для модераторов")
    @admin_only()
    async def log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.bot.db.set_setting(interaction.guild.id, "mod_log", channel.id)
        await interaction.response.send_message(
            embed=embeds.ok(f"Логи будут приходить в {channel.mention}."), ephemeral=True
        )

    @config_group.command(name="welcome", description="Включить приветствие новых участников")
    @app_commands.describe(channel="Канал приветствий",
                           text="Текст. Можно {user}, {server}. Пусто — стандартный")
    @admin_only()
    async def welcome(self, interaction: discord.Interaction, channel: discord.TextChannel,
                      text: str | None = None):
        gid = interaction.guild.id
        await self.bot.db.set_setting(gid, "welcome_channel", channel.id)
        if text:
            await self.bot.db.set_setting(gid, "welcome_text", text.replace("\\n", "\n"))
        else:
            await self.bot.db.del_setting(gid, "welcome_text")
        await interaction.response.send_message(
            embed=embeds.ok(f"Приветствия включены в {channel.mention}."), ephemeral=True
        )

    @config_group.command(name="welcome_off", description="Выключить приветствие")
    @admin_only()
    async def welcome_off(self, interaction: discord.Interaction):
        await self.bot.db.del_setting(interaction.guild.id, "welcome_channel")
        await interaction.response.send_message(embed=embeds.ok("Приветствия выключены."), ephemeral=True)

    @config_group.command(name="show", description="Показать текущие настройки")
    @admin_only()
    async def show(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        db = self.bot.db

        async def channel_of(key):
            value = await db.get_setting(gid, key)
            return f"<#{value}>" if value else "—"

        category = await db.get_setting(gid, "ticket_category")
        embed = embeds.make("⚙️ Настройки VEX")
        embed.add_field(name="Лог модерации", value=await channel_of("mod_log"), inline=True)
        embed.add_field(name="Лог тикетов", value=await channel_of("ticket_log"), inline=True)
        embed.add_field(name="Приветствия", value=await channel_of("welcome_channel"), inline=True)
        embed.add_field(name="Категория тикетов", value=f"<#{category}>" if category else "—", inline=True)
        embed.add_field(name="Часовой пояс", value=config.TIMEZONE, inline=True)
        embed.add_field(name="База данных", value=f"`{self.bot.db.path}`", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---- приветствие новых участников (журнал входов/выходов ведёт модуль logs)
    @commands.Cog.listener()
    async def on_member_join(self, member):
        gid = member.guild.id
        channel_id = await self.bot.db.get_setting(gid, "welcome_channel")
        if not channel_id or member.bot:
            return
        channel = member.guild.get_channel(int(channel_id))
        if channel is None:
            return
        template = await self.bot.db.get_setting(gid, "welcome_text", DEFAULT_WELCOME)
        text = template.replace("{user}", member.mention).replace("{server}", member.guild.name)
        embed = embeds.make("👋 Добро пожаловать!", text)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Участник №", value=str(member.guild.member_count), inline=True)
        try:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException:
            pass


class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dashboard", description="Ссылка на сайт-панель управления")
    @app_commands.guild_only()
    @access("dashboard")
    async def dashboard(self, interaction: discord.Interaction):
        url = await self.bot.get_public_url()
        if not url:
            await interaction.response.send_message(
                embed=embeds.err(
                    "Адрес сайта ещё не известен. Администратору нужно один раз войти на сайт через Discord "
                    "(после этого адрес запомнится) или задать переменную `PUBLIC_URL` на хостинге."
                ),
                ephemeral=True,
            )
            return
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Открыть панель", emoji="🌐", style=discord.ButtonStyle.link,
                                        url=f"{url}/g/{interaction.guild.id}"))
        text = ("Здесь настраивается бот: модерация, события, тикеты и многое другое.\n"
                "Вход через твой аккаунт Discord. Какие разделы тебе доступны, зависит от твоей роли.")
        await interaction.response.send_message(embed=embeds.info(text, "🌐 Панель управления VEX"), view=view,
                                                ephemeral=True)


# Разделы справки: (заголовок, [(команда, что делает, ключ доступа)])
HELP_SECTIONS = [
    ("🎫 Тикеты", [
        ("/ticket panel", "панель создания обращений", "ticket_admin"),
        ("/ticket setup", "категория, лог, лимит, удалять ли канал", "ticket_admin"),
        ("/ticket support add|remove|list", "роли поддержки", "ticket_admin"),
        ("/ticket type add|remove|list", "свои типы обращений", "ticket_admin"),
        ("/ticket blacklist add|remove|list", "кому запрещено открывать тикеты", "ticket_admin"),
        ("/ticket autoclose · archive", "автозакрытие и категория-архив", "ticket_admin"),
        ("/ticket reopen", "открыть закрытый тикет заново", "ticket_admin"),
        ("/ticket claim · unclaim · transfer", "взять, отпустить, передать", "поддержка"),
        ("/ticket priority · lock · unlock · move", "срочность, блокировка, перенос", "поддержка"),
        ("/ticket note · notes", "внутренние заметки", "поддержка"),
        ("/ticket add · remove · rename · close", "участники, имя канала, закрытие", "поддержка"),
        ("/ticket list · info · transcript · stats", "обзор, карточка, переписка, статистика",
         "ticket_manage"),
    ]),
    ("✉️ Эмбеды и сообщения", [
        ("/say embed", "конструктор: заголовок, автор, футер, поля, картинки, JSON", "say"),
        ("/say plain", "быстрый текст от имени бота", "say"),
        ("/say raw", "отправка готового JSON", "say"),
        ("/say edit", "править сообщение бота в конструкторе", "say"),
        ("/say template save|load|list|delete", "шаблоны эмбедов", "say"),
    ]),
    ("⚔️ Клан и вайпы", [
        ("/wipereact", "событие с кнопками «Приду / Не приду / Опоздаю»", "wipe"),
        ("/noreact", "кто не ответил на событие", "wipe"),
        ("/wipe stats", "топ по явке на вайпы", "wipe"),
        ("/roster", "состав клана страницами", "roster"),
        ("/nick set · show · clear", "карточка участника: ник, часы, часовой пояс", "всем"),
        ("/poll create · close · results", "голосование кнопками с живыми результатами", "poll"),
    ]),
    ("🔨 Наказания", [
        ("/warn · unwarn · mute · unmute · kick", "предупреждения, мут, кик", "mod"),
        ("/ban · unban", "баны", "ban"),
        ("/history · purge", "история нарушений, очистка чата", "mod"),
    ]),
    ("🌐 Сайт", [
        ("/dashboard", "ссылка на панель управления (панели ролей, логи, настройки)", "dashboard"),
    ]),
    ("🛡️ Защита и роли", [
        ("/automod status · toggle", "автомодерация ссылок", "automod"),
        ("/automod allow · disallow · bypass · ignore_channel · punishment",
         "домены, исключения, наказание", "automod"),
        ("/role add · remove", "выдать и снять роль", "role"),
        ("/role allow · deny · allowed", "какие роли можно выдавать", "role_admin"),
        ("/autorole add · remove · list", "роли для новых участников и ботов", "autorole"),
    ]),
    ("⚙️ Настройка", [
        ("/perms grant · revoke · reset · list", "кто какими командами пользуется", "админ"),
        ("/config log_channel", "канал логов модерации", "админ"),
        ("/config welcome · welcome_off", "приветствие новых участников", "админ"),
        ("/config show", "текущие настройки сервера", "админ"),
        ("/help", "эта справка", "всем"),
    ]),
]


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Что умеет VEX")
    async def help(self, interaction: discord.Interaction):
        embed = embeds.make(
            "🟣 VEX — управление кланом",
            "Тикеты, конструктор эмбедов, состав клана, вайп-события, модерация и защита сервера.\n"
            "В скобках — ключ доступа: его выдают роли командой `/perms grant`.",
        )
        for title, rows in HELP_SECTIONS:
            lines = [f"`{command}`\n└ {what} *({key})*" for command, what, key in rows]
            embed.add_field(name=title, value="\n".join(lines)[:1024], inline=False)
        embed.set_footer(text=f"{config.FOOTER} • «поддержка» = роль из /ticket support add")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Permissions(bot))
    await bot.add_cog(ServerConfig(bot))
    await bot.add_cog(Dashboard(bot))
    await bot.add_cog(Help(bot))
''',
}


class _EmbeddedFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Отдаёт модули vex.* прямо из словаря _SOURCES, без файлов на диске."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in _SOURCES:
            return None
        return importlib.util.spec_from_loader(fullname, self, is_package=fullname in _PACKAGES)

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        name = module.__spec__.name
        filename = name.replace(".", "/") + (".py" if name not in _PACKAGES else "/__init__.py")
        exec(compile(_SOURCES[name], filename, "exec"), module.__dict__)

    def get_source(self, fullname):  # чтобы в ошибках были видны строки кода
        return _SOURCES[fullname]


sys.meta_path.insert(0, _EmbeddedFinder())


def main():
    from vex import config
    from vex.bot import VexBot

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not config.TOKEN:
        raise SystemExit("Не задана переменная окружения DISCORD_TOKEN")
    VexBot().run(config.TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
