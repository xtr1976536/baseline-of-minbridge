# ReAct 环境恢复

## Wikipedia

原代码使用 `requests.get()` 请求英文 Wikipedia HTML 搜索页。本机实测：默认请求返回 403，同一 URL 增加明确 User-Agent 后返回 200。修复保留原 URL、HTML parser、搜索结果分支、句子截取、Lookup 和动作协议，仅增加 User-Agent、30 秒超时与 HTTP 错误检查。没有使用搜索引擎摘要、模型回答或题目答案替换观察。

`REACT_WIKIPEDIA_USER_AGENT` 可覆盖请求标识，HTTPS 代理继续使用 requests 原生环境变量。检查脚本为 `scripts/check_react_wikipedia.py`，检查记录为 `logs/react-wikipedia-check.json`。四种实体搜索、Lookup、Finish，以及 HotpotQA/FEVER 正确答案评分均不调用模型 API。Wikipedia 内容仍是运行时页面，不能恢复为论文时期快照。

## WebShop

作者 ReAct notebook 的旧地址 `http://3.83.245.205:3000` 返回 502。本地部署使用官方 [Princeton-NLP/WebShop](https://github.com/princeton-nlp/WebShop)，固定 commit `64fa2a5c15c7daa698b9ac93f5bb5437b634c9bd`。服务继续输出作者 HTML 页面，ReAct 继续使用作者的 `webshopEnv`、`webshop_text`、session 路由和 action/parser；`REACT_WEBSHOP_URL` 仅切换服务地址。没有用另一个购物网站或改写奖励取代原环境。

原始 Google Drive 链接由 gdown 下载失败。公开镜像 `YWZBrandon/webshop-data` 与 `HongbangYuan/webshop` 的商品、属性、人工指令文件有相同的 Git/LFS 对象标识；下载脚本固定前一个镜像的 revision `ce990fff5aee388db2706f07820c578ab68e0453`，对大型文件验证公开 LFS SHA256，保存实际文件大小与 hash。该检查证明镜像内容一致，不能证明它们与已无法下载的 Google Drive 文件逐字节相同。

完整原始商品 JSON 为 5,479,720,229 字节，不能用 1,000 商品示例数据代替正式环境。独立环境依赖锁在 `configs/webshop-requirements.lock.txt`，安装与完整索引构建入口是 `scripts/setup_webshop.sh`。使用作者版本 Pyserini 0.17.0 / Lucene BM25、官方文档转换、en_core_web_sm 3.3.0 英语模型和官方 reward。为适配当前 Apple Silicon/Python，spaCy 运行库为 3.8.18，加载旧权重时有版本警告；保留此兼容性差异及实测日志，不把它表述为历史环境逐版本一致。

为避免先加载整段 5.48 GB JSON 文本造成峰值内存过高，`webshop_runtime.py` 流式读取商品，并逐条调用作者原始字段清理函数。后续商品转换、商品顺序、重复 ASIN 过滤和价格生成仍由作者 `load_products` 完成。已对 1,000 商品用相同随机种子比较四个返回值，全部相等，记录在 `logs/webshop-streaming-equivalence.json`。

启动入口 `scripts/start_webshop.py` 默认载入完整数据，只绑定 `127.0.0.1`；`--demo` 是独立标记的 1,000 商品检查。`scripts/check_react_webshop.py` 用脚本动作检查初始指令、检索、商品详情、Description、Think、购买结束与奖励范围。检查奖励仅说明环境通路有效，不能作为 ReAct 模型实验结果。

## 可从 GitHub 重建

两个作者代码子模块指向公开 commit。兼容性改动保存在 `patches/`，通过 `scripts/apply_runtime_patches.sh` 应用；不会把子模块指向只存在于本机的提交。完整数据、虚拟环境、索引和编译产物在 `.local/`，GitHub 保存下载、构建、启动、校验脚本及清单。
