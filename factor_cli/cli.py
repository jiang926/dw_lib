import os
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


def node_factor(code: str, day: str, factor_name: str, factor_type: str):
    day = str(day).replace('-', '')
    try:
        from dw_data.fastpai import getAPI, getLS, getOrig, putAPI
    except Exception as e:
        print(f"❌ 引用获取数据包失败，检查环境是否安装： {e}")
        raise

    try:
        result = gt_api.get_new_factor_name(factor_name)
        version = result.get('version')
        print(f"采用 {factor_name} 因子的 {version} 版本计算因子")
    except Exception as e:
        print(f"因子获取失败，{e}")
        raise
    msg = gt_api.exists_source_code_data(
            factor_name,
            version,
            code,
            day
    )

    save_path = f"{factor_type}/{factor_name}/{day}/{code}.parquet"
    if msg:
        print(f"因子结果已经存在库中")
        try:
            return getAPI.get_df(f"122/data2/{save_path}")
        except Exception as e:
            print(f"读取错误，{e}")
            return None

    try:
        df = getLS.read_ls(code, day)
    except Exception as e:
        print(f"❌ 原始数据获取失败， {e}")
        raise

    try:
        import sys
        sys.path.append('../lib')
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
        df = pd.DataFrame(result)

        try:
            result_status = putAPI.put_parquet(df, f"122/{save_path}", verbose=1)
            if result_status.get('success', False):
                gt_api.write_node_factor_data(
                    factor_name,
                    version,
                    code,
                    day,
                    factor_type,
                    save_path
                )
                return df
            else:
                print(f"数据保存失败")
                return None
        except Exception as e:
            print(f"因子结果保存到{save_path}失败，{e}")
            raise
    except Exception as e:
        print(f"{factor_name} 计算失败， {e}")
        raise


# class FactorCalculationRunner:
#     pass


if __name__ == '__main__':
    add_cmake_factor('name', '1.1', '0', 'jiang', {'a': 1, 'b': 2})
