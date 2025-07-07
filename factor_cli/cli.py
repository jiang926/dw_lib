import subprocess

import pandas as pd

from database.mysql_database import GetFactorDataAPI

gt_api = GetFactorDataAPI()


def add_cmake_factor(
        factor_name: str,
        factor_version: str,
        factor_type: str,
        submitted_by: str,
        factor_args: dict = None,
        review_by: str = None
):
    factor_info = {
        'factor_name': factor_name,  # 因子名称
        'version': factor_version,  # 因子版本
        'factor_type': factor_type,  # 因子类型
        'submitted_by': submitted_by,  # 因子提交人
    }
    if factor_args:
        factor_info.update({'factor_args': factor_args})

    if review_by:
        factor_info.update({'review_by': review_by})

    try:
        # subprocess.run(["./build.sh", factor_version], check=True)
        print(f"✅ 编译版本 {factor_version} 成功！")
        try:
            gt_api.create_factor_info(factor_info)
        except Exception as e:
            print(f"❌ 因子信息入库失败，错误码: {e}")
    except Exception as e:
        print(f"❌ 编译失败，错误码: {e}")


def node_factor(code: str, datetime: str, factor_name: str, factor_version: str = None):
    if factor_version is None:
        result = gt_api.get_new_factor_name(factor_name)
        print(result)
        print(f"采用 {factor_name} 因子的 {result.get('version')} 版本计算因子")

    if not gt_api.factor_exists(factor_name, factor_version):
        print(f" 因子不存在")

    df = pd.read_parquet('../data/000001_ls.parquet')  # 获取数据
    try:
        import factor_framework as ff
    except Exception as e:
        print("因子导入失败....")
        raise
    try:
        factor = ff.create_factor(factor_name)
        factor.set_data(df)
        factor.set_params([factor_name])
        factor.run()
        result = factor.get_result()
    except Exception as e:
        print(f"{factor_name} 计算失败， {e}")


# class FactorCalculationRunner:
#     pass


if __name__ == '__main__':
    add_cmake_factor('name', '1.1', '0', 'jiang', {'a': 1, 'b': 2})
