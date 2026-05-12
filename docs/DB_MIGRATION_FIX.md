# 数据库结构紧急修复说明

当后端启动报错 `Unknown column 'hash_algo' in 'field list'` 时，说明当前 MySQL 中的 `sys_user_account` 仍是旧表结构。优先执行自动迁移：

```bash
python scripts/migrate_schema.py
python scripts/check_schema.py
python scripts/init_security.py
python backend/app.py
```

如果必须手动修复，可在 `bigdata` 数据库中执行：

```sql
ALTER TABLE sys_user_account
ADD COLUMN hash_algo VARCHAR(32) NOT NULL DEFAULT 'scrypt';

ALTER TABLE sys_user_account
ADD COLUMN hash_version VARCHAR(32) NOT NULL DEFAULT 'v1';

ALTER TABLE sys_user_account
ADD COLUMN display_name VARCHAR(64) NULL;

ALTER TABLE sys_user_account
ADD COLUMN email VARCHAR(128) NULL;

ALTER TABLE sys_user_account
ADD COLUMN phone VARCHAR(32) NULL;

ALTER TABLE sys_user_account
ADD COLUMN account_status VARCHAR(32) NOT NULL DEFAULT 'active';

ALTER TABLE sys_user_account
ADD COLUMN failed_login_count INT NOT NULL DEFAULT 0;

ALTER TABLE sys_user_account
ADD COLUMN failed_attempts INT NOT NULL DEFAULT 0;

ALTER TABLE sys_user_account
ADD COLUMN last_failed_login_at DATETIME NULL;

ALTER TABLE sys_user_account
ADD COLUMN lock_until DATETIME NULL;

ALTER TABLE sys_user_account
ADD COLUMN last_login_at DATETIME NULL;

ALTER TABLE sys_user_account
ADD COLUMN password_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE sys_user_account
ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE sys_user_account
ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

`sys_audit_log` 不存在时可创建：

```sql
CREATE TABLE IF NOT EXISTS sys_audit_log (
    audit_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NULL,
    username VARCHAR(64) NULL,
    role VARCHAR(32) NULL,
    school_id VARCHAR(32) NULL,
    action VARCHAR(80) NULL,
    module VARCHAR(120) NULL,
    ip VARCHAR(80) NULL,
    detail_json JSON NULL,
    action_type VARCHAR(64) NULL,
    module_name VARCHAR(100) NULL,
    target_type VARCHAR(64) NULL,
    target_id VARCHAR(128) NULL,
    request_path VARCHAR(255) NULL,
    request_method VARCHAR(16) NULL,
    result_status VARCHAR(20) NULL,
    message VARCHAR(255) NULL,
    ip_address VARCHAR(64) NULL,
    user_agent VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Windows 终端如仍出现中文乱码，先执行：

```bat
chcp 65001
```
