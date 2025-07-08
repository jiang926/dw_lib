# 因子管理平台

## 1. 平台架构设计
    dwlib_system
    |__database  # 数据库模块
    |__factor  # 因子管理模块
    |__src  # 主程序
    |__test  # 测试模块

### 1.1 数据库设置
    因子信息表：
    |  字段名                  |        定义                 | 设计原因 |
    | `id`                    | 自增的数字主键。              | 提供一个无业务含义的唯一行标识，便于高效的内部数据操作。 |
    | `factor_name`           | 因子名称标识符。              | 建立因子主记录与其多个版本之间的一对多关系。 |
    | `version`               | 版本的唯一字符串标识。         | 业务层面的版本号，便于识别和沟通。与`factor_id`共同构成业务唯一键。 |
    | `factor_args`           | 使用这个因子时需要传递那些参数  | 使用JSON格式提供了极高的灵活性，可以在不修改表结构的情况下支持任意复杂的参数组合，保证了每个版本的可复现性。 |
    | `factor_type`           | 因子的类别属于什么类型。       | 关键的计算元数据，告知计算引擎需要加载何种粒度的数据源。 |
    | `factor_status`         | 版本的审核状态。              | **审核流程的核心**。通过状态（待审、通过、拒绝）的流转来驱动整个因子的生命周期管理。 |
    | `submitted_by`          | 因子提交人标识。              | 提供清晰的审计链，明确每个环节的责任人。 |
    | `review_by`             | 因子审核人标识。              | 提供清晰的审计链，明确每个环节的责任人。 |
    | `review_notes`          | 审核人填写的备注理由。         | 促进研究员和审核人之间的沟通，使得审核流程更加透明。 |
    | `created_at`            | 版本记录的创建时间。           | 记录版本的提交时间。 |
    | `updated_at`            | 版本更新时间。                | 记录版本的提交时间。 |
    
    因子计算结果存储：
    |  字段名                  |        定义                 | 设计原因 |
    | `id`                    | 自增的数字主键。              | 高效索引。 |
    | `factor_name`           | 因子名称标识符。              |
    | `factor_version`        | 计算任务对应的版本号。         | 精确关联到被计算的具体因子版本。 |
    | `code`                  | 标的代码，例如 "600519.SH"。  | 因子计算是针对具体标的进行的。 |
    | `data_type`             | 数据类型。                   |
    | `factor_path`           | 因子结果存储路劲。            |
    | `calculated_date`       | 数据的计算日期。              | 因子计算是针对具体交易日进行的。 |
    | `data_status`           | 计算任务的执行结果状态。       | 用于监控计算任务的健康状况，是判断数据是否可用的依据，也是失败重试机制的基础。 |
    | `created_at`            | 数据写入时间。                | 审计字段。 |
    | `updated_at`            | 数据更新时间。                | 记录版本的提交时间。 |
    | `extra_info`            | 存储额外信息的JSON字段。       | 提供一个灵活的扩展点来存储诊断和性能分析信息，而无需频繁修改表结构。 |
        

## 2. 数据库连接模块

### 2.1 数据库表设计
    factor_table.sql  # 数据库建表命令

### 2.2 数据库连接实例
    class DatabaseConnectionManager:
        ...

### 2.3 因子数据入库实例
    class GetFactorDataAPI:
        def create_factor_info(self, factor_info: dict):
            """提交因子入库逻辑"""

        def update_factor_status(self, factor_name: str, factor_version: str):
            """审批，判断因子是否可以上线使用逻辑"""

        def get_all_factor_version(self, factor_name: str):
            """"查看库内当前因子的所有版本"""
        
        def get_all_factor_name(self):
            """取所有因子名称"""

        def get_new_factor_name(self, factor_name: str):
            """获取因子的最新版本"""

        def get_factor_pending_status(self, factor_name: str = None, factor_version: str = None):
            """获取处于审核状态的因子"""

        def write_node_factor_data(self, factor_name: str, factor_version: str,
                               code: str, day: str, data_type: str, save_path: str = './save_path',
                               data_status: str = 1, extra_info: dict = None
                               ):
        """将计算因子结果信息保存到数据库中"""

        def exists_source_code_data(self, factor_name: str, factor_version: str,
                                code: str, day: str):
        """判定因子计算结果存在"""

## 3. 因子管理平台

### 3.1 cli管理
    def add_cmake_factor(
        factor_name: str,
        factor_version: str,
        factor_type: str,
        submitted_by: str,
        factor_args: dict = None,
        review_by: str = None
    ):
        """构建因子"""

    def node_factor(
        code: str,  # 股票代码
        day: str,  # 日期
        factor_name: str,  # 因子名称 
        factor_type: str,   # 类型
        save_path: str = None  # 保存路径
    ):
        """计算因子结果"""
        # 1. 获取因子最新版本, GetFactorDataAPI.get_new_factor_name()
        # 2. 从数据库中获取数据，判断因子计算的结果是否存在，存在则告知，然后结束。 
                GetFactorDataAPI.exists_source_code_data()
        # 3. 获取原始数据
        # 4. 计算
        # 5. 保存计算结果
        # 6. 将计算结果相关信息保存到数据库中。 GetFactorDataAPI.write_node_factor_data()

### 3.2 构建步骤
    #----------第一步----------#
    # my_factor.cpp 自己构建的因子文件
    ...实际代码，省略...

    #----------第二步----------#
    # CMakeLists.txt 文件，把你的新 .cpp 文件加入编译项中
    set(FACTOR_SOURCES
        factors/calc_RMI_zzh.cpp
        factors/factor_template.cpp
        factors/calc_RSI_example.cpp
        factors/my_factor.cpp     # 👈 添加这里
        ${COMMON_SOURCES}
    )
    
    if(NOT DEFINED VERSION)   # 获取外部传入的 VERSION 参数
        set(VERSION "default")
    endif()
    
    message(STATUS "因子库版本: ${VERSION}")

    set(LIBRARY_OUTPUT_PATH ${CMAKE_SOURCE_DIR}/lib/${VERSION})  # 设置输出路径为 lib/${VERSION}

    #----------第三步(可跳过)----------#
    # 重新构建编译
    cat build.sh

    #!/bin/bash
    VERSION=$1
    if [ -z "$VERSION" ]; then
      VERSION="default"
    fi
    
    mkdir -p build
    cd build
    cmake .. -DVERSION=$VERSION
    make -j
    
    #----------第四步----------#
    import cli
    # 编译因子，以及因子信息入库
    add_cmake_factor(
        factor_name: str,  # 因子名称
        factor_version: str,  # 因子版本
        factor_type: str,  # 因子类型
        submitted_by: str,  # 因子提交人
        factor_args: dict = None,  # 因子需要的参数
        review_by: str = None  # 因子审批人
    )
