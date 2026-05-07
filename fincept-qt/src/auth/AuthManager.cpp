#include "auth/AuthManager.h"

#include <QProcessEnvironment>
#include <QFile>
#include <QTextStream>

#include "auth/AuthApi.h"
#include "auth/PinManager.h"
#include "auth/UserApi.h"
#include "core/config/AppConfig.h"
#include "core/logging/Logger.h"
#include "network/http/HttpClient.h"
#include "storage/repositories/LlmConfigRepository.h"
#include "storage/repositories/SettingsRepository.h"
#include "storage/secure/SecureStorage.h"

#include <QCryptographicHash>
#include <QDateTime>
#include <QJsonDocument>
#include <QRandomGenerator>
#include <QSysInfo>

namespace fincept::auth {

AuthManager& AuthManager::instance() {
    static AuthManager s;
    return s;
}

AuthManager::AuthManager() {}

void AuthManager::set_loading(bool v) {
    if (is_loading_ != v) {
        is_loading_ = v;
        emit loading_changed(v);
    }
}

QJsonObject AuthManager::unwrap_data(const QJsonObject& raw) const {
    if (raw.contains("data") && raw["data"].isObject()) {
        const auto inner = raw["data"].toObject();
        if (inner.contains("data") && inner["data"].isObject()) {
            return inner["data"].toObject();
        }
        return inner;
    }
    return raw;
}

QString AuthManager::generate_device_id() const {
    QString info =
        QSysInfo::machineHostName() + "|" + QSysInfo::productType() + "|" + QSysInfo::currentCpuArchitecture();
    QByteArray hash = QCryptographicHash::hash(info.toUtf8(), QCryptographicHash::Sha256).toHex();
    QString timestamp = QString::number(QDateTime::currentMSecsSinceEpoch(), 36);
    quint32 random = QRandomGenerator::global()->generate();
    return QString("fincept_desktop_%1_%2_%3")
        .arg(QString::fromUtf8(hash.left(16)), timestamp, QString::number(random, 36));
}

// ── Token helper — single place to set/clear tokens on HttpClient ────────────

static void apply_tokens(const QString& api_key, const QString& session_token) {
    auto& http = fincept::HttpClient::instance();
    http.set_auth_header(api_key);
    http.set_session_token(session_token);
}

static void clear_tokens() {
    apply_tokens({}, {});
}

// ── Session persistence (SQLite via SettingsRepository) ──────────────────────

void AuthManager::save_session() {
    QJsonDocument doc(session_.to_json());
    QString json = QString::fromUtf8(doc.toJson(QJsonDocument::Compact));
    auto r = fincept::SettingsRepository::instance().set("fincept_session", json, "auth");
    if (r.is_err()) {
        LOG_ERROR("Auth", "Failed to save session: " + QString::fromStdString(r.error()));
    }

    // Persist api_key to OS-native encrypted storage (DPAPI / Keychain) as the
    // durable credential. SQLite session JSON is the fallback.
    if (!session_.api_key.isEmpty()) {
        auto sr = fincept::SecureStorage::instance().store("api_key", session_.api_key);
        if (sr.is_err())
            LOG_WARN("Auth", "SecureStorage: failed to persist api_key — using SQLite fallback");
    }
}

void AuthManager::load_session() {
    auto r = fincept::SettingsRepository::instance().get("fincept_session");
    if (r.is_ok() && !r.value().isEmpty()) {
        auto doc = QJsonDocument::fromJson(r.value().toUtf8());
        if (!doc.isNull())
            session_ = SessionData::from_json(doc.object());
    }

    // Try to recover api_key from SecureStorage (DPAPI / Keychain) — this is the
    // most reliable source since it survives SQLite corruption and DB migrations.
    auto secure_key = fincept::SecureStorage::instance().retrieve("api_key");
    if (secure_key.is_ok() && !secure_key.value().isEmpty()) {
        if (session_.api_key.isEmpty() || session_.api_key != secure_key.value()) {
            LOG_INFO("Auth", "Restored api_key from SecureStorage");
            session_.api_key = secure_key.value();
        }
    }

    // Never trust saved authenticated flag — must be re-validated
    session_.authenticated = false;
}

void AuthManager::clear_session() {
    session_ = SessionData{};
    clear_tokens();
    fincept::SettingsRepository::instance().remove("fincept_session");
    fincept::SettingsRepository::instance().remove("fincept_api_key");
    fincept::SecureStorage::instance().remove("api_key");

    // PIN intentionally NOT cleared here. The PIN is a local-device credential,
    // independent of the backend session. Wiping it on every logout means a
    // transient session expiry (SessionGuard 401 path, explicit Logout) trains
    // the user to keep choosing fresh PINs and destroys the audit trail across
    // sessions. The only path that should reset the PIN is the max-attempts
    // re-auth flow (LockScreen → reauth_requested), and that path should call
    // PinManager::clear_pin() explicitly before invoking logout().

    // Clear auto-configured fincept LLM provider and reset LlmService
    LlmConfigRepository::instance().delete_provider("fincept");
}

bool AuthManager::needs_pin_setup() const {
    // SSO 模式不需要 PIN — 安全性由 SaaS session 保障
    if (is_sso_mode_)
        return false;
    return session_.authenticated && !PinManager::instance().has_pin();
}

// ── Initialize ───────────────────────────────────────────────────────────────

void AuthManager::initialize() {
    set_loading(true);
    load_session();

    // ── SSO 路徑：KTW_JWT_TOKEN 環境變數存在 → 自動登入（跳過手動登入流程）──
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        QString sso_token = QProcessEnvironment::systemEnvironment()
                                .value("KTW_JWT_TOKEN");
        if (!sso_token.isEmpty()) {
            LOG_INFO("Auth", "SSO: 偵測到 KTW_JWT_TOKEN，嘗試自動登入...");
            is_sso_mode_ = true;
            session_.api_key = sso_token;
            auto& http = fincept::HttpClient::instance();
            http.set_auth_header(sso_token);
            http.clear_session_token();
            // 啟動 JWT 檔案監視（Pool Manager 定期寫入新 JWT 到 /tmp/.ktw_jwt）
            setup_jwt_file_watcher();
            // 走既有 profile → subscription 驗證鏈路
            validate_saved_session();
            return;
        }
    }

