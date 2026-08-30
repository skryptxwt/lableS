INDUSTRIAL_QSS = r"""
QMainWindow {
    background: #e8ecef;
    color: #27313a;
    font-family: "Microsoft YaHei UI";
    font-size: 11px;
}

QWidget#centralwidget, QWidget#windowShell {
    background: transparent;
    color: #27313a;
    font-family: "Microsoft YaHei UI";
    font-size: 11px;
}

QWidget#windowShell {
    border: 1px solid rgba(125, 138, 150, 170);
}

QWidget#titleBar {
    background: #d8e1e5;
    border: 0;
}

QWidget#titleToolbar {
    background: transparent;
}

QLabel#windowTitleLabel {
    color: #30383e;
    font-size: 12px;
    font-weight: 600;
}

QWidget#categoryPopup {
    color: #27353e;
    background: rgba(247, 250, 252, 248);
    border: 1px solid rgba(117, 137, 150, 185);
    border-radius: 10px;
}

QWidget#categoryPopupHeader {
    background: transparent;
    border: 0;
}

QLabel#categoryPopupTitle {
    color: #263640;
    background: transparent;
    border: 0;
    font-size: 12px;
    font-weight: 600;
}

QLabel#categoryPopupCurrent {
    min-height: 22px;
    color: #177da3;
    background: rgba(210, 233, 242, 205);
    border: 1px solid rgba(64, 153, 187, 105);
    border-radius: 11px;
    padding: 0 9px;
    font-size: 10px;
}

QPushButton#categoryPopupClose {
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    color: #64747e;
    background: transparent;
    border: 0;
    border-radius: 6px;
    padding: 0;
    font-family: "Segoe UI";
    font-size: 16px;
    font-weight: 400;
}

QPushButton#categoryPopupClose:hover {
    color: #ffffff;
    background: #c95860;
}

QPushButton#categoryPopupClose:pressed {
    background: #ad424a;
}

QListWidget#categoryPopupList {
    color: #2c3942;
    background: rgba(255, 255, 255, 105);
    border: 1px solid rgba(144, 160, 171, 105);
    border-radius: 7px;
    outline: 0;
    padding: 5px;
}

QListWidget#categoryPopupList::item {
    min-height: 30px;
    color: #2c3942;
    background: transparent;
    border: 0;
    border-radius: 6px;
    padding: 2px 9px;
}

QListWidget#categoryPopupList::item:hover {
    color: #1f2c35;
    background: rgba(220, 231, 238, 205);
}

QListWidget#categoryPopupList::item:selected {
    color: #ffffff;
    background: #299bc5;
    border: 0;
}

QListWidget#categoryPopupList QScrollBar:vertical {
    width: 6px;
    margin: 5px 2px;
}

QListWidget#categoryPopupList QScrollBar::handle:vertical {
    min-height: 34px;
    background: rgba(80, 102, 116, 105);
    border-radius: 3px;
}

QListWidget#categoryPopupList QScrollBar::handle:vertical:hover {
    background: rgba(37, 155, 200, 190);
}

QGroupBox {
    background: rgba(248, 250, 252, 62);
    border: 1px solid rgba(150, 163, 174, 165);
    border-radius: 7px;
    margin: 0;
    padding: 0;
}

QGroupBox#horizontalGroupBox {
    background: rgba(251, 252, 253, 138);
    border-radius: 7px;
}

QGroupBox#temp {
    background: rgba(249, 251, 252, 125);
    border: 0;
    border-bottom: 1px solid rgba(125, 141, 153, 115);
    border-radius: 0;
}

QLabel {
    color: #2d3841;
    background: transparent;
}

QLabel[role="sectionTitle"] {
    color: #283740;
    background: rgba(249, 251, 252, 125);
    border: 0;
    border-bottom: 1px solid rgba(125, 141, 153, 115);
    font-size: 12px;
    font-weight: 600;
    padding: 0 12px;
}

QWidget#objectSectionHeader {
    background: rgba(249, 251, 252, 125);
    border: 0;
    border-bottom: 1px solid rgba(125, 141, 153, 115);
}

QPushButton#objectDeleteButton {
    color: #6d7a83;
    background: transparent;
    border: 0;
    border-radius: 5px;
    padding: 0;
}

QPushButton#objectDeleteButton:hover {
    color: #b44750;
    background: rgba(213, 82, 91, 38);
}

QPushButton#objectDeleteButton:pressed {
    background: rgba(213, 82, 91, 70);
}

QPushButton#objectDeleteButton:disabled {
    color: #a8b1b7;
    background: transparent;
}

QLabel#styleControlTitle,
QLabel#styleOptionTitle {
    color: #26343d;
    font-size: 11px;
    font-weight: 600;
}

QWidget#rightSectionPanel {
    background: transparent;
}

QSplitter#rightSectionSplitter {
    background: rgba(247, 249, 251, 72);
}

QSplitter#workspaceSplitter,
QSplitter#contentSectionSplitter,
QWidget#queueSection,
QWidget#canvasSection,
QWidget#workspaceContentSection {
    background: transparent;
    border: 0;
}

QWidget#rightSectionPanel QListWidget {
    background: transparent;
}

QWidget#transparentListViewport {
    background: transparent;
    border: 0;
}

QSplitter#rightSectionSplitter::handle {
    background: transparent;
}

QLabel#label {
    background: transparent;
    border: 1px solid rgba(112, 125, 137, 180);
    border-radius: 5px;
    color: #82909b;
}

QLabel#character_label {
    color: #53616c;
    background: rgba(250, 251, 252, 185);
    border: 1px solid rgba(150, 163, 174, 155);
    border-top: 0;
    padding: 0 12px;
    font-family: "Consolas";
    font-size: 10px;
}

QWidget#hoverSliderControl {
    background: rgba(255, 255, 255, 35);
    border: 1px solid rgba(125, 141, 153, 55);
    border-radius: 5px;
}

QWidget#hoverSliderControl:hover {
    background: rgba(255, 255, 255, 90);
    border-color: rgba(125, 141, 153, 105);
}

QLabel#hoverSliderCaption {
    color: #26343e;
    font-size: 11px;
    font-weight: 600;
}

QLabel#hoverSliderValue {
    color: #344550;
    font-family: "Consolas";
    font-size: 10px;
}

QPushButton {
    min-height: 30px;
    color: #34414b;
    background: rgba(255, 255, 255, 225);
    border: 1px solid rgba(145, 157, 168, 185);
    border-radius: 5px;
    padding: 0 10px;
    font-size: 11px;
    font-weight: 500;
}

QPushButton:hover {
    color: #1f2a32;
    background: rgba(255, 255, 255, 248);
    border-color: #738593;
}

QPushButton:pressed {
    background: rgba(224, 231, 237, 240);
    border-color: #2499c5;
}

QPushButton:disabled {
    color: #a2acb4;
    background: rgba(234, 238, 241, 190);
    border-color: #c3cbd1;
}

QComboBox,
QSpinBox {
    min-height: 28px;
    color: #34414b;
    background: rgba(248, 250, 251, 225);
    border: 1px solid rgba(145, 157, 168, 170);
    border-radius: 5px;
    padding: 0 7px;
    selection-background-color: #dbeaf0;
}

QComboBox:hover,
QSpinBox:hover,
QComboBox:focus,
QSpinBox:focus {
    border-color: #5b9bb5;
    background: rgba(255, 255, 255, 242);
}

QComboBox::drop-down,
QSpinBox::up-button,
QSpinBox::down-button {
    border: 0;
    background: transparent;
}

QPushButton[role="primary"] {
    color: #ffffff;
    background: #249bc8;
    border-color: #1785ad;
}

QPushButton[role="primary"]:hover {
    background: #168bb7;
    border-color: #08769f;
}

QPushButton[role="danger"] {
    color: #a23a41;
    background: rgba(255, 245, 246, 230);
    border-color: #d7a4a8;
}

QPushButton[role="danger"]:hover {
    color: #ffffff;
    background: #c45159;
    border-color: #a83c44;
}

QPushButton[toolbarControl="true"] {
    min-height: 24px;
    max-height: 24px;
    color: #4a535a;
    background: transparent;
    border: 0;
    border-radius: 4px;
    padding: 0 9px;
    font-weight: 400;
}

QPushButton[toolbarControl="true"]:hover {
    color: #20282e;
    background: #e5e7e9;
    border: 0;
}

QPushButton[toolbarControl="true"]:pressed {
    background: #dadddf;
    border: 0;
}

QWidget#hoverSliderPopup {
    color: #26343e;
    background: rgba(250, 252, 253, 245);
    border: 1px solid rgba(128, 143, 154, 125);
    border-radius: 7px;
}

QMenu#backgroundMenu,
QMenu#modelMenu,
QMenu#shortcutMenu,
QMenu#taskMenu {
    color: #303b43;
    background: #f7f8f9;
    border: 1px solid #b8c1c7;
    border-radius: 6px;
    padding: 5px;
    font-family: "Microsoft YaHei UI";
    font-size: 11px;
    font-weight: 400;
}

QMenu#backgroundMenu::item,
QMenu#modelMenu::item,
QMenu#shortcutMenu::item,
QMenu#taskMenu::item {
    min-height: 28px;
    padding: 2px 24px 2px 10px;
    border-radius: 4px;
    font-weight: 400;
}

QMenu#backgroundMenu::item:selected,
QMenu#modelMenu::item:selected,
QMenu#shortcutMenu::item:selected,
QMenu#taskMenu::item:selected {
    color: #18242c;
    background: #e3e8eb;
}

QMenu#backgroundMenu::separator,
QMenu#modelMenu::separator,
QMenu#shortcutMenu::separator,
QMenu#taskMenu::separator {
    height: 1px;
    margin: 4px 8px;
    background: #d2d8dc;
}

QWidget#backgroundOpacityMenu,
QWidget#thumbnailSizeMenu {
    background: transparent;
    border: 0;
}

QWidget#modelConfidenceMenu {
    background: transparent;
    border: 0;
}

QLabel#backgroundOpacityValue,
QLabel#thumbnailSizeValue {
    color: #45545e;
    font-family: "Consolas";
    font-size: 10px;
}

QLabel#modelConfidenceValue {
    color: #45545e;
    font-family: "Consolas";
    font-size: 10px;
}

QSlider[menuSlider="true"]::groove:horizontal {
    height: 4px;
    background: #c4cdd3;
    border-radius: 2px;
}

QSlider[menuSlider="true"]::sub-page:horizontal {
    background: #249bc8;
    border-radius: 2px;
}

QSlider[menuSlider="true"]::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background: #ffffff;
    border: 2px solid #249bc8;
    border-radius: 7px;
}

QWidget#sliderPopupHeader {
    background: transparent;
    border: 0;
}

QLabel#sliderPopupCaption {
    color: #34434d;
    font-size: 11px;
    font-weight: 500;
}

QLabel#sliderPopupValue {
    color: #4b5b65;
    font-family: "Consolas";
    font-size: 10px;
}

QSlider[popupSlider="true"]::groove:horizontal {
    height: 4px;
    background: rgba(98, 115, 127, 75);
    border-radius: 2px;
}

QSlider[popupSlider="true"]::sub-page:horizontal {
    background: #249bc8;
    border-radius: 2px;
}

QSlider[popupSlider="true"]::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background: #ffffff;
    border: 2px solid #249bc8;
    border-radius: 7px;
}

QPushButton[compact="true"] {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    background: transparent;
    border: 0;
    border-radius: 7px;
}

QPushButton[compact="true"]:hover {
    background: rgba(226, 232, 237, 210);
    border: 0;
}

QPushButton[compact="true"]:pressed {
    background: rgba(207, 216, 223, 225);
    border: 0;
}

QPushButton[compact="true"]:checked {
    background: rgba(255, 255, 255, 245);
    border: 1px solid rgba(166, 177, 186, 175);
}

QFrame {
    color: rgba(146, 157, 166, 120);
}

QListWidget {
    color: #35424c;
    background: rgba(247, 249, 251, 72);
    border: 1px solid rgba(150, 163, 174, 160);
    border-top: 0;
    outline: 0;
    padding: 5px;
}

QListWidget::item {
    min-height: 28px;
    color: #24323b;
    background: rgba(255, 255, 255, 168);
    border-radius: 4px;
    padding: 3px 8px;
}

QListWidget::item:hover {
    color: #1d2932;
    background: rgba(220, 230, 237, 225);
}

QListWidget::item:selected {
    color: #ffffff;
    background: #299bc5;
    border-left: 3px solid #087da8;
}

QListWidget#thumbnailWidget::item {
    color: #30414b;
    background: rgba(247, 250, 252, 105);
    border: 1px solid rgba(111, 139, 152, 65);
    border-radius: 5px;
}

QListWidget#thumbnailWidget::item:hover {
    color: #25343d;
    background: rgba(224, 237, 243, 175);
    border-color: rgba(76, 153, 181, 125);
}

QListWidget#thumbnailWidget::item:selected {
    color: #23343e;
    background: rgba(193, 226, 238, 210);
    border: 1px solid rgba(55, 159, 195, 175);
}

QListWidget#thumbnailWidget {
    background: none;
    border: 0;
    outline: 0;
    padding: 5px;
}

QCheckBox {
    color: #3c4852;
    spacing: 5px;
    padding: 0;
    font-size: 11px;
}

QCheckBox:hover {
    color: #17232c;
}

QLineEdit {
    min-height: 24px;
    color: #26323b;
    background: rgba(255, 255, 255, 225);
    border: 1px solid rgba(137, 151, 162, 190);
    border-radius: 5px;
    padding: 0 8px;
    selection-background-color: #249bc8;
}

QLineEdit:focus {
    border: 1px solid #249bc8;
    background: #ffffff;
}

QSlider[compactHover="true"]::groove:horizontal {
    height: 4px;
    background: rgba(109, 124, 136, 85);
    border-radius: 2px;
}

QSlider[compactHover="true"]::sub-page:horizontal {
    background: #249bc8;
    border-radius: 2px;
}

QSlider[compactHover="true"]::handle:horizontal {
    width: 12px;
    margin: -5px 0;
    background: #ffffff;
    border: 2px solid #249bc8;
    border-radius: 7px;
}

QScrollBar:vertical {
    width: 7px;
    margin: 3px 1px;
    background: transparent;
    border: 0;
}

QScrollBar::handle:vertical {
    min-height: 36px;
    background: rgba(73, 91, 103, 105);
    border: 0;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(37, 155, 200, 190);
}

QScrollBar::handle:vertical:pressed {
    background: #168bb7;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    width: 0;
    height: 0;
    border: 0;
    background: transparent;
}

QScrollBar::up-arrow:vertical,
QScrollBar::down-arrow:vertical {
    width: 0;
    height: 0;
    background: transparent;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
    border: 0;
}

QStatusBar {
    color: #53616c;
    background: rgba(249, 251, 252, 205);
    border-top: 1px solid rgba(150, 163, 174, 155);
    font-family: "Consolas";
    font-size: 10px;
}

QToolTip {
    color: #f4f7f9;
    background: #37434d;
    border: 1px solid #657681;
    padding: 5px;
}

QMessageBox {
    background: #f7f9fb;
}
"""
