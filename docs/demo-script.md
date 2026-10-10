# 作品集演示脚本（约 5–7 分钟）

## 1. 项目定位（30 秒）

这是一个学生个人项目，使用人工编写的合成劳动争议材料，演示材料解析、结构化整理、来源追溯和离线评测。输出必须人工核验，不是法律意见。

## 2. 运行评测（1 分钟）

```powershell
.\.venv\Scripts\python.exe -m legal_case_agent.evaluation `
  --output reports\synthetic-v1.json `
  --markdown reports\synthetic-v1.md
```

展示 `5/5` 文件解析覆盖和 `5/5` 来源覆盖，并说明这是固定合成数据集的结果。

## 3. 展示待核实项（1 分钟）

打开 `reports\synthetic-v1.md`，展示：

- case-001 的工资支付待核实项；
- case-002 的入职/离职日期冲突；
- 缺少考勤记录的提示。

强调系统保留不确定性，不把冲突材料合并成单一结论。

## 4. 展示 Web 应用（2 分钟）

```powershell
.\.venv\Scripts\python.exe -m uvicorn legal_case_agent.app:app --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:8000`，创建案件，上传 `data\synthetic\case-001` 中的 TXT 文件，生成报告，查看来源和模型端点，再点击“导出 Markdown”。

## 5. 展示质量保障（1 分钟）

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp
```

展示测试通过结果，并说明测试覆盖解析、模型 Schema、任务失败和报告导出。

## 6. 诚实说明限制（30 秒）

当前版本不处理真实客户材料，不提供法律意见，不包含 OCR、完整法律检索、账号权限或云端多租户能力。评测数字只适用于当前合成数据集和代码版本。