    // ── 既有路徑：本地 session 恢復 ──
    if (!session_.api_key.isEmpty()) {
        // Apply api_key ONLY — do NOT send the stale session_token during
        // startup validation. The server enforces single-session via
        // X-Session-Token; sending a stale one triggers 401 even though
        // the api_key is perfectly valid and permanent.
        auto& http = fincept::HttpClient::instance();
        http.set_auth_header(session_.api_key);
        http.clear_session_token();

        validate_saved_session();
        return;
    }

    set_loading(false);
    emit auth_state_changed();
}

void AuthManager::validate_saved_session() {
    // Validate the saved api_key by fetching the user profile.
    // We intentionally do NOT send X-Session-Token here — the api_key is
    // the permanent credential. A stale session_token would cause a false 401.
    //
    // Flow:
    //   api_key valid (200) → fetch subscription → mark authenticated → save
    //   api_key revoked (401/403) → clear everything → show login
    //   network error → trust cached session data (offline-friendly)
    LOG_INFO("Auth", "Validating saved session via profile fetch (api_key only, no session_token)");
    fetch_user_profile([this] { emit subscription_fetched(); });
}

void AuthManager::fetch_user_profile(std::function<void()> on_done) {
    AuthApi::instance().get_user_profile([this, on_done = std::move(on_done)](ApiResponse r) mutable {
        if (!r.success && (r.status_code == 401 || r.status_code == 403)) {
            // API key is revoked or invalid — force re-login
            LOG_WARN("Auth", "Profile fetch returned 401/403 — API key invalid, clearing session");
            clear_session();
            set_loading(false);
            emit auth_state_changed();
            return;
        }
        if (r.success) {
            const auto data = unwrap_data(r.data);
            session_.user_info = UserProfile::from_json(data);

            // api_key confirmed valid — now restore session_token on HttpClient
            // so subsequent authenticated requests include it. If the old
            // session_token turns out to be stale during usage, SessionGuard
            // will handle recovery without clearing the api_key.
            if (!session_.session_token.isEmpty()) {
                fincept::HttpClient::instance().set_session_token(session_.session_token);
            }
        } else {
            // Network/server error — keep going with cached session data
            LOG_WARN("Auth", "Profile fetch failed (non-auth error) — using cached data");
            session_.authenticated = !session_.api_key.isEmpty();
            // Restore session_token for subsequent requests even in offline mode
            if (!session_.session_token.isEmpty()) {
                fincept::HttpClient::instance().set_session_token(session_.session_token);
            }
        }
        fetch_user_subscription(std::move(on_done));
    });
}

