# V2.4 型号判断优化更新

此更新修正过严的型号命名判断，并将应用版本号升至 2.4。压缩包中包含 4 个运行文件和 2 个说明文件。

## 必须替换的运行文件

- `agent_core.py`：避免凭模型记忆否定型号名称；只在材料明确写出不同型号时提示冲突，并收窄 AirPods 程序规则，避免兼容配件或顺带提及误触发。
- `domain_knowledge.py`：补充型号与充电盒版本的区分提示。
- `review_record.py`：应用版本更新为 2.4。
- `skills/seller-chat/SKILL.md`：同步自然追问规则。

`README.md` 和 `DEPLOY.md` 是说明文件，可一并替换。ZIP 内保留了 `skills/seller-chat/SKILL.md` 的目录结构。

## 上传方式

1. 解压 `二手数码交易助手V2.4-型号判断优化.zip`。
2. 在 GitHub 仓库 `zoey4444/secondhand-tech-agent` 的 `main` 分支，替换仓库根目录的 `agent_core.py`、`domain_knowledge.py`、`review_record.py`。
3. 将 `skills/seller-chat/SKILL.md` 放回仓库同一路径并替换旧文件。GitHub 不会自动解压 ZIP。
4. 提交后等待 Streamlit Cloud 完成重新部署；页面底部显示版本 2.4 后，才代表新规则在线生效。

本更新不需要 API 密钥或依赖变更。不要上传 `.env`、Secrets、个人截图或真实交易记录。
