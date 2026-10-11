# 热线派单服务

通过 `uv venv`、`uv pip install -r requirements.txt` 安装依赖，运行 `python main.py`。默认只监听 127.0.0.1:5000，生产环境通过 HTTPS 反向代理访问。

配置 DB_HOST、DB_PORT、DB_USER、DB_PASSWORD、DB_NAME、APP_USERS_FILE、APP_ORIGINS。账号 JSON 数组格式与 sftz-server 相同，密码使用加盐 PBKDF2-HMAC-SHA256（310000 次）；可用 scripts/create-account.py 生成。会话 8 小时过期，重启失效。

备份数据库、处理重复工单编号后执行 migrations/001_workflow.sql。工单以版本号检测并发修改，状态转换、转派原因及操作人写入同一事务的历史表。归档保留原记录，人员停用不删除历史引用。旧工单中仅有姓名/微信的指派信息，在编辑时重新选择人员以绑定人员 ID。

`pytest` 使用独立临时 SQLite 数据库，不连接业务 MySQL。此前入库的数据库凭据须在数据库服务端轮换。
