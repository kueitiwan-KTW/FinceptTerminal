#include "auth/AuthApi.h"

#include "core/config/AppConfig.h"
#include "core/logging/Logger.h"
#include "network/http/HttpClient.h"

#include <QJsonDocument>

namespace fincept::auth {

AuthApi& AuthApi::instance() {
    static AuthApi s;
    return s;
}

// Parse FastAPI/Pydantic 422 validation error detail array into a human-readable string.
// Input: {"detail": [{"loc": ["body", "email"], "msg": "...", "type": "..."}, ...]}
// Output: "Email: value is not a valid email address"
static QString parse_422_detail(const QJsonDocument& doc) {
    if (doc.isNull() || !doc.isObject())
        return {};

    auto root = doc.object();
    if (!root.contains("detail"))
        return {};

    // detail can be a string (plain message) or an array (Pydantic field errors)
    if (root["detail"].isString())
        return root["detail"].toString();

    if (!root["detail"].isArray())
        return {};

    QStringList msgs;
    for (const auto& item : root["detail"].toArray()) {
        auto err = item.toObject();
        QString msg = err["msg"].toString();
        if (msg.isEmpty())
            continue;

        // loc is ["body", "field_name"] — extract the field name (last element)
        QString field;
        auto loc = err["loc"].toArray();
        if (!loc.isEmpty()) {
            // Skip "body" prefix, take the last meaningful segment
            for (int i = loc.size() - 1; i >= 0; --i) {
                QString seg = loc[i].toString();
                if (!seg.isEmpty() && seg != "body") {
                    // Convert snake_case to Title Case for display
                    seg[0] = seg[0].toUpper();
                    seg.replace('_', ' ');
                    field = seg;
                    break;
                }
            }
        }

        if (!field.isEmpty())
            msgs << field + ": " + msg;
        else
            msgs << msg;
    }

    return msgs.join("\n");
}

void AuthApi::request(const QString& method, const QString& endpoint, const QJsonObject& body, Callback cb) {
    auto& http = fincept::HttpClient::instance();

    auto handle = [cb, endpoint](fincept::Result<QJsonDocument> result) {
        // ── No body / network error path ─────────────────────────────────────
        // HttpClient returns err() only when there is NO parseable JSON body.
        // In that case we fall back to status-based messages.
        if (result.is_err()) {
            QString err = QString::fromStdString(result.error());
            int status = 0;
            if (err.startsWith("HTTP_"))
                status = err.mid(5).toInt();

            QString msg;
            switch (status) {
                case 400:
                    msg = "請求無效。請確認您的輸入。";
                    break;
                case 401:
                    msg = "電子郵件或密碼不正確。";
                    break;
                case 403:
                    msg = "存取被拒。您的帳戶可能已被停權。";
                    break;
                case 404:
                    msg = "找不到帳戶。請確認您的電子郵件。";
                    break;
                case 409:
                    msg = "此電子郵件或使用者名稱的帳戶已存在。";
                    break;
                case 422:
                    msg = "請確認您的輸入後重試。";
                    break;
                case 429:
                    msg = "嘗試次數過多。請稍候再試。";
                    break;
                case 500:
                    msg = "伺服器錯誤。請稍後再試。";
                    break;
                case 503:
                    msg = "服務暫時無法使用。請稍後再試。";
                    break;
                default:
                    msg = status > 0 ? QString("請求失敗 (HTTP %1)。請重試。").arg(status)
                                     : "網路錯誤。請檢查您的連線。";
            }
            cb({false, {}, msg, status});
            return;
        }

        // ── JSON body path (covers both success and all HTTP error responses) ─
        auto doc = result.value();
        auto obj = doc.object();

        // Infer HTTP status from body when available (HttpClient doesn't pass status with ok())
        // We detect error bodies by absence of positive signals below.

        // 1. Pydantic 422 field-level validation errors: {"detail": [{loc, msg, type}, ...]}
        if (obj.contains("detail") && obj["detail"].isArray()) {
            QString detail_msg = parse_422_detail(doc);
            if (!detail_msg.isEmpty()) {
                cb({false, obj, detail_msg, 422});
                return;
            }
        }

        // 2. Server business-logic errors: {"success": false, "message": "..."}
        //    This is the primary path for ALL the specific messages:
        //    - "Incorrect password. You have 2 attempt(s) remaining."
        //    - "Too many failed attempts — please try again in 2 minutes."
        //    - "Your account is not verified yet."
        //    - "This username is already taken."
        //    - "An account with this email already exists."
        //    - "Your verification code has expired."
        //    - "Incorrect verification code. You have X attempt(s) remaining."
        //    etc. — the server sends these verbatim and we display them as-is.
        if (obj.contains("success") && !obj["success"].toBool()) {
            // Prefer "message", fall back to "detail" string, then generic
            QString msg = obj.value("message").toString();
            if (msg.isEmpty())
                msg = obj.value("detail").toString();
            if (msg.isEmpty())
                msg = "請求失敗。請重試。";
            cb({false, obj, msg, 200});
            return;
        }

        // 3. Plain {"detail": "string"} error (FastAPI default for non-422 errors)
        if (obj.contains("detail") && obj["detail"].isString()) {
            QString msg = obj["detail"].toString();
            if (!msg.isEmpty()) {
                cb({false, obj, msg, 0});
                return;
            }
        }

        cb({true, obj, {}, 200});
    };

    if (method == "GET")
        http.get(endpoint, handle);
    else if (method == "POST")
        http.post(endpoint, body, handle);
    else if (method == "PUT")
        http.put(endpoint, body, handle);
    else if (method == "DELETE")
        http.del(endpoint, handle);
}

// ── Health ───────────────────────────────────────────────────────────────────

void AuthApi::check_health(std::function<void(bool)> cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        // SaaS 模式：呼叫 SaaS 健康檢查端點
        auto& http = fincept::HttpClient::instance();
        http.saas_get("/api/fincept/health", [cb](fincept::Result<QJsonDocument> r) {
            cb(r.is_ok());
        });
    } else {
        request("GET", "/health", {}, [cb](ApiResponse r) { cb(r.success); });
    }
}

