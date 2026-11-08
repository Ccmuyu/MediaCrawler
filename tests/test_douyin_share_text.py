# -*- coding: utf-8 -*-
"""抖音分享口令要先抽出短链，短链码不能当作品 ID。"""

from media_platform.douyin.help import extract_douyin_targets, parse_video_info_from_url

SHARE_TEXT = """2.30 02/15 JVl:/ :0pm o@d.AT 嗯 # 172 # 高级姐感
https://v.douyin.com/kI7wdSAdKKs/ 复制此链接，打开Dou音搜索，直接观看视频！"""


def test_share_text_keeps_the_full_short_url():
    assert extract_douyin_targets(SHARE_TEXT) == ["https://v.douyin.com/kI7wdSAdKKs/"]


def test_share_text_short_code_is_not_treated_as_aweme_id():
    url = extract_douyin_targets(SHARE_TEXT)[0]
    info = parse_video_info_from_url(url)

    assert info.url_type == "short"
    assert info.aweme_id == ""


def test_plain_aweme_id_stays_unchanged():
    assert extract_douyin_targets("7525538910311632128") == ["7525538910311632128"]


def test_numbers_inside_share_copy_are_not_aweme_ids():
    targets = extract_douyin_targets(SHARE_TEXT)

    assert "172" not in targets
    assert "2" not in targets
