#pragma once
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QStackedWidget>
#include <QTimer>
#include <QWidget>

namespace fincept::screens {

/// Login screen — email/password, MFA step, force-login for active sessions.
/// Obsidian design: sharp corners, monospace, no shadows, terminal aesthetic.
class LoginScreen : public QWidget {
    Q_OBJECT
  public:
    explicit LoginScreen(QWidget* parent = nullptr);

  signals:
    void navigate_register();
    void navigate_forgot_password();

  private:
    QLineEdit* email_input_ = nullptr;
    QLineEdit* password_input_ = nullptr;
    QPushButton* login_btn_ = nullptr;
    QLabel* error_label_ = nullptr;
    QPushButton* show_pw_btn_ = nullptr;

    QWidget* mfa_page_ = nullptr;
    QLineEdit* mfa_input_ = nullptr;
    QPushButton* mfa_verify_btn_ = nullptr;
    QLabel* mfa_error_ = nullptr;

    QWidget* conflict_page_ = nullptr;
    QLabel* conflict_msg_ = nullptr;

    QStackedWidget* pages_ = nullptr;

    void build_login_page();
    void build_mfa_page();
    void build_conflict_page();
    void build_device_page();

    void show_error(const QString& msg);
    void clear_error();
    void set_loading(bool loading);

    // SaaS 模式狀態
    bool is_saas_mode_ = false;

    // Device Flow 頁面元件
    QWidget* device_page_ = nullptr;
    QLabel* device_code_label_ = nullptr;
    QLabel* device_status_label_ = nullptr;
    QPushButton* device_open_browser_btn_ = nullptr;
    QString device_verification_url_;
    QTimer* device_dot_timer_ = nullptr;
    int device_dot_count_ = 0;

  protected:
    void paintEvent(QPaintEvent* event) override;
    /// Wipe email/password/MFA fields whenever the screen leaves the stack so
    /// credentials do not linger across logout → login cycles.
    void hideEvent(QHideEvent* event) override;

  private slots:
    void on_login();
    void on_mfa_verify();
    void on_force_login();
    void on_login_succeeded();
    void on_login_failed(const QString& error);
    void on_mfa_required();
    void on_active_session(const QString& msg);
    void on_mfa_verified();
    void on_mfa_failed(const QString& error);

    // Device Flow slots
    void on_device_code_received(const QString& user_code, const QString& verification_url);
    void on_device_flow_complete();
    void on_device_flow_failed(const QString& error);
    void on_device_flow_expired();
};

} // namespace fincept::screens
