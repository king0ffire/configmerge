from PyQt6 import QtWidgets, QtGui
from PyQt6.QtGui import QTextCharFormat, QColor
from ui.textviewer import DrapDropTextEdit
import util.helper as helper
import logging
import util.enumtypes as enumtypes
import copy

logger = logging.getLogger(__name__)


class DiffEngine:
    def __init__(self, textedit: DrapDropTextEdit, textedit_2: DrapDropTextEdit):
        self.textedit = textedit
        self.textedit_2 = textedit_2

    def diffandrefresh(self):
        warning_box = None
        try:
            self.textedit.prepareoriginaldict()
            logging.debug(f"debug original dict{self.textedit.originaldict}")
        except helper.InvaildInputError as e:
            warning_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                "warning",
                f"invalid input in left window at line {e+1}",
            )
            warning_box.exec()
        try:
            self.textedit_2.prepareoriginaldict()
        except helper.InvaildInputError as e:
            warning_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Icon.Warning,
                "warning",
                f"invalid input in right window at line {e+1}",
            )
            warning_box.exec()
        if warning_box is None:
            self.textedit_2.diff_dict = helper.diff_dict_by_dict(
                self.textedit_2.originalcontent,
                self.textedit.originaldict
            )
            self.output_diff_dict(self.textedit_2, self.textedit_2.diff_dict)

            self.textedit.diff_dict=helper.diff_dict_by_dict(
                self.textedit.originalcontent,
                self.textedit_2.originaldict
            )
            self.output_diff_dict(self.textedit, self.textedit.diff_dict)
            
            '''
            self.output_diff_by_stringindict(
                self.textedit_2, copy.deepcopy(self.textedit.originaldict)
            )
            self.output_diff_by_stringindict(
                self.textedit, copy.deepcopy(self.textedit_2.originaldict)
            )
            '''

    def output_diff_dict(self,textedit:DrapDropTextEdit,diff_dict:dict[str,dict[str,tuple]],dict_from_opponent=False):
        textedit.editbyuser = False
        textedit.clear()
        green_format = QTextCharFormat()
        green_format.setBackground(QColor("green"))
        yellow_format = QTextCharFormat()
        yellow_format.setBackground(QColor("yellow"))
        red_format = QTextCharFormat()
        red_format.setBackground(QColor("red"))
        normal_format = QTextCharFormat()

        logger.info("output by using dict: orderless")
        cursor = textedit.textCursor()
        
        for section, configs in diff_dict.items():
            logger.debug(f"section:{section}")
            cursor.insertText(f"[{section}]\n", normal_format)
            for key, status in configs.items():
                if status[1] == enumtypes.DiffType.ADDED:
                    logger.debug(
                        f"insert green: section:{section},key:{key},value:{status[0]}"
                    )
                    cursor.insertText(f"{key}= {status[0]}\n", green_format)
                elif status[1] == enumtypes.DiffType.REMOVED:
                    logger.debug(
                        f"insert red: section:{section},key:{key},value:{status[0]}"
                    )
                    cursor.insertText(f"missing:{key}= {status[0]}\n", red_format)
                elif status[1] == enumtypes.DiffType.MODIFIED:
                    logger.debug(
                        f"insert yellow: section:{section},key:{key},value:{status[0]}"
                    )
                    cursor.insertText(f"{key}= {status[0]}\n", yellow_format)
        
        logger.debug("switch to DIFF MODE")
        textedit.textmode = enumtypes.TextMode.DIFF
        textedit.savebutton.setText(
            textedit._translate("MainWindow", f"同步差异到文件(功能未完成)")
        )
        textedit.label.setText(
            textedit._translate(
                "MainWindow", f"差异编辑模式: {textedit.fileoriginalfullpath}"
            )
        )
        textedit.editbyuser = True
        
    
    
    def output_diff_by_stringindict(
        textedit: DrapDropTextEdit, opponent_dict: dict[str, dict[str, str]]
    ):
        textedit.editbyuser = False
        textedit.clear()
        textedit.diff_dict = {}
        green_format = QTextCharFormat()
        green_format.setBackground(QColor("green"))
        yellow_format = QTextCharFormat()
        yellow_format.setBackground(QColor("yellow"))
        red_format = QTextCharFormat()
        red_format.setBackground(QColor("red"))
        normal_format = QTextCharFormat()

        logger.info("start compare diff by string")
        lines = textedit.originalcontent.split("\n")
        current_section = None
        textedit.diff_dict[current_section] = {}
        sectionhasdifference = False
        cursor = textedit.textCursor()
        for line in lines:
            line = line.strip()
            logger.debug(f"line has {line}; section has value:{sectionhasdifference}")
            if line.startswith("[") and line.endswith("]"):
                if current_section in opponent_dict:
                    for key, value in opponent_dict[current_section].items():
                        logger.debug(
                            f"missing section:{current_section},key:{key},value:{value}"
                        )
                        cursor.insertText(f"missing:{key} = {value}\n", red_format)
                        textedit.diff_dict[current_section][key] = (
                            value,
                            enumtypes.DiffType.REMOVED,
                        )
                    del opponent_dict[current_section]
                if sectionhasdifference == False:
                    cursor.movePosition(
                        QtGui.QTextCursor.MoveOperation.PreviousBlock,
                        cursor.MoveMode.KeepAnchor,
                    )
                    logger.debug(f"clearing {cursor.block().text()}")
                    cursor.removeSelectedText()
                    logger.debug(f"after clearing {cursor.block().text()}")
                current_section = line[1:-1]
                logger.debug(f"current section={current_section}")
                textedit.diff_dict[current_section] = {}
                sectionhasdifference = False
                logger.debug(f"new section:{current_section}")
                cursor.insertText(f"{line}\n", normal_format)
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if (
                    current_section in opponent_dict
                    and key in opponent_dict[current_section]
                ):
                    if value != opponent_dict[current_section][key]:
                        logger.debug(
                            f"insert yellow: section:{current_section},key:{key},value:{value}"
                        )
                        cursor.insertText(f"{line}\n", yellow_format)
                        textedit.diff_dict[current_section][key] = (
                            value,
                            enumtypes.DiffType.MODIFIED,
                        )
                        sectionhasdifference = True
                    del opponent_dict[current_section][key]
                else:
                    logger.debug(
                        f"insert green: section:{current_section},key:{key},value:{value}"
                    )
                    cursor.insertText(f"{line}\n", green_format)
                    textedit.diff_dict[current_section][key] = (
                        value,
                        enumtypes.DiffType.ADDED,
                    )
                    sectionhasdifference = True
        if current_section in opponent_dict:
            for key, value in opponent_dict[current_section].items():
                logger.debug(
                    f"missing section:{current_section},key:{key},value:{value}"
                )
                cursor.insertText(f"missing:{key} = {value}\n", red_format)
                textedit.diff_dict[current_section][key] = (
                    value,
                    enumtypes.DiffType.REMOVED,
                )
            del opponent_dict[current_section]
        if sectionhasdifference == False:
            cursor.movePosition(
                QtGui.QTextCursor.MoveOperation.PreviousBlock,
                cursor.MoveMode.KeepAnchor,
            )
            logger.debug(f"clearing {cursor.block().text()}")
            cursor.removeSelectedText()
            logger.debug(f"after clearing {cursor.block().text()}")
        current_section = None

        logger.debug(f"missing sections:{opponent_dict}")
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.MoveAnchor)
        logger.debug(
            f"cursor line number:{cursor.block().lineCount()},cursor block content:{cursor.block().text()}"
        )
        for missing_section in opponent_dict:
            logger.debug(
                f"cursor position:{cursor.position()},cursor block content:{cursor.block().text()}"
            )
            cursor.insertText(f"missing section:[{missing_section}]\n", red_format)
            current_section = missing_section
            textedit.diff_dict[missing_section] = {}
            logger.debug(f"currrent missing section:[{missing_section}]")
            for key, value in opponent_dict[missing_section].items():
                logger.debug(f"=========missing start=========")
                logger.debug(
                    f"cursor position:{cursor.position()},cursor block content:{cursor.block().text()}"
                )
                cursor.insertText(f"missing:{key} = {value}\n", red_format)
                textedit.diff_dict[current_section][key] = (
                    value,
                    enumtypes.DiffType.REMOVED,
                )
                logger.debug(
                    f"cursor position:{cursor.position()},cursor block content:{cursor.block().text()}"
                )
                logger.debug(f"=========missing stop=========")

        logger.debug("switch to DIFF MODE")
        textedit.textmode = enumtypes.TextMode.DIFF
        textedit.savebutton.setText(
            textedit._translate("MainWindow", f"同步差异到文件(功能未完成)")
        )
        textedit.label.setText(
            textedit._translate(
                "MainWindow", f"差异编辑模式: {textedit.fileoriginalfullpath}"
            )
        )
        textedit.editbyuser = True