// ── Unauthenticated auth endpoints ───────────────────────────────────────────

void AuthApi::login(const LoginRequest& req, Callback cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        // SaaS 模式：呼叫 /api/fincept/auth
        auto& http = fincept::HttpClient::instance();
        http.saas_post("/api/fincept/auth", req.to_json(), [cb](fincept::Result<QJsonDocument> r) {
            if (r.is_err()) {
                cb({false, {}, QString::fromStdString(r.error()), 0});
                return;
            }
            auto obj = r.value().object();
            bool success = obj["success"].toBool();
            if (!success) {
                cb({false, obj, obj["error"].toString("Login failed"), 403});
                return;
            }
            // SaaS 回傳格式：{success: true, data: {api_key, session_token, ...}}
            cb({true, obj, {}, 200});
        });
    } else {
        request("POST", "/user/login", req.to_json(), cb);
    }
}

void AuthApi::register_user(const RegisterRequest& req, Callback cb) {
    request("POST", "/user/register", req.to_json(), cb);
}

void AuthApi::verify_otp(const VerifyOtpRequest& req, Callback cb) {
    request("POST", "/user/verify-otp", req.to_json(), cb);
}

void AuthApi::forgot_password(const ForgotPasswordRequest& req, Callback cb) {
    request("POST", "/user/forgot-password", req.to_json(), cb);
}

void AuthApi::reset_password(const ResetPasswordRequest& req, Callback cb) {
    request("POST", "/user/reset-password", req.to_json(), cb);
}

void AuthApi::verify_mfa(const QString& email, const QString& otp, Callback cb) {
    QJsonObject body;
    body["email"] = email;
    body["otp"] = otp;
    request("POST", "/user/verify-mfa", body, cb);
}

void AuthApi::get_auth_status(Callback cb) {
    request("GET", "/auth/status", {}, cb);
}

// ── Authenticated endpoints (HttpClient carries X-API-Key + X-Session-Token) ─

void AuthApi::logout(Callback cb) {
    request("POST", "/user/logout", {}, cb);
}