// ── Shared post-auth completion ───────────────────────────────────────────────
// Fetches subscription, syncs state, saves session, then calls on_done().
// Used by login / verify_otp / verify_mfa / session restore.

void AuthManager::complete_auth_flow(std::function<void()> on_done) {
    UserApi::instance().get_user_subscription([this, on_done = std::move(on_done)](ApiResponse r) {
        if (r.success) {
            const auto sub_data = unwrap_data(r.data);
            session_.subscription = UserSubscription::from_json(sub_data);
            session_.has_subscription = !session_.subscription.account_type.isEmpty();
        }
        // Fallback: promote profile account_type into subscription so account_type() is consistent
        if (session_.subscription.account_type.isEmpty() && !session_.user_info.account_type.isEmpty()) {
            session_.subscription.account_type = session_.user_info.account_type;
            session_.subscription.credit_balance = session_.user_info.credit_balance;
            session_.has_subscription = true;
        }
        // Sync user_info from subscription so legacy readers stay consistent
        if (!session_.subscription.account_type.isEmpty())
            session_.user_info.account_type = session_.subscription.account_type;
        if (session_.subscription.credit_balance > 0)
            session_.user_info.credit_balance = session_.subscription.credit_balance;

        if (!session_.api_key.isEmpty())
            session_.authenticated = true;
        save_session();
        auto_configure_fincept_llm();
        set_loading(false);
        if (on_done)
            on_done();
        emit auth_state_changed();
    });
}

void AuthManager::fetch_user_subscription(std::function<void()> on_done) {
    complete_auth_flow(std::move(on_done));
}

// ── Login ────────────────────────────────────────────────────────────────────

void AuthManager::login(const QString& email, const QString& password, bool force_login) {
    set_loading(true);

    LoginRequest req;
    req.email = sanitize_input(email).toLower();
    req.password = password;
    req.force_login = force_login;

    AuthApi::instance().login(req, [this](ApiResponse r) {
        if (!r.success) {
            set_loading(false);
            emit login_failed(r.error.isEmpty() ? "登入失敗" : r.error);
            return;
        }

        const auto data = unwrap_data(r.data);

        if (data["active_session"].toBool()) {
            set_loading(false);
            emit login_active_session(data["message"].toString("You are already logged in on another device."));
            return;
        }

        if (data["mfa_required"].toBool()) {
            set_loading(false);
            emit login_mfa_required();
            return;
        }

        const QString api_key = data["api_key"].toString();
        if (api_key.isEmpty()) {
            set_loading(false);
            emit login_failed("No API key returned from server");
            return;
        }

        const QString session_token = data["session_token"].toString();

        // Set tokens on HttpClient — all subsequent API calls will use them
        apply_tokens(api_key, session_token);

        session_.authenticated = true;
        session_.api_key = api_key;
        session_.session_token = session_token;
        session_.device_id = generate_device_id();

        // Fetch profile then subscription; on_done emits login_succeeded
        fetch_user_profile([this] { emit login_succeeded(); });
    });
}

// ── Device Authorization Flow（RFC 8628）─────────────────────────────────────

void AuthManager::start_device_flow(const QString& email) {
    set_loading(true);
    stop_device_polling(); // 清理先前的輪詢（如有）

    AuthApi::instance().device_request_code(
        sanitize_input(email).toLower(),
        [this](ApiResponse r) {
            if (!r.success) {
                set_loading(false);
                emit device_flow_failed(r.error.isEmpty() ? "無法取得授權碼" : r.error);
                return;
            }

            // 解析回應：device_code, user_code, verification_url, interval
            device_code_ = r.data["device_code"].toString();
            QString user_code = r.data["user_code"].toString();
            QString verification_url = r.data["verification_url"].toString();
            device_poll_interval_ = r.data.value("interval").toInt(5);

            if (device_code_.isEmpty() || user_code.isEmpty()) {
                set_loading(false);
                emit device_flow_failed("伺服器回應格式錯誤");
                return;
            }

            LOG_INFO("Auth", "Device Flow: 取得 user_code " + user_code + " (interval=" + QString::number(device_poll_interval_) + "s)");

            // 啟動輪詢 timer
            if (!device_poll_timer_) {
                device_poll_timer_ = new QTimer(this);
                connect(device_poll_timer_, &QTimer::timeout, this, &AuthManager::on_device_poll_tick);
            }
            device_poll_timer_->start(device_poll_interval_ * 1000);

            set_loading(false);
            emit device_code_received(user_code, verification_url);
        }
    );
}

