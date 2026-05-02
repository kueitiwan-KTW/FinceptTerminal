#pragma once
// ReportBuilderScreen — full document-owning widget.
//
// Maintains its own component list, metadata, theme, undo stack, autosave,
// and recent files.  LLM/MCP tools may also mutate through the friend
// UndoCommand classes defined below.

#include "core/report/ReportDocument.h"
#include "screens/IStatefulScreen.h"
#include "screens/report_builder/ComponentToolbar.h"
#include "screens/report_builder/DocumentCanvas.h"
#include "screens/report_builder/PropertiesPanel.h"

#include <QPropertyAnimation>
#include <QPushButton>
#include <QSplitter>
#include <QTimer>
#include <QUndoStack>
#include <QWidget>

namespace fincept::screens {

// Type aliases — keep the original names resolving after the model moved to
// core/report so that other headers (DocumentCanvas, PropertiesPanel) which
// already use `using …` aliases do not conflict.
using ReportComponent = ::fincept::report::ReportComponent;
using ReportMetadata  = ::fincept::report::ReportMetadata;
using ReportTheme     = ::fincept::report::ReportTheme;

// Forward declarations for undo commands (defined after the class).
class AddComponentCommand;
class RemoveComponentCommand;
class UpdateComponentCommand;
class MoveComponentCommand;

class ReportBuilderScreen : public QWidget, public IStatefulScreen {
    Q_OBJECT
  public:
    explicit ReportBuilderScreen(QWidget* parent = nullptr);
    ~ReportBuilderScreen() override;

    void restore_state(const QVariantMap& state) override;
    QVariantMap save_state() const override;
    QString state_key() const override { return "report_builder"; }
    int state_version() const override { return 3; }

    // ── Accessors used by UndoCommand classes ────────────────────────────
    QList<ReportComponent>& components() { return components_; }
    const QList<ReportComponent>& components() const { return components_; }
    int& selected() { return selected_; }

    // ── Direct (no-undo-push) operations ─────────────────────────────────
    void add_component_direct(const ReportComponent& comp, int at = -1);
    void remove_component_direct(int index);
    void update_component_direct(int index, const QString& content, const QMap<QString, QString>& config);
    void swap_components(int a, int b);

    void refresh_canvas();
    void refresh_structure();

  private:
    QWidget* build_toolbar();

    // Dialogs
    void show_recent_dialog();
    void show_template_dialog();
    void show_theme_dialog();
    void show_metadata_dialog();

    // User-driven operations
    void add_component(const QString& type);
    void select_component(int index);
    void remove_component_at(int index);
    void duplicate_at(int index);
    void move_up_at(int index);
    void move_down_at(int index);

    // I/O
    void load_report(const QString& path);
    void update_recent(const QString& path);
    QString serialize_to_json() const;
    bool deserialize_from_json(const QString& json);
    void apply_template(const QString& name);

    // ── Document state ───────────────────────────────────────────────────
    QList<ReportComponent> components_;
    int selected_ = -1;
    int next_id_  = 1;
    QUndoStack* undo_stack_ = nullptr;
    ReportMetadata metadata_;
    ReportTheme theme_;
    QString current_file_;
    QTimer* autosave_ = nullptr;
    QString autosave_path_;

    // ── Children ─────────────────────────────────────────────────────────
    ComponentToolbar* comp_toolbar_ = nullptr;
    DocumentCanvas*   canvas_       = nullptr;
    PropertiesPanel*  properties_   = nullptr;
    QSplitter*        splitter_     = nullptr;

    // ── Side-panel collapse state ────────────────────────────────────────
    QPushButton* left_toggle_btn_  = nullptr;
    QPushButton* right_toggle_btn_ = nullptr;
    QPropertyAnimation* left_anim_  = nullptr;
    QPropertyAnimation* right_anim_ = nullptr;
    bool left_collapsed_  = false;
    bool right_collapsed_ = false;
    static constexpr int kLeftPanelWidth  = 240;
    static constexpr int kRightPanelWidth = 280;
    void apply_left_collapsed(bool collapsed, bool animate);
    void apply_right_collapsed(bool collapsed, bool animate);

    friend class AddComponentCommand;
    friend class RemoveComponentCommand;
    friend class UpdateComponentCommand;
    friend class MoveComponentCommand;

  private slots:
    void on_toggle_left();
    void on_toggle_right();
    void on_save();
    void on_open();
    void on_new();
    void on_auto_save();
    void on_export_pdf();
    void on_preview();

  protected:
    void showEvent(QShowEvent* e) override;
    void hideEvent(QHideEvent* e) override;
};

// ── Undo Commands ────────────────────────────────────────────────────────────

class AddComponentCommand : public QUndoCommand {
  public:
    AddComponentCommand(ReportBuilderScreen* screen, const ReportComponent& comp, int insert_at);
    void redo() override;
    void undo() override;
  private:
    ReportBuilderScreen* screen_;
    ReportComponent comp_;
    int insert_at_;
};

class RemoveComponentCommand : public QUndoCommand {
  public:
    RemoveComponentCommand(ReportBuilderScreen* screen, int index);
    void redo() override;
    void undo() override;
  private:
    ReportBuilderScreen* screen_;
    ReportComponent saved_;
    int index_;
};

class UpdateComponentCommand : public QUndoCommand {
  public:
    UpdateComponentCommand(ReportBuilderScreen* screen, int index, const QString& old_content,
                           const QMap<QString, QString>& old_config, const QString& new_content,
                           const QMap<QString, QString>& new_config);
    void redo() override;
    void undo() override;
    bool mergeWith(const QUndoCommand* other) override;
    int id() const override { return 1001; }
  private:
    ReportBuilderScreen* screen_;
    int index_;
    QString old_content_, new_content_;
    QMap<QString, QString> old_config_, new_config_;
};

class MoveComponentCommand : public QUndoCommand {
  public:
    MoveComponentCommand(ReportBuilderScreen* screen, int from, int to);
    void redo() override;
    void undo() override;
  private:
    ReportBuilderScreen* screen_;
    int from_, to_;
};

} // namespace fincept::screens

