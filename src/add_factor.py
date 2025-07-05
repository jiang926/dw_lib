import os.path

import pandas as pd
import sys
sys.path.append('../')

from database.mysql_database import GetFactorDataAPI


db_api = GetFactorDataAPI()


def rmi_factor(code: str, date: str):
    import sys
    try:
        sys.path.append('../lib')
        import factor_framework as ff
    except Exception as e:
        print(f"导入C++因子框架失败: {e}")
        sys.exit(1)
    test_data = pd.read_parquet('../data/000001._ls.parquet')
    factor = ff.create_factor("RMI")
    factor.set_data(test_data)
    factor.set_params(["RMI"])
    factor.run()
    result = factor.get_result()
    return result


factor_info = {
    'factor_name': "RMI",  # 因子名称
    'version': "v1.1.0",  # 因子版本
    # 因子描述
    'factor_args': {
        '参数1': "a",
        '参数2': "b"
    },
    'factor_type': "stock",  # 因子类型
    # 'factor_status': "None",
    'submitted_by': "jiang",  # 因子提交人
    # 'review_by': "",
    # 'review_notes': "",
    # 'created_at': "",
    # 'updated_at': ""
}

db_api.create_factor_info(factor_info)
# print(db_api.get_factor_pending_status(factor_version='v1.0.0'))
# print(db_api.update_factor_status(factor_info['factor_name'], 'v1.1.0'))
# print(db_api.get_all_factor_version(factor_info['factor_name']))
# print(db_api.get_new_factor_name(factor_info['factor_name']))
# print(db_api.get_all_factor_name())

res = rmi_factor('000001', '20250701')
print(res)