void AuthManager::cancel_device_flow() {
    stop_device_polling();
    set_loading(false);
}

void AuthManager::on_device_poll_tick() {
    if (device_code_.isEmpty()) {
        stop_device_polling();
        return;
    }

    AuthApi::instance().device_poll(device_code_, [this](ApiResponse r) {
        if (!r.success) {
            // 網路錯誤 — 不停止輪詢，繼續重試
            LOG_WARN("Auth", "Device poll 網路錯誤，繼續重試...");
            return;
        }

        QString status = r.data["status"].toString();

        if (status == "authorization_pending") {
            // 尚未授權，繼續等待
            return;
        }

        if (status == "slow_down") {
            // 增加輪詢間隔 5 秒
            device_poll_interval_ += 5;
            if (device_poll_timer_)
                device_poll_timer_->setInterval(device_poll_interval_ * 1000);
            LOG_INFO("Auth", "Device poll slow_down, interval=" + QString::number(device_poll_interval_) + "s");
            return;
        }

        if (status == "complete") {
            // 授權完成 — 取得 JWT token
            stop_device_polling();
            QString token = r.data["token"].toString();
            if (token.isEmpty()) {
                emit device_flow_failed("授權完成但未收到 token");
                return;
            }

            LOG_INFO("Auth", "Device Flow: 授權完成，設定 JWT token");
            set_loading(true);

            // 設定 JWT（與 SSO 路徑一致）
            is_sso_mode_ = true;
            session_.api_key = token;
            apply_tokens(token, {});

            // 走既有驗證鏈路：fetch profile → auto_configure_fincept_llm
            fetch_user_profile([this] {
                emit device_flow_complete();
                emit login_succeeded();
            });
            return;
        }

        if (status == "expired") {
            stop_device_polling();
            emit device_flow_expired();
            return;
        }

        if (status == "access_denied") {
            stop_device_polling();
            emit device_flow_failed("授權被拒絕");
            return;
        }

        // 未知狀態
        LOG_WARN("Auth", "Device poll 未知狀態: " + status);
    });
}

void AuthManager::stop_device_polling() {
    if (device_poll_timer_) {
        device_poll_timer_->stop();
    }
    device_code_.clear();
    device_poll_interval_ = 5;
}

// ── Signup ───────────────────────────────────────────────────────────────────

void AuthManager::signup(const QString& username, const QString& email, const QString& password, const QString& phone,
                         const QString& country, const QString& country_code) {
    set_loading(true);

    RegisterRequest req;
    req.username = sanitize_input(username).toLower();
    req.email = sanitize_input(email).toLower();
    req.password = password;
    req.phone = phone;
    req.country = country;
    req.country_code = country_code;

    AuthApi::instance().register_user(req, [this](ApiResponse r) {
        set_loading(false);
        if (r.success)
            emit signup_succeeded();
        else
            emit signup_failed(r.error.isEmpty() ? "Registration failed" : r.error);
    });
}

// ── OTP verification ─────────────────────────────────────────────────────────

void AuthManager::verify_otp(const QString& email, const QString& otp) {
    set_loading(true);

    VerifyOtpRequest req;
    req.email = sanitize_input(email).toLower();
    req.otp = sanitize_input(otp);

    AuthApi::instance().verify_otp(req, [this](ApiResponse r) {
        if (!r.success) {
            set_loading(false);
            emit otp_failed(r.error.isEmpty() ? "Verification failed" : r.error);
            return;
        }

        const auto data = unwrap_data(r.data);
        const QString api_key = data["api_key"].toString();
        if (api_key.isEmpty()) {
            set_loading(false);
            emit otp_failed("No API key returned");
            return;
        }

        const QString session_token = data["session_token"].toString();
        apply_tokens(api_key, session_token);

        session_.authenticated = true;
        session_.api_key = api_key;
        session_.session_token = session_token;
        session_.device_id = generate_device_id();

        LOG_INFO("Auth", "OTP verified successfully");
        fetch_user_profile([this] { emit otp_verified(); });
    });
}

// ── MFA verification ─────────────────────────────────────────────────────────

