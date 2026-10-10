import pytest

from legal_case_agent.db import connect, create_case, get_case, init_db
from legal_case_agent.storage import UploadError, save_upload


def test_create_and_read_case(tmp_path):
    connection = connect(tmp_path / "app.db")
    init_db(connection)
    case_id = create_case(connection, "张某劳动争议")
    assert get_case(connection, case_id)["name"] == "张某劳动争议"


def test_init_db_marks_interrupted_runs_failed(tmp_path):
    connection = connect(tmp_path / "app.db")
    init_db(connection)
    connection.execute("INSERT INTO cases VALUES (?, ?, ?, ?, ?)", ("case", "测试", "draft", "now", "now"))
    connection.execute("INSERT INTO analysis_runs VALUES (?, ?, ?, ?, ?, ?, ?)", ("run", "case", "running", "model", None, "now", None))
    connection.commit()
    init_db(connection)
    run = connection.execute("SELECT status, error, finished_at FROM analysis_runs WHERE id = 'run'").fetchone()
    assert run["status"] == "failed"
    assert run["error"] == "服务重启，分析任务已终止"
    assert run["finished_at"]


def test_safe_upload(tmp_path):
    stored = save_upload("case1", "../工资记录.txt", "工资 8000".encode(), tmp_path, 1)
    assert stored.original_name == "工资记录.txt"
    assert stored.path.parent == (tmp_path / "cases" / "case1" / "documents").resolve()


@pytest.mark.parametrize("name", ["x.exe", "x", "x.sh"])
def test_rejects_unsupported_upload(tmp_path, name):
    with pytest.raises(UploadError, match="不支持"):
        save_upload("case1", name, b"x", tmp_path, 1)


def test_rejects_mismatched_content_type(tmp_path):
    with pytest.raises(UploadError, match="不匹配"):
        save_upload("case1", "伪装.pdf", b"text", tmp_path, 1, "text/plain")
