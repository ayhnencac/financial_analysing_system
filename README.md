# FinAgent Platform

七个金融投研赛题共用的 Agent 平台代码仓库。当前版本是可运行的第一阶段骨架：提供七个独立入口、统一入库和证据对象、持久化运行记录、模型网关、确定性财务公式与 CLI。项目整体设计见[架构文档](七赛题统一金融投研Agent平台架构设计.md)。

## 当前实现范围

| 业务线 | 当前状态 |
|---|---|
| ① 文档结构化 | `L1_FORMATS` 可按字节签名识别损坏 JSON、伪 PDF、扫描件和 GB18030 文本，并把文档内指令保存为不可信内容；`L1_VERSION` 可审查更正与冲突；`L1_PUBLIC` 可交付公开年报目录状态与页级已核验字段。可选本地 Tesseract OCR 会保存行级转写、坐标、置信度和低置信候选，仍不直接产生财务事实。 |
| ② 财报分析 | `L2_RATIOS` 可复算十项财务与估值指标；`L2_EDGE` 会拒绝缺失、零值/负值、不同行期间、范围和币种的无效计算；`L2_MAOTAI` 已支持样例中经页级核验的真实年报字段；`L2_PUBLIC` 会在缺少可核验字段时输出资料覆盖和缺口。 |
| ④ 估值、⑤ 研报纠错 | `L4_DCF` 支持 FCFF DCF 与九格敏感性并拒绝无效永续增长参数；`L4_PUBLIC` 在真实年报字段、估值日市场数据、资本结构或预测缺失时交付模型适配和补料清单，不输出公允价值；`L5_ERRORS`、`L5_CONTROL`、`L5_VERSION` 分别处理错误、误报控制和更正重算。 |
| ③ 产业影响 | `L3_COPPER` 可根据事件、产业链、套保和转嫁假设复算年化未覆盖成本情景；`L3_NEWS` 会把匿名媒体、意向订单和收入确认条件分开；`L3_POLICY` 从国务院原文提取行业级方向、时点和公司级证据缺口。三者均不会把未验证材料写成公司业绩。 |
| ⑥ 投资备忘录、⑦ 报告质量 | `L6_MEMO`、`L6_MISSING` 可输出事实/假设、失效条件、监测和资料缺口；`L6_PUBLIC` 在真实资料不完整时只交付受限研究计划。`L7_COMPARE`、`L7_COVERAGE` 用固定 rubric 比较报告并单列核验覆盖；`L7_PUBLIC` 会先区分财务披露和研究报告，禁止按篇幅或格式给披露文件评分。 |

这些状态是有意公开的能力边界。运行时不会将尚未通过字段核验、OCR 或领域审查的草稿标记为正式分析。

## 业务规范与评价

`金融投研智能体体系构建思路.md` 的第 6.1 至 6.7 节是七条业务线的主规范；第一、第二条另附各自的专项构建文档。`tools/build_business_specs.py` 将完整流程、方法、交付和评价章节编译到 `finagent/data/business_specifications.v1.json`，把第 2、5、7、9 节共同规则编译到 `platform_policy.v1.json`，保留文件哈希与原文节号。修改原始规范后需重新运行 `python tools/build_business_specs.py`，检查生成差异并运行测试。代码从打包快照读取规范，安装后也无需访问仓库根目录的 Markdown。

每次运行的 `run_manifest` 保存业务规范版本和来源哈希，`spec_assessment` 保存逐阶段、逐交付物和逐评价项清单。当前清单状态一律为 `not_assessed`，只表示已纳入待验证范围；运行事件和 `result` 才记录实际完成的操作。规范中的评价指标是项目拟议标准，尚无权重、阈值或官方评分，因此平台不生成自证质量分数。第七条的清单评价的是平台能力，不等同于其将来用于评价研究报告的评分规则。

## 本地运行

要求 Python 3.12。基础依赖为 Pydantic 2 和 HTTPX；无需数据库服务。

```powershell
python -m pip install -e '.[dev]'
python -m finagent lines
python -m finagent run 1 examples/financial_report.json --as-of 2026-04-01 --entity-id demo:000001
python -m finagent run 2 examples/financial_report.json --as-of 2026-04-01 --entity-id demo:000001
python -m pytest -q
```