void AuthManager::verify_mfa(const QString& email, const QString& otp) {
    set_loading(true);

    AuthApi::instance().verify_mfa(sanitize_input(email).toLower(), sanitize_input(otp), [this](ApiResponse r) {
        if (!r.success) {
            set_loading(false);
            emit mfa_failed(r.error.isEmpty() ? "MFA verification failed" : r.error);
            return;
        }

        const auto data = unwrap_data(r.data);
        const QString api_key = data["api_key"].toString();
        if (api_key.isEmpty()) {
            set_loading(false);
            emit mfa_failed("No API key returned");
            return;
        }

        const QString session_token = data["session_token"].toString();
        apply_tokens(api_key, session_token);

        session_.authenticated = true;
        session_.api_key = api_key;
        session_.session_token = session_token;
        session_.device_id = generate_device_id();

        LOG_INFO("Auth", "MFA verified successfully");
        fetch_user_profile([this] { emit mfa_verified(); });
    });
}

// ── Forgot password ──────────────────────────────────────────────────────────

void AuthManager::forgot_password(const QString& email) {
    set_loading(true);

    ForgotPasswordRequest req;
    req.email = sanitize_input(email).toLower();

    AuthApi::instance().forgot_password(req, [this](ApiResponse r) {
        set_loading(false);
        if (r.success)
            emit forgot_password_sent();
        else
            emit forgot_password_failed(r.error.isEmpty() ? "發送重設碼失敗" : r.error);
    });
}

// ── Reset password ───────────────────────────────────────────────────────────

void AuthManager::reset_password(const QString& email, const QString& otp, const QString& new_password) {
    set_loading(true);

    ResetPasswordRequest req;
    req.email = sanitize_input(email).toLower();
    req.otp = sanitize_input(otp);
    req.new_password = new_password;

    AuthApi::instance().reset_password(req, [this](ApiResponse r) {
        set_loading(false);
        if (r.success)
            emit password_reset_succeeded();
        else
            emit password_reset_failed(r.error.isEmpty() ? "Password reset failed" : r.error);
    });
}

// ── Logout ───────────────────────────────────────────────────────────────────

void AuthManager::logout() {
    if (is_logging_out_)
        return;
    is_logging_out_ = true;

    if (!session_.api_key.isEmpty()) {
        AuthApi::instance().logout([](ApiResponse) {});
    }

    clear_session();
    is_logging_out_ = false;

    emit logged_out();
    emit auth_state_changed();
}

// ── Session recovery ─────────────────────────────────────────────────────────
// Called by SessionGuard when it gets 401. Instead of immediately logging out,
// we strip the stale session_token and re-validate with api_key only.
// If the api_key is still valid → session recovered, no disruption.
// If api_key is also invalid → truly expired, must re-login.

void AuthManager::attempt_session_recovery(std::function<void(bool)> cb) {
    if (session_.api_key.isEmpty()) {
        if (cb)
            cb(false);
        return;
    }

    LOG_INFO("Auth", "Attempting session recovery with api_key only");

    // Temporarily strip session_token so the validation request doesn't 401
    fincept::HttpClient::instance().clear_session_token();

    AuthApi::instance().get_user_profile([this, cb = std::move(cb)](ApiResponse r) mutable {
        if (r.success) {
            LOG_INFO("Auth", "Session recovery succeeded — api_key is valid");
            const auto data = unwrap_data(r.data);
            session_.user_info = UserProfile::from_json(data);
            session_.authenticated = true;

            // The old session_token was stale. Clear it from our saved state.
            // The app continues with api_key-only auth. A fresh session_token
            // will be obtained on the next explicit login.
            session_.session_token.clear();
            save_session();

            // Don't restore session_token — operate with api_key only
            if (cb)
                cb(true);
        } else if (r.status_code == 401 || r.status_code == 403) {
            LOG_WARN("Auth", "Session recovery failed — api_key is invalid");
            if (cb)
                cb(false);
        } else {
            // Network error — don't force logout, assume transient
            LOG_WARN("Auth", "Session recovery: network error — keeping session alive");
            // Restore session_token since we can't determine if it's stale
            if (!session_.session_token.isEmpty())
                fincept::HttpClient::instance().set_session_token(session_.session_token);
            if (cb)
                cb(true);
        }
    });
}

// ── Refresh user data ────────────────────────────────────────────────────────

void AuthManager::refresh_user_data() {
    if (!session_.authenticated || session_.api_key.isEmpty())
        return;
    // fetch_user_profile chains into fetch_user_subscription automatically
    fetch_user_profile([this] { emit subscription_fetched(); });
}

// ── Auto-configure Fincept LLM provider ──────────────────────────────────────

