#include "screens/dashboard/widgets/EconomicCalendarWidget.h"

#include "core/config/AppConfig.h"
#include "network/http/HttpClient.h"
#include "services/KtwIntelligenceService.h"
#include "ui/theme/Theme.h"

#include <QFrame>
#include <QHBoxLayout>
#include <QJsonObject>
#include <QSet>

namespace fincept::screens::widgets {

EconomicCalendarWidget::EconomicCalendarWidget(QWidget* parent)
    : BaseWidget("經濟日曆", parent, ui::colors::CYAN()) {
    auto* vl = content_layout();
    vl->setContentsMargins(0, 0, 0, 0);
    vl->setSpacing(0);

    // Column headers
    header_widget_ = new QWidget(this);
    auto* hl = new QHBoxLayout(header_widget_);
    hl->setContentsMargins(8, 4, 8, 4);

    auto make_hdr = [&](const QString& text, int stretch, Qt::Alignment align = Qt::AlignLeft) {
        auto* lbl = new QLabel(text);
        lbl->setAlignment(align);
        header_labels_.append(lbl);
        hl->addWidget(lbl, stretch);
    };
    make_hdr("EVENT", 4);
    make_hdr("CTY", 1);
    make_hdr("DATE", 2);
    make_hdr("ACT", 1, Qt::AlignRight);
    make_hdr("FCST", 1, Qt::AlignRight);
    make_hdr("SRC", 1, Qt::AlignRight);  // 來源標示
    make_hdr("IMP", 1, Qt::AlignRight);
    vl->addWidget(header_widget_);

    header_sep_ = new QFrame;
    header_sep_->setFixedHeight(1);
    vl->addWidget(header_sep_);

    // Scrollable list
    scroll_area_ = new QScrollArea;
    scroll_area_->setWidgetResizable(true);

    auto* list_widget = new QWidget(this);
    list_widget->setStyleSheet("background: transparent;");
    list_layout_ = new QVBoxLayout(list_widget);
    list_layout_->setContentsMargins(0, 0, 0, 0);
    list_layout_->setSpacing(0);

    status_label_ = new QLabel("Loading...");
    status_label_->setAlignment(Qt::AlignCenter);
    list_layout_->addWidget(status_label_);
    list_layout_->addStretch();

    scroll_area_->setWidget(list_widget);
    vl->addWidget(scroll_area_, 1);

    connect(this, &BaseWidget::refresh_requested, this, &EconomicCalendarWidget::refresh_data);

    apply_styles();
    set_loading(true);
    refresh_data();
}

void EconomicCalendarWidget::apply_styles() {
    header_widget_->setStyleSheet(QString("background: %1;").arg(ui::colors::BG_RAISED()));
    for (auto* lbl : header_labels_)
        lbl->setStyleSheet(QString("color: %1; font-size: 9px; font-weight: bold; background: transparent;")
                               .arg(ui::colors::TEXT_TERTIARY()));
    header_sep_->setStyleSheet(QString("background: %1;").arg(ui::colors::BORDER_DIM()));
    scroll_area_->setStyleSheet(
        QString("QScrollArea { border: none; background: transparent; }"
                "QScrollBar:vertical { width: 4px; background: transparent; }"
                "QScrollBar::handle:vertical { background: %1; border-radius: 2px; min-height: 20px; }"
                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
            .arg(ui::colors::BORDER_MED()));
    status_label_->setStyleSheet(QString("color: %1; font-size: 10px; padding: 16px; background: transparent;")
                                     .arg(ui::colors::TEXT_TERTIARY()));
}

void EconomicCalendarWidget::on_theme_changed() {
    apply_styles();
    if (!last_events_.isEmpty())
        populate(last_events_);
}

void EconomicCalendarWidget::refresh_data() {
    set_loading(true);
    fincept_events_ = QJsonArray();
    saas_events_ = QJsonArray();
    pending_fetches_ = 1;  // Fincept 原生請求必定有

    // 檢查是否啟用 SaaS 情報室
    if (fincept::KtwIntelligenceService::instance().is_available())
        pending_fetches_ = 2;

    // ── 1. Fincept 原生 API ─────────────────────────────────────────────
    QString url = "https://api.fincept.in/macro/upcoming-events?limit=25";
    fincept::HttpClient::instance().get(url, [this](fincept::Result<QJsonDocument> result) {
        if (result.is_ok()) {
            auto doc = result.value();
            QJsonArray events;
            if (doc.isObject()) {
                auto root = doc.object();
                if (root.contains("data") && root["data"].isObject()) {
                    auto data = root["data"].toObject();
                    if (data.contains("events") && data["events"].isArray())
                        events = data["events"].toArray();
                }
                if (events.isEmpty() && root.contains("data") && root["data"].isArray())
                    events = root["data"].toArray();
                if (events.isEmpty() && root.contains("events") && root["events"].isArray())
                    events = root["events"].toArray();
            } else if (doc.isArray()) {
                events = doc.array();
            }
            // 標記來源為 Fincept
            for (int i = 0; i < events.size(); ++i) {
                auto obj = events[i].toObject();
                obj["_source"] = "FIN";
                events[i] = obj;
            }
            fincept_events_ = events;
        }
        --pending_fetches_;
        if (pending_fetches_ <= 0)
            merge_and_populate();
    });

    // ── 2. SaaS 情報室 API（可用時）──────────────────────────────────────
    if (fincept::KtwIntelligenceService::instance().is_available())
        fetch_saas_data();
}

void EconomicCalendarWidget::fetch_saas_data() {
    using DT = fincept::KtwIntelligenceService::DataType;
    fincept::KtwIntelligenceService::instance().fetch(DT::Calendar, 25,
        [this](fincept::KtwIntelligenceService::IntelligenceResult result) {
            if (result.success) {
                QJsonArray events;
                for (const auto& item : result.items) {
                    QJsonObject obj = item.raw;
                    // 確保基本欄位存在
                    if (!obj.contains("event") && !item.title.isEmpty())
                        obj["event"] = item.title;
                    obj["_source"] = "KTW";  // 標記來源為 KTW SaaS
                    events.append(obj);
                }
                saas_events_ = events;
            }
            --pending_fetches_;
            if (pending_fetches_ <= 0)
                merge_and_populate();
        });
}

void EconomicCalendarWidget::merge_and_populate() {
    set_loading(false);

    // 合併兩路數據
    QJsonArray merged;
    QSet<QString> seen_keys;

    // 先加入 Fincept 原生數據
    for (const auto& v : fincept_events_) {
        auto obj = v.toObject();
        QString key = obj["event"].toString().toLower().trimmed() + "|" + obj["date"].toString();
        if (!seen_keys.contains(key)) {
            seen_keys.insert(key);
            merged.append(v);
        }
    }

    // 再加入 SaaS 數據（去重）
    for (const auto& v : saas_events_) {
        auto obj = v.toObject();
        QString key = obj["event"].toString().toLower().trimmed() + "|" + obj["date"].toString();
        if (!seen_keys.contains(key)) {
            seen_keys.insert(key);
            merged.append(v);
        }
    }

    if (merged.isEmpty()) {
        status_label_->setVisible(true);
        status_label_->setText(tr("No events available"));
        return;
    }

    status_label_->setVisible(false);
    populate(merged);
}

void EconomicCalendarWidget::populate(const QJsonArray& events) {
    last_events_ = events;

    // Clear list
    while (list_layout_->count() > 0) {
        auto* item = list_layout_->takeAt(0);
        if (item->widget())
            item->widget()->deleteLater();
        delete item;
    }

    bool alt = false;
    int count = 0;

    for (const auto& v : events) {
        if (count >= 25)
            break;
        auto e = v.toObject();

        // Real fields: event, country, date, time, importance, actual, forecast, previous
        QString event_name = e["event"].toString().trimmed();
        if (event_name.isEmpty())
            continue;

        QString country = e["country"].toString().toUpper();
        QString date = e["date"].toString();
        QString time_str = e["time"].toString().trimmed();
        QString actual = e["actual"].toString().trimmed();
        QString forecast = e["forecast"].toString().trimmed();
        int imp_int = e["importance"].toInt(0);

        // Date: show as MMM-DD
        QString date_display = date;
        if (date.length() == 10) { // YYYY-MM-DD
            QStringList parts = date.split('-');
            if (parts.size() == 3) {
                static const char* months[] = {"",    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
                int m = parts[1].toInt();
                if (m >= 1 && m <= 12)
                    date_display = QString("%1-%2").arg(months[m]).arg(parts[2]);
            }
        }
        if (!time_str.isEmpty())
            date_display += " " + time_str.left(5);

        // Importance color: 0=dim, 1=low/dim, 2=medium/amber, 3=high/red
        QString imp_color = imp_int >= 3   ? ui::colors::NEGATIVE()
                            : imp_int == 2 ? ui::colors::WARNING()
                                           : ui::colors::TEXT_TERTIARY();
        QString imp_text = imp_int >= 3 ? "HIGH" : imp_int == 2 ? "MED" : imp_int == 1 ? "LOW" : "--";

        auto* row = new QWidget(this);
        row->setStyleSheet(QString("background: %1;").arg(alt ? ui::colors::BG_RAISED() : "transparent"));
        auto* rl = new QHBoxLayout(row);
        rl->setContentsMargins(8, 4, 8, 4);

        // Event name
        QString display_name = event_name;
        if (display_name.length() > 28)
            display_name = display_name.left(26) + "…";
        auto* ev_lbl = new QLabel(display_name);
        ev_lbl->setToolTip(event_name); // full name on hover
        ev_lbl->setStyleSheet(
            QString("color: %1; font-size: 10px; background: transparent;").arg(ui::colors::TEXT_PRIMARY()));
        rl->addWidget(ev_lbl, 4);

        auto* cty_lbl = new QLabel(country);
        cty_lbl->setStyleSheet(QString("color: %1; font-size: 9px; background: transparent;").arg(ui::colors::CYAN()));
        rl->addWidget(cty_lbl, 1);

        auto* date_lbl = new QLabel(date_display);
        date_lbl->setStyleSheet(
            QString("color: %1; font-size: 9px; background: transparent;").arg(ui::colors::TEXT_SECONDARY()));
        rl->addWidget(date_lbl, 2);

        auto* act_lbl = new QLabel(actual.isEmpty() ? "--" : actual);
        act_lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        act_lbl->setStyleSheet(QString("color: %1; font-size: 10px; font-weight: bold; background: transparent;")
                                   .arg(actual.isEmpty() ? ui::colors::TEXT_TERTIARY() : ui::colors::TEXT_PRIMARY()));
        rl->addWidget(act_lbl, 1);

        auto* fcst_lbl = new QLabel(forecast.isEmpty() ? "--" : forecast);
        fcst_lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        fcst_lbl->setStyleSheet(
            QString("color: %1; font-size: 9px; background: transparent;").arg(ui::colors::TEXT_SECONDARY()));
        rl->addWidget(fcst_lbl, 1);

        auto* imp_lbl = new QLabel(imp_text);
        imp_lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        imp_lbl->setStyleSheet(
            QString("color: %1; font-size: 9px; font-weight: bold; background: transparent;").arg(imp_color));
        rl->addWidget(imp_lbl, 1);

        // 數據來源標示
        QString src = e["_source"].toString("FIN");
        QString src_color = (src == "KTW") ? ui::colors::POSITIVE() : ui::colors::TEXT_TERTIARY();
        auto* src_lbl = new QLabel(src);
        src_lbl->setAlignment(Qt::AlignRight | Qt::AlignVCenter);
        src_lbl->setStyleSheet(
            QString("color: %1; font-size: 8px; font-weight: bold; background: transparent;").arg(src_color));
        rl->addWidget(src_lbl, 1);

        list_layout_->addWidget(row);
        alt = !alt;
        ++count;
    }

    list_layout_->addStretch();
}

} // namespace fincept::screens::widgets
