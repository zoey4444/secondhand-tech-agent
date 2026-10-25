# V2.2 更新现有网页

这是本地更新包，尚未替你提交 GitHub 或更新线上网页。沿用当前仓库、分支和 Cloud Secrets。

## 操作顺序

1. 下载并解压 `二手数码交易助手V2.2-完整部署包.zip`。打开解压后的文件夹，应该直接看到 `app.py` 和若干文件夹。
2. 打开现有 GitHub 仓库 `secondhand-tech-agent`。确认选中的是 Streamlit 应用设置中正在使用的 Branch；如果那里显示 main，就选 main。
3. 在仓库根目录使用 **Add file → Upload files**。上传解压文件夹里面的文件和子文件夹。不要只上传 ZIP，也不要把外层文件夹一起套进仓库。
4. 点击 **Commit changes**，提交到刚才确认的分支。提交说明可以写 `Update review workflow to V2.2`。
5. 等待应用完成更新，再打开应用。若仍是旧页面，从应用管理处重启一次。
6. 完成一条分析后，页面底部应出现“版本 2.2”和“下载本次核验记录”；结果区域应有“重新分析当前材料”。这能帮助确认看到的是新版。

## 上传后的目录必须这样对应

```text
app.py
agent_core.py
evidence_refs.py           ← 新增，必需
review_record.py           ← 新增，必需
review_policy.py
domain_knowledge.py
cart_scene.py
puzzle_feedback.py
product_preview.py
image_dialogue.py
requirements.txt
cart_component/
    index.html
skills/
    seller-chat/
        SKILL.md
.streamlit/
    config.toml
```

`index.html` 必须放在 `cart_component` 里，完整话术必须放在 `skills/seller-chat/SKILL.md`。同名文件放在根目录不能代替这些路径。缺失话术文件会使用内置简版，仍应上传完整文件。

包内 `tests` 文件夹、`evaluate.py`、模拟案例和说明文档也可以一并保留；它们不会在打开应用时自动执行。测试目录同时有 `.py` 和 `.cjs` 文件，两个都保留。

## 密钥与模型

继续使用已有配置。本包中的 `.env.example` 只是示例，没有真实密钥。不要把 `.env`、`.streamlit/secrets.toml`、个人截图或下载的真实交易记录上传 GitHub。

初次配置的开发者可以在本地复制 `.env.example` 为 `.env`，设置账号实际可用的模型与接口，再安装 `requirements.txt` 中依赖，运行 `streamlit run app.py`。Cloud 的密钥保存在应用 Secrets。不要因这次更新重复创建应用。

## 一次集中验收

具体输入和检查点见 `V2.2更新与复测说明.md`。先做三个代表案例及两个后续答复；每条完成后下载记录。若通过，就转入对照评测与报告整理，不继续重复相同冒烟案例。

如果失败，保留下载的记录和错误截图，按具体失败项修复。新结果与旧版记录分开，不用修改代码后的预期替换旧实测结果。
