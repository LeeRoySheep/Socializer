# Socializer Project File Documentation

> **Purpose**: Document every file in the project, its usage, and quality status.
> **Approach**: Backend-first, category by category, test after each change.
> **Standards**: OOP best practices, docstrings, comments review.

---

## Status Legend
- ✅ **REVIEWED** - File checked, meets standards
- ⚠️ **NEEDS WORK** - File needs improvements (OOP/docstrings/comments)
- 🗑️ **DELETE** - File is unused/duplicate, marked for deletion
- 🔄 **IN PROGRESS** - Currently being reviewed
- ⏳ **PENDING** - Not yet reviewed

---

## Category 1: Core Application (`app/`)

### Main Entry Points
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/__init__.py` | Package init | ✅ | Cleaned: removed unused FastAPI() instance |
| `app/main.py` | FastAPI app entry point | ✅ | Cleaned: removed duplicate imports, dead code, replaced 30+ print() with logger |
| `app/web.py` | Web routes | 🗑️ | DELETED: Dead code, never imported/mounted |
| `app/config.py` | Configuration settings | ✅ | Cleaned: removed duplicate import, reorganized imports |
| `app/database.py` | Database connection | ✅ | Active - full DB config with pooling, logging, error handling |
| `app/db.py` | DB utilities | 🗑️ | DELETED: Dead code, replaced by database.py |
| `app/dependencies.py` | FastAPI dependencies | ✅ | Clean - Note: get_db() duplicated with database.py (consolidate later) |
| `app/auth.py` | Authentication logic | ⏳ | |
| `app/auth_utils.py` | Auth utilities | ⏳ | |
| `app/ai_manager.py` | AI management | ⏳ | |
| `app/chat_interfaces.py` | Chat interfaces | ⏳ | |
| `app/ote_logger.py` | OTE logging | ⏳ | |
| `app/websocket_manager.py` | WebSocket management | ⏳ | |

### Routers (`app/routers/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/routers/__init__.py` | Package init | ⏳ | |
| `app/routers/ai.py` | AI endpoints | ⏳ | |
| `app/routers/auth.py` | Auth endpoints | ⏳ | |
| `app/routers/chat.py` | Chat endpoints | ⏳ | |
| `app/routers/rooms.py` | Room endpoints | ⏳ | |
| `app/routers/test_runner.py` | Test runner endpoint | ⏳ | |
| `app/routers/users.py` | User endpoints | ⏳ | |

### Models & Schemas (`app/models/`, `app/schemas/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/models/__init__.py` | SQLAlchemy models | ⏳ | |
| `app/schemas/__init__.py` | Pydantic schemas | ⏳ | |

### Services (`app/services/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/services/__init__.py` | Package init | ⏳ | |
| `app/services/ai_chat_agent_service.py` | AI chat service | ⏳ | |
| `app/services/room_ai_service.py` | Room AI service | ⏳ | |

### Agents (`app/agents/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/agents/__init__.py` | Package init | ⏳ | |
| `app/agents/memory_handler.py` | Memory handling | ⏳ | |
| `app/agents/response_handler.py` | Response handling | ⏳ | |
| `app/agents/tool_handler.py` | Tool handling | ⏳ | |

### WebSocket (`app/websocket/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/websocket/__init__.py` | Package init | ⏳ | |
| `app/websocket/chat_endpoint.py` | Chat WS endpoint | ⏳ | |
| `app/websocket/chat_manager.py` | Chat WS manager | ⏳ | |
| `app/websocket/connection_manager.py` | Connection manager | ⏳ | |
| `app/websocket/general_chat_history.py` | Chat history | ⏳ | |
| `app/websocket/room_websocket.py` | Room WS | ⏳ | |
| `app/websocket/routes.py` | WS routes | ⏳ | |

### Auth & Security (`app/auth/`, `app/security/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/auth/__init__.py` | Package init | ⏳ | |
| `app/auth/token_manager.py` | Token management | ⏳ | |
| `app/security/__init__.py` | Package init | ⏳ | |
| `app/security/encryption.py` | Encryption utils | ⏳ | |

### Utils (`app/utils/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `app/utils/__init__.py` | Package init | ⏳ | |
| `app/utils/decorators.py` | Decorators | ⏳ | |
| `app/utils/metrics.py` | Metrics | ⏳ | |
| `app/utils/ote_logger.py` | OTE logger | ⏳ | |

---

## Category 2: Data Management (`datamanager/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `datamanager/__init__.py` | Package init | ⏳ | |
| `datamanager/data_manager.py` | Main data manager | ⏳ | |
| `datamanager/data_model.py` | Data models | ⏳ | |
| `datamanager/life_event_manager.py` | Life events | ⏳ | |
| `datamanager/test_data_model.py` | Tests | ⏳ | |
| `datamanager/README.md` | Documentation | ⏳ | |

---

## Category 3: Memory System (`memory/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `memory/__init__.py` | Package init | ⏳ | |
| `memory/memory_encryptor.py` | Encryption | ⏳ | |
| `memory/secure_memory_manager.py` | Secure memory | ⏳ | |
| `memory/user_agent.py` | User agent | ⏳ | |

