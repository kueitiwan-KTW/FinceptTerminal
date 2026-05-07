#include "services/crypto/TotpService.h"

#include "core/logging/Logger.h"
#include "python/PythonRunner.h"

#include <QCoreApplication>
#include <QJsonDocument>
#include <QJsonObject>

namespace fincept::services::crypto {

TotpService& TotpService::instance() {
    static TotpService s;
    return s;
}

void TotpService::generate(const QString& secret, TotpCallback cb) {
    if (secret.isEmpty()) {
        if (cb) {
            TotpResult r;
            r.error = QCoreApplication::translate("FinceptTerminal", "empty secret");
            cb(r);
        }
        return;
    }

    const QString script =
        fincept::python::PythonRunner::instance().scripts_dir() + "/exchange/totp_gen.py";

    fincept::python::PythonRunner::instance().run(
        script, {secret},
        [cb = std::move(cb)](const fincept::python::PythonResult& result) {
            TotpResult out;
            if (!result.success) {
                out.error = result.output.isEmpty() ? QCoreApplication::translate("FinceptTerminal", "totp_gen failed")
                                                   : result.output;
                if (cb) cb(out);
                return;
            }
            const auto doc = QJsonDocument::fromJson(result.output.toUtf8());
            if (!doc.isObject()) {
                out.error = QCoreApplication::translate("FinceptTerminal", "malformed totp_gen output");
                if (cb) cb(out);
                return;
            }
            const auto obj = doc.object();
            if (!obj.contains("code")) {
                out.error = QCoreApplication::translate("FinceptTerminal", "totp_gen output missing 'code'");
                if (cb) cb(out);
                return;
            }
            out.success = true;
            out.code = obj.value("code").toString();
            out.valid_for = obj.value("valid_for").toInt();
            if (cb) cb(out);
        });
}

} // namespace fincept::services::crypto
