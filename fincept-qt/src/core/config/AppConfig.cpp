#include "core/config/AppConfig.h"
#include <QProcessEnvironment>

namespace fincept {

AppConfig& AppConfig::instance() {
    static AppConfig s;
    return s;
}

AppConfig::AppConfig() : settings_("Fincept", "FinceptTerminal") {}

QVariant AppConfig::get(const QString& key, const QVariant& default_val) const {
    return settings_.value(key, default_val);
}

void AppConfig::set(const QString& key, const QVariant& value) {
    settings_.setValue(key, value);
}

void AppConfig::remove(const QString& key) {
    settings_.remove(key);
}

QString AppConfig::api_base_url() const {
    return settings_.value("api/base_url", "https://api.fincept.in").toString();
}

bool AppConfig::dark_mode() const {
    return settings_.value("ui/dark_mode", true).toBool();
}

int AppConfig::refresh_interval_ms() const {
    return settings_.value("data/refresh_interval_ms", 30000).toInt();
}

// ── KTW SaaS 整合 ─────────────────────────────────────────────────────────

QString AppConfig::saas_base_url() const {
    // 優先讀取環境變數 KTW_SAAS_URL
    QString env_url = QProcessEnvironment::systemEnvironment().value("KTW_SAAS_URL");
    if (!env_url.isEmpty())
        return env_url;
    // 其次讀取 QSettings 持久化設定
    return settings_.value("saas/base_url", "https://platform.ktweb.io").toString();
}

bool AppConfig::use_saas_auth() const {
    // 環境變數 KTW_SAAS_URL 存在 = 啟用 SaaS 認證
    bool env_has = !QProcessEnvironment::systemEnvironment().value("KTW_SAAS_URL").isEmpty();
    if (env_has)
        return true;
    return settings_.value("saas/enabled", false).toBool();
}

} // namespace fincept
