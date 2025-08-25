import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))
from bot.parser.hashtags import parse_hashtags


def test_booklet_with_lecture_suggests_board_images():
    text = "#الملزمة\n#المحاضرة_1: عنوان\n#1446"
    _, error = parse_hashtags(text)
    assert error is not None
    assert "#صور_السبورة" in error