---

## Category 4: AI & LLM (`ai_chatagent.py`, `llm_*.py`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `ai_chatagent.py` | Main AI chat agent | ⏳ | |
| `llm_config.py` | LLM configuration | ⏳ | |
| `llm_manager.py` | LLM manager | ⏳ | |
| `llm_provider_manager.py` | Provider manager | ⏳ | |
| `response_formatter.py` | Response formatting | ⏳ | |
| `skill_agents.py` | Skill agents | ⏳ | |
| `web_search_tool.py` | Web search tool | ⏳ | |

---

## Category 5: Tools (`tools/`)

### Core Tools
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/__init__.py` | Package init | ⏳ | |
| `tools/tool_manager.py` | Tool manager | ⏳ | |
| `tools/conversation_recall_tool.py` | Conversation recall | ⏳ | |
| `tools/conversation_recall_tool_v2.py` | V2 recall | ⏳ | |
| `tools/language_preference_tool.py` | Language prefs | ⏳ | |

### Communication (`tools/communication/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/communication/__init__.py` | Package init | ⏳ | |
| `tools/communication/clarity_tool.py` | Clarity tool | ⏳ | |
| `tools/communication/cultural_checker_tool.py` | Cultural checker | ⏳ | |

### Events (`tools/events/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/events/__init__.py` | Package init | ⏳ | |
| `tools/events/life_event_tool.py` | Life events | ⏳ | |

### Gemini (`tools/gemini/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/gemini/__init__.py` | Package init | ⏳ | |
| `tools/gemini/base.py` | Base class | ⏳ | |
| `tools/gemini/response_handler.py` | Response handler | ⏳ | |
| `tools/gemini/search_tool.py` | Search tool | ⏳ | |
| `tools/gemini/validator.py` | Validator | ⏳ | |
| `tools/gemini/README.md` | Documentation | ⏳ | |

### Search (`tools/search/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/search/__init__.py` | Package init | ⏳ | |
| `tools/search/tavily_search_tool.py` | Tavily search | ⏳ | |

### Skills (`tools/skills/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/skills/__init__.py` | Package init | ⏳ | |
| `tools/skills/evaluator_tool.py` | Evaluator | ⏳ | |

### User (`tools/user/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tools/user/__init__.py` | Package init | ⏳ | |
| `tools/user/preference_tool.py` | Preferences | ⏳ | |

---

## Category 6: Services (Root Level) (`services/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `services/ai_language_detector.py` | AI language detection | ⏳ | |
| `services/language_detector.py` | Language detection | ⏳ | |

---

## Category 7: Models (Root Level) (`models/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `models/__init__.py` | Package init | ⏳ | |
| `models/life_event.py` | Life event model | ⏳ | |

---

## Category 8: Training (`training/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `training/__init__.py` | Package init | ⏳ | |
| `training/training_plan_manager.py` | Training manager | ⏳ | |

---

## Category 9: Frontend (`static/`, `templates/`)

### Templates
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `templates/base.html` | Base template | ⏳ | |
| `templates/login.html` | Login page | ⏳ | |
| `templates/register.html` | Register page | ⏳ | |
| `templates/new-chat.html` | New chat page | ⏳ | |
| `templates/rooms.html` | Rooms page | ⏳ | |
| `templates/test.html` | Test page | ⏳ | |
| `templates/test_login.html` | Test login | ⏳ | |
| `templates/test_runner.html` | Test runner | ⏳ | |

### CSS (`static/css/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `static/css/style.css` | Main styles | ⏳ | |
| `static/css/chat.css` | Chat styles | ⏳ | |
| `static/css/new-chat.css` | New chat styles | ⏳ | |
| `static/css/rooms.css` | Room styles | ⏳ | |
| `static/css/chat-history.css` | History styles | ⏳ | |

### JavaScript (`static/js/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `static/js/auth.js` | Auth logic | ⏳ | |
| `static/js/chat.js` | Chat logic | ⏳ | |
| `static/js/chat-new.js` | New chat logic | ⏳ | |
| `static/js/encryption.js` | Encryption | ⏳ | |

### JS Modules (`static/js/modules/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `static/js/modules/ChatController.js` | Chat controller | ⏳ | |
| `static/js/modules/RoomManager.js` | Room manager | ⏳ | |
| `static/js/modules/RoomUI.js` | Room UI | ⏳ | |
| `static/js/modules/UIManager.js` | UI manager | ⏳ | |
| `static/js/modules/WebSocketService.js` | WebSocket | ⏳ | |

### JS Auth (`static/js/auth/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `static/js/auth/AuthService.js` | Auth service | ⏳ | |
| `static/js/auth/LoginForm.js` | Login form | ⏳ | |
| `static/js/auth/LogoutButton.js` | Logout button | ⏳ | |
| `static/js/auth/index.js` | Auth index | ⏳ | |

