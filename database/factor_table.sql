create table factor_info (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  factor_name VARCHAR(64) NOT NULL COMMENT '因子名字',
  version	 VARCHAR(16) NOT NULL COMMENT '版本信息',
  factor_args JSON COMMENT '描述信息',
  factor_type VARCHAR(128) NOT NULL COMMENT '因子类型',
  factor_status ENUM('0', '1', '2') NOT NULL COMMENT '0=待审, 1=通过, 2=拒绝',
  submitted_by VARCHAR(32) COMMENT '提交人',
  review_by VARCHAR(32) COMMENT '审核人',
  review_notes TEXT DEFAULT NULL COMMENT '审核备注',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE (factor_name, version) -- 约束键，因子名 + 版本号
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '因子信息表';


CREATE TABLE factor_result (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,             -- 自增主键
    factor_name VARCHAR(64) NOT NULL,                -- 因子名称标识符
    version VARCHAR(16) NOT NULL,             -- 因子版本号
    code VARCHAR(50) NOT NULL,                        -- 标的代码
    data_type VARCHAR(128) NOT NULL,                  -- 数据类型
    factor_path VARCHAR(500) NOT NULL,                -- 因子结果存储路径
    calculated_date DATE NOT NULL,                    -- 因子计算日期
    data_status TINYINT NOT NULL COMMENT '0=未开始, 1=成功, 2=失败', -- 数据状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- 更新时间
    extra_info JSON DEFAULT NULL,                     -- 额外信息（JSON格式）
    UNIQUE (factor_name, version, code, calculated_date), -- 唯一约束
    INDEX idx_factor_name (factor_name),              -- 索引：因子名称
    INDEX idx_calculated_date (calculated_date),      -- 索引：计算日期
    INDEX idx_code (code)                             -- 索引：标的代码
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='因子计算结果存储表';
