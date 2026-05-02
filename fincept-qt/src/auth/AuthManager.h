#pragma once
#include "auth/AuthTypes.h"

#include <QObject>
#include <QTimer>

#include <functional>

namespace fincept::auth {

/// Central auth state machine.
/// Manages login/signup/MFA flows, session persistence, and validation.
class AuthManager : public QObject {
    Q_OBJECT
  public:
    static AuthManager& instance();

    const SessionData& session() const { return session_; }
    bool is_authenticated() const { return session_.authenticated; }
    bool is_loading() const { return is_loading_; }

    // Auth flows
    void login(const QString& email, const QString& password, bool force_login = false);
    void signup(const QString& username, const QString& email, const QString& password, const QString& phone,
                const QString& country = {}, const QString& country_code = {});
    void verify_otp(const QString& email, const QString& otp);
    void verify_mfa(const QString& email, const QString& otp);
    void forgot_password(const QString& email);
    void reset_password(const QString& email, const QString& otp, const QString& new_password);
    void logout();

    // Device Authorization Flow（RFC 8628 — SaaS 模式專用）
    void start_device_flow(const QString& email);
    void cancel_device_flow();

    // Session management
    void initialize();
    void refresh_user_data();
    void attempt_session_recovery(std::function<void(bool)> cb);

    /// True if user needs to set up a PIN (authenticated but no PIN configured).
    bool needs_pin_setup() const;

    /// True if running in SaaS SSO mode (auto-login via KTW_JWT_TOKEN env var).
    bool is_sso_mode() const { return is_sso_mode_; }

  signals:
    void auth_state_changed();
    void login_succeeded();
    void login_failed(const QString& error);
    void login_mfa_required();
    void login_active_session(const QString& message);
    void signup_succeeded();
    void signup_failed(const QString& error);
    void otp_verified();
    void otp_failed(const QString& error);
    void mfa_verified();
    void mfa_failed(const QString& error);
    void forgot_password_sent();
    void forgot_password_failed(const QString& error);
    void password_reset_succeeded();
    void password_reset_failed(const QString& error);
    void logged_out();
    void session_expired();
    void loading_changed(bool loading);
    void subscription_fetched();

    /// Emitted after successful login when PIN setup is needed.
    void pin_setup_required();

    /// Emitted after login + PIN verify (or setup) — terminal is fully unlocked.
    void terminal_unlocked();

    // Device Flow 信號
    void device_code_received(const QString& user_code, const QString& verification_url);
    void device_flow_complete();
    void device_flow_failed(const QString& error);
    void device_flow_expired();

  private:
    AuthManager();

    void set_loading(bool v);
    void save_session();
    void load_session();
    void clear_session();
    void validate_saved_session();
    void fetch_user_profile(std::function<void()> on_done = {});
    void fetch_user_subscription(std::function<void()> on_done = {});
    void complete_auth_flow(std::function<void()> on_done);
    void auto_configure_fincept_llm();
    QString generate_device_id() const;

    // Device Flow 輪詢
    void on_device_poll_tick();
    void stop_device_polling();
    QJsonObject unwrap_data(const QJsonObject& raw) const;

    SessionData session_;
    bool is_loading_ = true;
    bool is_logging_out_ = false;
    bool is_sso_mode_ = false; // SSO 自動登入模式（容器池注入 KTW_JWT_TOKEN）

    // Device Flow 狀態
    QTimer* device_poll_timer_ = nullptr;
    QString device_code_;
    int device_poll_interval_ = 5; // 秒
};

} // namespace fincept::auth