### JS Chat (`static/js/chat/`)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `static/js/chat/ChatService.js` | Chat service | ⏳ | |
| `static/js/chat/ChatUI.js` | Chat UI | ⏳ | |
| `static/js/chat/PrivateRooms.js` | Private rooms | ⏳ | |

---

## Category 10: Scripts (`scripts/`)

### Database Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `scripts/database/create_db.py` | Create DB | ⏳ | |
| `scripts/database/create_tables.py` | Create tables | ⏳ | |
| `scripts/database/init_database_with_memory.py` | Init with memory | ⏳ | |

### Migration Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `scripts/migration/migrate_add_general_chat.py` | Add general chat | ⏳ | |
| `scripts/migration/migrate_add_memory_fields.py` | Add memory fields | ⏳ | |

### Maintenance Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `scripts/maintenance/backup_code.py` | Backup | ⏳ | |
| `scripts/maintenance/cleanup_user_memory.py` | Cleanup memory | ⏳ | |
| `scripts/maintenance/clear_user_memory.py` | Clear memory | ⏳ | |
| `scripts/maintenance/fix_user_encryption_key.py` | Fix encryption | ⏳ | |
| `scripts/maintenance/set_user_language.py` | Set language | ⏳ | |
| `scripts/maintenance/verify_all_fixes.sh` | Verify fixes | ⏳ | |
| `scripts/maintenance/verify_fixes.py` | Verify fixes | ⏳ | |

### Development Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `scripts/development/create_test_users.py` | Create users | ⏳ | |
| `scripts/development/debug_chat_history.py` | Debug history | ⏳ | |
| `scripts/development/diagnose_gemini_api.py` | Diagnose Gemini | ⏳ | |
| `scripts/development/test_auth_api.sh` | Test auth API | ⏳ | |
| `scripts/development/test_registration_both_methods.sh` | Test registration | ⏳ | |

### Archive Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `scripts/archive/migrate_claude_model_names.py` | Migrate Claude | ⏳ | |
| `scripts/archive/tool_nodes.py` | Tool nodes | ⏳ | |

---

## Category 11: Tests (`tests/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `tests/__init__.py` | Package init | ⏳ | |
| `tests/conftest.py` | Pytest config | ⏳ | |
| `tests/comprehensive_api_test.py` | API tests | ⏳ | |
| `tests/test_*.py` | Various tests | ⏳ | |

---

## Category 12: Root Level Files

### Configuration
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `.env` | Environment vars | ⏳ | |
| `.env.example` | Env example | ⏳ | |
| `.env.test` | Test env | ⏳ | |
| `requirements.txt` | Python deps | ⏳ | |
| `package.json` | Node deps | ⏳ | |
| `setup.py` | Package setup | ⏳ | |
| `alembic.ini` | Alembic config | ⏳ | |

### Utility Scripts (Root)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `add_ai_comparison_slides.py` | Add slides | ⏳ | |
| `create_er_diagram.py` | ER diagram | ⏳ | |
| `create_er_diagrams_split.py` | Split ER | ⏳ | |
| `create_presentation.py` | Presentation | ⏳ | |
| `execute_cleanup.py` | Execute cleanup | ⏳ | |
| `format_tool.py` | Format tool | ⏳ | |
| `init_chat_tables.py` | Init tables | ⏳ | |
| `recreate_users.py` | Recreate users | ⏳ | |
| `verify_claude_fix.py` | Verify Claude | ⏳ | |
| `verify_database_encryption.py` | Verify encryption | ⏳ | |

### Shell Scripts
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `install_llm_providers.sh` | Install LLM | ⏳ | |
| `update_deps.sh` | Update deps | ⏳ | |
| `verify_venv.sh` | Verify venv | ⏳ | |

### Documentation (Root)
| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `README.md` | Main readme | ⏳ | |
| `CHANGELOG.md` | Changelog | ⏳ | |
| `TODO.md` | Todo list | ⏳ | |
| `LICENSE` | License | ⏳ | |
| `SECURITY.md` | Security info | ⏳ | |
| `SECURITY_NOTICE.md` | Security notice | ⏳ | |
| `SECURITY_AUDIT.md` | Security audit | ⏳ | |
| Various report .md files | Reports | ⏳ | |

---

## Files Marked for Deletion

| File | Reason | Confirmed |
|------|--------|-----------|
| `app/web.py` | Dead code - never imported/mounted, duplicates main.py routes | ✅ Deleted (backup: .backup/app_web.py.bak) |
| `app/db.py` | Dead code - never imported, replaced by database.py | ✅ Deleted (backup: .backup/app_db.py.bak) |

---

## Review Progress

- [ ] Category 1: Core Application (`app/`)
- [ ] Category 2: Data Management (`datamanager/`)
- [ ] Category 3: Memory System (`memory/`)
- [ ] Category 4: AI & LLM
- [ ] Category 5: Tools (`tools/`)
- [ ] Category 6: Services (Root Level)
- [ ] Category 7: Models (Root Level)
- [ ] Category 8: Training
- [ ] Category 9: Frontend
- [ ] Category 10: Scripts
- [ ] Category 11: Tests
- [ ] Category 12: Root Level Files

---

*Last Updated: [In Progress]*