若需要 PDF、XLSX 和 OCR 适配器，使用仓库内的隔离环境；它不会修改全局 Python、`PATH` 或模型环境变量：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev,documents,ocr,spreadsheets]'
.\.venv\Scripts\python.exe -m pytest -q
```

`pytesseract` 只是本地引擎适配器，扫描件还需要 Tesseract 可执行文件和所需语言包。当前机器已验证 `D:\late\tesseract.exe`（Tesseract 5.4.0，`chi_sim+eng`）；运行时显式传入路径，不需要修改系统 `PATH`：

```powershell
.\.venv\Scripts\python.exe -m finagent process-ocr OCR_JOB_ID --language chi_sim+eng --tesseract-cmd D:\late\tesseract.exe
```

## 真实数据试点

已提供目录驱动的试点入库入口：[数据接入试点规范](数据接入试点规范.md)。[真实公司试点数据需求清单](真实公司试点数据需求清单.md) 定义了首批数据、金标、市场快照、版本、许可和拆分要求。目录记录来源、许可、时点、版本与内容 hash；PDF、XLSX、XML/XBRL 的解析结果会进入候选队列，可用 `finagent candidates DOCUMENT_ID` 查询。PDF 解析器会在相邻同列数续表中继承表头、单位和范围，并保留继承链定位；无法确定表头的表不会生成候选。XBRL 可按版本化 taxonomy map 再生成带字段、单位、期间和范围提示的候选。只有带页级原文定位和核验状态的 `finagent.verified-financial.v1` 字段文件才能进入事实库。PDF 文本层和表格解析是可选能力，安装 `.[documents]` 后才启用，且解析结果仍只是候选材料。

```powershell
python -m finagent catalog-validate --catalog examples/pilot_catalog.example.json
python -m finagent catalog-ingest --catalog examples/pilot_catalog.example.json
python -m finagent pilot-readiness --catalog pilot-data\catalog\sample_public_2024_catalog.json
python -m finagent pilot-label-templates --catalog pilot-data\catalog\sample_public_2024_catalog.json --output-dir pilot-data\labels\sample_public_2024
python -m finagent candidates DOCUMENT_ID
python -m finagent map-xbrl --document-id DOCUMENT_ID --taxonomy-map examples/xbrl_taxonomy_map.example.json
python -m finagent apply-review --review path\to\candidate_review.json
python -m finagent ocr-jobs --status queued
python -m finagent process-ocr OCR_JOB_ID --language chi_sim+eng --tesseract-cmd .tools\tesseract\tesseract.exe
python -m finagent ocr-transcript OCR_JOB_ID
python -m finagent requeue-ocr OCR_JOB_ID
python -m finagent fact-conflicts --entity-id ENTITY_ID --as-of YYYY-MM-DD
python -m finagent apply-resolution --resolution path\to\fact_resolution.json
```

`finagent.pilot-catalog.v1` 可选 `source_root` 指向经过批准的只读原件目录，原件无需复制到仓库；每个条目可带 `dataset_split: train|dev|test`。目录校验拒绝把同一公司或其同一披露文件家族拆到不同集合。`pilot-readiness` 只报告报告期覆盖，不把解析结果当作金标；`pilot-label-templates` 生成字段完整、数值为空的审核包，只有人工填写页、表、行、列、原文摘录和审核理由后才能进入事实层。

### 公开 SEC EDGAR 小规模采集

`collect-sec-edgar` 只访问 SEC 的公开结构化 submissions、companyfacts API 和对应归档文件 URL，不抓取搜索网页，不处理登录、验证码、反爬或 robots 限制。默认是**零联网的 dry-run**；只有显式传入 `--execute` 才会发送请求。执行时必须传入包含联系邮箱的真实 `User-Agent`，并遵循 SEC 的访问条款和速率要求。

采集器的总下载配额默认且硬限制为 `2 GiB`，并按输出目录已有文件、每个响应和流式内容逐字节核验；同时限制单文件、请求数、每秒请求数、超时和重试次数。它只下载少量被 submissions 元数据确认的申报主文档，并生成 `pilot_catalog.sec_edgar.json`。原件尚未入库，也不会直接产生候选或事实。

```powershell
# 默认只展示将访问的官方端点，不联网，也不创建 .finagent 状态库
.\.venv\Scripts\python.exe -m finagent collect-sec-edgar --cik 320193 --output-dir public_data

# 先从一家公司的一份 10-K 开始；请替换为你的组织和可联系邮箱
.\.venv\Scripts\python.exe -m finagent collect-sec-edgar --cik 320193 --forms 10-K --max-filings 1 --output-dir public_data --user-agent 'YourOrg research@example.com' --execute

