# JCPC 新生赛公开网站

独立网站仓库；仅 `site/` 会发布到 GitHub Pages。站点由相邻的 `../xxs_workflow/` 生成，个人资料、报名表、账号、邮件与 SMTP 凭据必须留在工作流仓库的忽略目录中。

当前是本地筹备草稿，Actions 会拒绝部署。日期、规则和域名确定后，先在工作流仓库 `build --release → check → sync`，然后审阅和推送本仓库。

## 首次设置仓库与 Pages

1. 在自己的 GitHub 账户新建独立仓库（例如 `xxs_website`），不自动生成 README。使用 `main` 分支；仓库公开性与 Pages 可用性应按你的账户方案确认。
2. 在本目录执行 `git remote add origin <你刚创建的仓库 SSH 或 HTTPS 地址>`。远程 URL 不带密码或令牌。先用 `git log` 核对已有提交，部署前应生成并提交正式站点。
3. 安装本地检查：`python3 scripts/check_git_privacy.py --install-hook`。
4. GitHub 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。确保 Actions 启用，`github-pages` 环境允许 `main` 部署。
5. 完成下面的域名设置，并生成、同步正式页面；执行：

```sh
python3 scripts/check_site.py site --release
python3 scripts/check_git_privacy.py
git status --short
git diff
git add .
git diff --cached
git commit -m "Publish confirmed contest information"
git push -u origin main
```

`.github/workflows/deploy-pages.yml` 在 `main` 的站点/脚本/工作流变更时，先检查 Git 私有路径、发布标记、公开清单哈希、链接与常见隐私标记，再上传 `site/` 并通过官方 Pages Actions 部署。也可在 Actions 手动触发。草稿不会部署；不需要 PAT，也不要上传个人 SMTP 密钥到此仓库。

本地与仓库检查不会自动识别所有图片、姓名或学号，提交前仍要审阅。检查在推送后运行不能阻止误推送的文件进入 GitHub 历史，应优先使用本地检查和 diff。

## 自己的域名

推荐使用单独子域名，例如 `contest.你的域名`，方便保留主站。

1. 工作流仓库 `config/2026.yaml`：`site.url` 填 `https://你的比赛域名`，`site.custom_domain` 填纯域名。不带协议、路径、端口。
2. 运行 `build --release → sync`，确认 `site/CNAME` 和 `site/build-meta.json` 中的域名一致。
3. 先在 GitHub Pages 设置中登记 **Custom domain**。建议按 GitHub 官方说明先验证域名所有权，避免域名被其他 Pages 项目绑定。
4. 在域名服务商的 DNS 控制台配置：

| 目标 | DNS 设置 |
|---|---|
| 子域名，如 `contest` | 添加 `CNAME`，值指向 `你的GitHub用户名.github.io`，不含协议、路径或仓库名 |
| 根域名，如 `example.com` | 按 GitHub 当前官方文档设置所需 A/AAAA，或服务商支持的 ALIAS/ANAME |

5. 删除同名冲突记录，等待 DNS 生效与 Pages 的 DNS 检查、证书签发；证书可用后启用 **Enforce HTTPS**。不必为自定义域名买独立 SSL 证书。
6. 用手机网络和电脑测试 HTTPS、首页、手册、报名表、群链接和图片。**自定义 Actions 模式忽略 `CNAME` 文件，域名实际以 Pages 设置为准**；本项目保留该文件只为核对生成配置。

不要用 DNS 通配符把所有子域都指向 Pages。若启用了域名服务商的代理/CDN，首次排障时先按 GitHub 文档验证 DNS 直连结果。

如果暂不绑定域名，`custom_domain` 留空，`site.url` 填 GitHub 实际给出的 Pages 地址（项目站点通常含仓库路径）。站内采用相对链接，兼容项目路径。不要把示例域名当作自己已经拥有的域名。

官方说明（首次操作以当前页面为准）：

当前环境无法联网核对官方文档或运行 GitHub Actions。仓库已配置静态 Pages 发布流程，只上传 `site/`；首次远程运行需检查所用 action 版本、权限与 Actions 日志。

- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages
- https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/securing-your-github-pages-site-with-https

## 更新网页

```sh
cd ../xxs_workflow
# 编辑 config/2026.yaml、content/、assets/ 或 templates/
python -m xxs_workflow build --release
python -m xxs_workflow check
python -m xxs_workflow preview
# 预览确认后 Ctrl+C，继续
python -m xxs_workflow sync
cd ../xxs_website
git diff
python3 scripts/check_site.py site --release
```

然后按上面的 Git 步骤提交推送。`sync` 会整体重建 `site/`；禁止直接手改生成文件。修改域名时需要同步改配置、Pages 设置和 DNS；网站仓库的回退提交不会自动回退域名控制台。

报名结束时同时关闭表单平台，重新生成关闭入口的页面。赛后只发布审核过的公示摘要与公开链接。原始名单、成绩、座位表、账号密码、邮箱电话都不能直接放进 `site/`。

## 本地预览与检查

```sh
python3 scripts/check_site.py site
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

打开 `http://127.0.0.1:8000`。部署失败先看 Actions 的 check/deploy 日志；草稿或哈希不符需回工作流源文件重建，权限与域名问题需在 GitHub 设置或 DNS 控制台处理。回退公开内容可 `git revert <提交>` 后审阅并推送。
