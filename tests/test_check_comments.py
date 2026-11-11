# -*- coding: utf-8 -*-
"""tools.check_comments 的判定。"""

from tools.check_comments import check_source


def test_shallow_docstring_is_flagged():
    source = '''
def get_name(user_id: str) -> str:
    """获取文件名。"""
    return user_id
'''
    issues = check_source(source, lines={2, 3})

    assert any("翻译函数名" in issue.message for issue in issues)


def test_reason_docstring_passes():
    source = '''
def creator_file_stem(item: str) -> str:
    """同一创作者目录下用作品 ID 做文件名。

    保留 -durl 后缀，避免和合流文件同名后被跳过。
    """
    return item
'''
    assert check_source(source, lines={2, 3, 4, 5}) == []


def test_annotation_restatement_is_flagged():
    source = '''
def save_note(note_id: str) -> None:
    """
    Args:
        note_id: 笔记 ID
    Returns:
        None: 无
    """
    return None
'''
    issues = check_source(source, lines={2, 3, 4, 5, 6, 7})

    assert any("复述参数注解" in issue.message for issue in issues)


def test_echo_comment_is_flagged():
    source = '''
def create_one() -> None:
    """创建一个爬虫实例，平台名不在表里时直接报错。"""
    # create_crawler platform
    crawler = create_crawler(platform=platform)
'''
    issues = check_source(source, lines={4})

    assert any("复述下一行" in issue.message for issue in issues)


def test_reason_comment_is_kept():
    source = '''
def open_db(option: str) -> None:
    """数据库保存模式下自动建表。"""
    # 数据库保存模式下自动建表，避免首次运行时出现 no such table 错误
    if option == "sqlite":
        init_db(option)
'''
    assert check_source(source, lines={4}) == []


def test_mixed_prose_is_flagged():
    source = '''
def run() -> None:
    """启动任务。"""
    # 这里会 retry the request when the server fails
    send()
'''
    issues = check_source(source, lines={4})

    assert any("中英文" in issue.message for issue in issues)


def test_identifier_inside_chinese_comment_is_kept():
    source = '''
def folder(sec_uid: str) -> str:
    """创作者目录名。优先 sec_uid，与主页链接里的创作者 ID 一致。"""
    return sec_uid
'''
    assert check_source(source, lines={2, 3}) == []


def test_old_function_without_docstring_is_ignored_when_def_line_not_in_diff():
    source = '''
def get_name() -> str:
    return "x"

def new_func() -> str:
    """返回新的目录名，避免和已有视频文件重名。"""
    return "y"
'''
    issues = check_source(source, lines={6, 7})

    assert issues == []
