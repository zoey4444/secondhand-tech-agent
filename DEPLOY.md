# V2.3 更新现有 Streamlit 应用

这份更新已在本地准备好，线上应用仍是先前版本。把下面 7 个文件一起上传到 GitHub 仓库 `zoey4444/secondhand-tech-agent` 的 `main` 分支，Streamlit Cloud 会从该分支重新拉取代码。

## 只需替换或新增这些文件

- `app.py`：新增参考价输入与结果展示
- `agent_core.py`：把价格对比写入核验结果
- `domain_knowledge.py`：补充已发布的新型号
- `review_record.py`：导出新增字段，版本号升至 2.3
- `market_comparison.py`：**新增，必须上传**；缺少它会导致应用启动失败
- `README.md`：更新功能、型号来源和限制说明
- `DEPLOY.md`：本说明

压缩包 `二手数码交易助手V2.3-仅更新文件.zip` 里只有这 7 个文件。先解压，再把解压后看到的 7 个文件上传到仓库**根目录**。GitHub 不会自动解压 ZIP，不能直接上传 ZIP 代替文件。已有的 `cart_component/`、`skills/seller-chat/` 和 `.streamlit/` 目录保留。

## 上传步骤

1. 打开 GitHub 仓库 `zoey4444/secondhand-tech-agent`，确认左上角分支是 `main`。
2. 点 **Add file → Upload files**，选择解压后的 7 个文件。确认 `market_comparison.py` 与 `app.py` 位于同一层。
3. 点 **Commit changes**。建议提交说明：`Add current models and used-price comparison`。
4. 等待 Streamlit Cloud 日志出现 `Pulling code changes from GitHub` 和 `Updated app!`，然后刷新应用。
5. 应用底部应显示**版本 2.3**。型号下拉列表可看到 AirPods 5 和 iPhone 18 Pro；第三站可输入同款二手参考价；分析结果会出现“同款二手价格对比”。

## 价格功能的边界

应用不自动抓取闲鱼等平台行情。用户提供同款、容量/版本和成色接近的 3 至 5 个二手挂牌价后，应用计算中位数与标价差幅，并保留用户填写的来源与查看日期。挂牌价不等于成交价，价格差异也不能单独证明商品真假或交易风险。没有合适样本时，页面会明确说无法判断是否接近市价。

继续使用现有 Streamlit Secrets。不要上传 `.env`、`.streamlit/secrets.toml`、个人截图、真实订单或核验记录。