void AuthManager::auto_configure_fincept_llm() {
    if (session_.api_key.isEmpty())
        return;

    auto& cfg = fincept::AppConfig::instance();

    // 儲存 API key
    fincept::SettingsRepository::instance().set("fincept_api_key", session_.api_key, "auth");

    // 檢查是否已存在 fincept provider
    auto providers = LlmConfigRepository::instance().list_providers();
    bool fincept_exists = false;
    if (providers.is_ok()) {
        for (const auto& p : providers.value()) {
            if (p.provider.toLower() == "fincept") {
                fincept_exists = true;
                break;
            }
        }
    }

    if (!fincept_exists) {
        LlmConfig fincept_llm;
        fincept_llm.provider = "fincept";

        if (cfg.use_saas_auth()) {
            // SaaS 模式：使用 SaaS LLM 代理端點
            fincept_llm.model = "saas-auto";
            fincept_llm.base_url = cfg.saas_base_url() + "/api/fincept/llm";
            LOG_INFO("Auth", "Created fincept LLM provider config (SaaS mode: " + cfg.saas_base_url() + ")");
        } else {
            // 原生模式：使用 MiniMax
            fincept_llm.model = "MiniMax-M2.7";
            fincept_llm.base_url = {};
            LOG_INFO("Auth", "Created fincept LLM provider config");
        }

        LlmConfigRepository::instance().save_provider(fincept_llm);
    }

    // 如果沒有任何 active provider，設為 fincept
    auto active = LlmConfigRepository::instance().get_active_provider();
    bool has_active = active.is_ok() && !active.value().provider.isEmpty();
    if (!has_active)
        LlmConfigRepository::instance().set_active("fincept");
}

} // namespace fincept::auth

// ── JWT 檔案監視（SSO Token Refresh）─────────────────────────────────────────
// Pool Manager 定期透過 docker exec 將新 JWT 寫入 /tmp/.ktw_jwt
// AuthManager 透過 QFileSystemWatcher 監視此檔，檔案變更時自動更新 session

void fincept::auth::AuthManager::setup_jwt_file_watcher() {
    if (jwt_watcher_) return; // 已啟動

    const QString jwt_path = QStringLiteral("/tmp/.ktw_jwt");
    jwt_watcher_ = new QFileSystemWatcher(this);

    // 如果檔案已存在，直接監視
    if (QFile::exists(jwt_path)) {
        jwt_watcher_->addPath(jwt_path);
    }

    // 監視 /tmp 目錄（當檔案尚不存在時，等待 Pool Manager 建立）
    jwt_watcher_->addPath(QStringLiteral("/tmp"));

    connect(jwt_watcher_, &QFileSystemWatcher::fileChanged,
            this, &AuthManager::on_jwt_file_changed);

    // 當目錄變更時（檔案新建），嘗試添加檔案監視
    connect(jwt_watcher_, &QFileSystemWatcher::directoryChanged,
            this, [this, jwt_path](const QString&) {
                if (QFile::exists(jwt_path) && !jwt_watcher_->files().contains(jwt_path)) {
                    jwt_watcher_->addPath(jwt_path);
                    // 檔案剛建立，立即讀取
                    on_jwt_file_changed(jwt_path);
                }
            });

    LOG_INFO("Auth", "SSO: JWT 檔案監視已啟動 (/tmp/.ktw_jwt)");
}

void fincept::auth::AuthManager::on_jwt_file_changed(const QString& path) {
    if (path != QStringLiteral("/tmp/.ktw_jwt")) return;

    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        LOG_WARN("Auth", "SSO: 無法讀取 JWT 檔案: " + path);
        return;
    }

    QTextStream in(&file);
    QString new_token = in.readAll().trimmed();
    file.close();

    if (new_token.isEmpty() || new_token == session_.api_key) {
        return; // 空檔或 token 未變，跳過
    }

    LOG_INFO("Auth", "SSO: 偵測到新 JWT，更新 session...");

    // 更新 session + HttpClient
    session_.api_key = new_token;
    auto& http = fincept::HttpClient::instance();
    http.set_auth_header(new_token);

    // 儲存到 SecureStorage（持久化）
    auto sr = fincept::SecureStorage::instance().store("api_key", new_token);
    if (sr.is_err())
        LOG_WARN("Auth", "SecureStorage: 更新 api_key 失敗");

    // 重新註冊監視（QFileSystemWatcher 在檔案變更後可能移除監視）
    if (!jwt_watcher_->files().contains(path)) {
        jwt_watcher_->addPath(path);
    }

    // 靜默重新驗證 profile（不影響 UI）
    LOG_INFO("Auth", "SSO: 重新驗證 profile...");
    validate_saved_session();
}