# 下载成功后仍需先校验和入库，之后才进入解析候选与人工审核流程
.\.venv\Scripts\python.exe -m finagent catalog-validate --catalog public_data\pilot_catalog.sec_edgar.json
.\.venv\Scripts\python.exe -m finagent catalog-ingest --catalog public_data\pilot_catalog.sec_edgar.json
```

### 公开巨潮年报小规模采集

`collect-cninfo-annual-reports` 只调用巨潮资讯的公告查询接口和其返回的 PDF 原件地址。默认目标是试点五家公司，目录请求以“证券代码,机构 ID”严格限定到单一公司，只选择指定年度的中文正式年报，排除摘要、英文版、更正和修订版。命令默认 dry-run；执行时受与 SEC 相同的 2 GiB 总配额、单文件、请求数、速率、超时和重试限制。下载文件只会生成原件与 `pilot_catalog.cninfo.json`，不会直接产生财务事实。

```powershell
# 零联网检查默认五家公司 FY2022-FY2023 的查询计划
.\.venv\Scripts\python.exe -m finagent collect-cninfo-annual-reports

# 本机实际试点使用 0.2 GiB 子配额；可重复执行，已有原件按路径跳过
.\.venv\Scripts\python.exe -m finagent collect-cninfo-annual-reports --output-dir public_data\cninfo --fiscal-years 2022,2023 --quota-gib 0.2 --max-file-mib 30 --max-requests 25 --rate-limit 1 --execute

# 将两个只读来源目录合并为一个无复制的三年试点目录，再解析到候选层
.\.venv\Scripts\python.exe -m finagent catalog-merge --catalog pilot-data\catalog\sample_public_2024_catalog.json --catalog public_data\cninfo\pilot_catalog.cninfo.json --output pilot-data\catalog\real_three_years_catalog.json --pilot-id cn-five-issuer-2022-2024-pilot
.\.venv\Scripts\python.exe -m finagent --state-dir .finagent-pilot-real catalog-ingest --catalog pilot-data\catalog\real_three_years_catalog.json
```

`catalog-merge` 只重写目录中的相对定位，使其指向两个既有根目录的共同祖先；不会复制原始 PDF。合并后的 `real_three_years_catalog.json` 覆盖五家公司 FY2022-FY2024，并保留公司级数据集拆分。

## 样例库开发闭环

将交付包解压到 `.finagent-sample/` 后，样例库作为只读语料使用。`run-task` 从任务表读取业务线、截止日、原文绑定和预期输出字段；先校验已解析状态与时点，合格材料再以内容哈希登记到本地证据库。未来资料、解析失败和发布日期未知的材料不会进入专业计算。

```powershell
python -m finagent sample-tasks --corpus .finagent-sample
python -m finagent run-task --corpus .finagent-sample L2_RATIOS
python -m finagent evaluate --corpus .finagent-sample RUN_ID
python -m finagent run-task --corpus .finagent-sample L4_DCF
python -m finagent run-task --corpus .finagent-sample L4_INVALID
python -m finagent run-task --corpus .finagent-sample L1_VERSION
python -m finagent run-task --corpus .finagent-sample L1_FORMATS
python -m finagent run-task --corpus .finagent-sample L2_EDGE
python -m finagent run-task --corpus .finagent-sample L3_COPPER
python -m finagent run-task --corpus .finagent-sample L3_NEWS
python -m finagent run-task --corpus .finagent-sample L3_POLICY
python -m finagent run-task --corpus .finagent-sample L4_PUBLIC
python -m finagent run-task --corpus .finagent-sample L5_ERRORS
python -m finagent run-task --corpus .finagent-sample L6_PUBLIC
python -m finagent run-task --corpus .finagent-sample L7_PUBLIC
```

当前 22 个样例任务都有专项 flow：`L1_FORMATS`、`L1_VERSION`、`L1_PUBLIC`；`L2_RATIOS`、`L2_EDGE`、`L2_MAOTAI`、`L2_PUBLIC`；`L3_COPPER`、`L3_NEWS`、`L3_POLICY`；`L4_DCF`、`L4_INVALID`、`L4_PUBLIC`；`L5_ERRORS`、`L5_CONTROL`、`L5_VERSION`；`L6_MEMO`、`L6_MISSING`、`L6_PUBLIC`；`L7_COMPARE`、`L7_COVERAGE`、`L7_PUBLIC`。其中独立参考库已通过 L1 多格式和版本、L2 比率和真实年报字段、L3 成本情景、L4 DCF 与无效参数、L5 错误与误报控制、L6 备忘录约束、L7 报告排序。开放型或真实资料型任务当前通过输出契约，但样例库没有独立金标；`L1_FORMATS` 的扫描合同 OCR 参考会保持 `not_assessed`，直到接入真正的 OCR。生产级解析与大规模数据接入缺口见 `当前缺口与样例验收计划.md`。运行时为每个样例任务保存 `output_contract_acceptance`；缺少任务声明的必填字段时，任务不会保持 `completed`。`evaluate` 独立读取交付包内的 `评测参考.sqlite`，不会将参考答案传给执行节点。

所有运行数据默认保存在工作目录的 `.finagent/`，包括原件对象、SQLite 元数据、事件与成果。可在命令前添加 `--state-dir PATH` 指定位置；用 `python -m finagent show RUN_ID` 查看结果和日志。再次使用同一原件会按 SHA-256 复用，并在任务事件中记录。

### 可恢复工作流与审核闭环

每个业务运行现在会持久化两个 DAG 节点：`execute_flow` 与依赖其 checkpoint 的 `review_findings`。节点记录声明幂等键、最大尝试次数和 worker lease 超时；SQLite 用原子 claim 确保同一节点只被一个 worker 执行。进程中断后，过期运行节点回到队列，已完成节点直接复用 checkpoint；依赖失败的节点会进入 `blocked`。已完成 run 再次 `resume` 不会重复执行。

审核节点将 actor/reviewer 的结构化 finding 保存为独立记录：`extractor_actor` 检查输入材料，`evidence_reviewer` 检查输出契约，②财报分析还会运行 `financial_reviewer` 与 `conflict_reviewer`。finding 的建议动作是 `continue`、`retry`、`escalate` 或 `block`；`retry` 会在节点重试上限内回退，未决的已核验事实冲突会阻断任务，已记录的事实决议会被正确应用。审核器不自动把候选升级为事实。

```powershell
# 完整显示 run、事件、DAG 节点 checkpoint 和 reviewer findings
.\.venv\Scripts\python.exe -m finagent --state-dir .finagent show RUN_ID