void AuthApi::session_pulse(Callback cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        auto& http = fincept::HttpClient::instance();
        http.saas_get("/api/fincept/pulse", [cb](fincept::Result<QJsonDocument> r) {
            if (r.is_err()) {
                cb({false, {}, "Pulse failed", 0});
                return;
            }
            cb({true, r.value().object(), {}, 200});
        });
    } else {
        request("GET", "/user/session-pulse", {}, cb);
    }
}

void AuthApi::get_user_profile(Callback cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        auto& http = fincept::HttpClient::instance();
        http.saas_get("/api/fincept/profile", [cb](fincept::Result<QJsonDocument> r) {
            if (r.is_err()) {
                cb({false, {}, QString::fromStdString(r.error()), 0});
                return;
            }
            auto obj = r.value().object();
            bool success = obj["success"].toBool();
            cb({success, obj, obj["error"].toString(), success ? 200 : 401});
        });
    } else {
        request("GET", "/user/profile", {}, cb);
    }
}

void AuthApi::update_user_profile(const QJsonObject& data, Callback cb) {
    request("PUT", "/user/profile", data, cb);
}

void AuthApi::validate_api_key(Callback cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        auto& http = fincept::HttpClient::instance();
        http.saas_get("/api/fincept/validate", [cb](fincept::Result<QJsonDocument> r) {
            if (r.is_err()) {
                cb({false, {}, "Token invalid", 401});
                return;
            }
            auto obj = r.value().object();
            cb({obj["valid"].toBool(), obj, {}, 200});
        });
    } else {
        request("GET", "/auth/validate", {}, cb);
    }
}

void AuthApi::regenerate_api_key(Callback cb) {
    request("POST", "/user/regenerate-api-key", {}, cb);
}

// ── Device Authorization Flow（RFC 8628）─────────────────────────────────────

void AuthApi::device_request_code(const QString& email, Callback cb) {
    QJsonObject body;
    body["email"] = email;
    auto& http = fincept::HttpClient::instance();
    http.saas_post("/api/fincept/device/code", body, [cb](fincept::Result<QJsonDocument> r) {
        if (r.is_err()) {
            QString err = QString::fromStdString(r.error());
            int status = 0;
            if (err.startsWith("HTTP_"))
                status = err.mid(5).toInt();
            cb({false, {}, status == 403 ? "此帳號無法使用 Device Flow" : "網路連線失敗", status});
            return;
        }
        auto obj = r.value().object();
        // 錯誤回應帶 error 欄位
        if (obj.contains("error")) {
            cb({false, obj, obj["error"].toString(), 400});
            return;
        }
        cb({true, obj, {}, 200});
    });
}

void AuthApi::device_poll(const QString& device_code, Callback cb) {
    QJsonObject body;
    body["device_code"] = device_code;
    auto& http = fincept::HttpClient::instance();
    http.saas_post("/api/fincept/device/poll", body, [cb](fincept::Result<QJsonDocument> r) {
        if (r.is_err()) {
            cb({false, {}, "網路連線失敗", 0});
            return;
        }
        auto obj = r.value().object();
        // poll 回應永遠帶 status 欄位，直接傳回讓 caller 判斷
        cb({true, obj, obj.value("error").toString(), 200});
    });
}

// ── Subscription / payment ────────────────────────────────────────────────────

void AuthApi::get_subscription_plans(Callback cb) {
    auto& cfg = fincept::AppConfig::instance();
    if (cfg.use_saas_auth()) {
        auto& http = fincept::HttpClient::instance();
        http.saas_get("/api/fincept/plans", [cb](fincept::Result<QJsonDocument> r) {
            if (r.is_err()) {
                cb({false, {}, "取得方案失敗", 0});
                return;
            }
            cb({true, r.value().object(), {}, 200});
        });
    } else {
        request("GET", "/cashfree/plans", {}, cb);
    }
}

void AuthApi::generate_checkout_token(const QString& plan_id, Callback cb) {
    QJsonObject body;
    body["plan_id"] = plan_id;
    request("POST", "/user/generate-checkout-token", body, cb);
}

} // namespace fincept::auth
