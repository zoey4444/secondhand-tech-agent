# 把二手数码交易助手分享给别人

最适合演示的方式是把项目部署到 Streamlit Community Cloud。完成后会得到一个网页链接，别人打开就能使用，无须安装 Python。

## 一、上传代码到 GitHub

1. 登录 GitHub，创建一个新仓库，例如 `secondhand-tech-agent`。
2. 在仓库页面选择 **Add file → Upload files**。
3. 上传这些文件：`app.py`、`cart_scene.py`、`product_preview.py`、`puzzle_feedback.py`、`image_dialogue.py`、`requirements.txt`、`README.md`、`DEPLOY.md`、`.gitignore`、`.env.example`，以及 `.streamlit/config.toml`（注意保留 `.streamlit` 文件夹结构）。
4. **不要上传 `.env`、`.streamlit/secrets.toml`、`.venv` 或 `__pycache__`。** 上传完成后再检查一次仓库文件列表。`.gitignore` 是额外保护，但手动网页上传时仍要自己核对。

## 二、部署到 Streamlit Community Cloud

1. 打开 <https://share.streamlit.io/>，用 GitHub 登录。
2. 点击 **Create app**，选择刚创建的仓库、分支和主文件 `app.py`。
3. 打开 **Advanced settings → Secrets**，粘贴下面这行，并把引号内文字替换成自己的密钥：

   ```toml
   DEEPSEEK_API_KEY = "自己的DeepSeek密钥"
   ```

   密钥只填在 Streamlit 的 Secrets 设置中，不填在 GitHub 文件中，也不要发给他人。
4. 点击部署。等安装和启动完成后，复制生成的 `streamlit.app` 网页链接，发给老师或测试者。

## 三、试用与排查

- 用手机或另一个浏览器打开分享链接，提交一条**不含个人信息**的模拟案例；分别试一次文字回复和聊天截图识别，确认可编辑识别结果、第二轮拼图和购物车变化提示出现。
- 若显示“没有配置 API Key”，回到应用的 Secrets 检查变量名是否为 `DEEPSEEK_API_KEY`，并重新启动应用。
- 若显示模型调用失败，检查 DeepSeek 密钥、额度、网络和模型名称。应用默认使用 `deepseek-flash`；如果你的账号使用其他可用模型，可在应用环境中设置 `DEEPSEEK_MODEL`。
- 面向公众开放前先评估 API 用量；公开访问会使用你配置的密钥发起调用。可先只向指导老师和组员分享链接。

本应用不保存跨浏览器会话的交易记录。分析基于使用者粘贴的文字，不能替代实物验货、凭证核验或平台争议处理。
