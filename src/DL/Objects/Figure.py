# ---------------------------------------------------------------------------------------------------------------------
# Figure.py
#
# Author      : Peter Heijligers
# Description : Figure
#
#
# Date       Ini Description
# ---------- --- ------------------------------------------------------------------------------------------------------
# 2023-10-20 PHe First creation
# ---------------------------------------------------------------------------------------------------------------------
from src.DL.Objects.TimelineItem import TimelineItem
from src.VL.Functions import map_tableau_color

BAR = 'bar'
LINE = 'line'


class Figure:

    @property
    def label(self):
        return self._label

    @property
    def timeline(self):
        return self._timeline

    @property
    def color_name(self):
        return self._color_name

    @property
    def color_tableau(self):
        return self._color_tableau

    @property
    def figure_type(self):
        return self._figure_type

    @property
    def means(self):
        return self._means

    """
    Setters
    """

    @color_name.setter
    def color_name(self, value: dict):
        self._color_name = value
        self._color_tableau = map_tableau_color(value)

    def __init__(self, label: str, timeline: [TimelineItem]):
        self._label = label.capitalize()
        self._timeline = timeline
        self._color_name = None
        self._color_tableau = None
        self._figure_type = LINE
        self._means = 0.0
        if timeline:
            self._means = sum([item.amount for item in timeline]) / len(timeline)