# 继续被中断的普通任务；样例任务另加 --corpus .finagent-sample
.\.venv\Scripts\python.exe -m finagent --state-dir .finagent resume RUN_ID
```

## 模型接入

需要 OpenAI 兼容的 `/chat/completions` 接口。设置以下环境变量后，②的叙述分析及③至⑦的研究草稿会调用模型：

```powershell
$env:FINAGENT_MODEL_BASE_URL = 'https://your-gateway.example/v1'
$env:FINAGENT_MODEL_API_KEY = '...'
$env:FINAGENT_MODEL_SMALL = 'small-model-name'
$env:FINAGENT_MODEL_STRONG = 'strong-model-name'
```

本地文件默认标为 `restricted`，不发送至外部模型。仅对具有相应使用许可的公开样例添加 `--public`。当前网关采用强模型处理研究任务，小模型选择及调用成本评测接口已经预留，后续必须以金标数据确定路由规则。

## 目录

```text
finagent/contracts.py       任务、证据、事实、指标与成果契约
finagent/storage.py         SQLite 元数据和内容寻址对象存储
finagent/corpus.py          交付样例 SQLite 的只读数据适配器
finagent/evaluation.py      独立样例参考库验收器
finagent/ingest.py          所有业务线共用的数据前置
finagent/catalog.py         试点资料目录校验与清单驱动入库
finagent/public_data.py     受总配额约束的公开 SEC EDGAR 采集器
finagent/resolution.py      财报冲突事实的人工决议记录
finagent/document_parser.py PDF 文本层覆盖检查与 OCR 路由状态
finagent/ocr.py             本地 OCR 执行、转写留存与候选生成
finagent/taxonomy.py        版本化 XBRL taxonomy map 与候选映射
finagent/finance_kernel.py  确定性财务计算
finagent/models.py          模型适配与结构化输出
finagent/prompts.py         七条业务线的版本化指令
finagent/specifications.py  版本化业务规范读取与未评估清单
finagent/data/             从原始 Markdown 编译的规范快照
finagent/runtime.py         七入口调度、事件记录和运行清单
finagent/workflow.py        持久 DAG、依赖、checkpoint、重试和失败传播
finagent/reviewers.py       actor/reviewer finding 与回退建议
finagent/flows/             七条独立业务 flow
tools/                     规范编译脚本
examples/                   可复算样例
tests/                      时间截面、公式、入库复用和来源约束测试
```

## 下一阶段

当前试点包含五家中国公司 2024 年报，按公司划分 train/dev/test，并已生成待审核金标包；它用于验证目录、解析和审核流程，不满足每家公司连续三年财报的分析最低条件。补齐连续年份和市场快照后，接入经人工核验的事实运行财报指标、估值和投资备忘录。数据量扩大后，`EvidenceStore` 接口可替换为对象存储、湖仓和关系库组合，flow 契约保持不变。

本机已完成的 OCR、五家公司解析、独立字段评测和 SEC dry-run 结果见[真实试点执行记录](真实试点执行记录.md)。
