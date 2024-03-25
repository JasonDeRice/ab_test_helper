#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   data_calculator.py
@Time    :   2023/09/26 08:04:43
@Author  :   Jason XU 
@Version :   1.0
@Desc    :   None
'''



import pandas as pd
# import json
# import sys
import numpy as np

def diff_calculation(ndarray_list1,ndarray_list2) -> dict:
    new1 = ndarray_list1.astype(float,order="k",casting='unsafe')
    new2 = ndarray_list2.astype(float,order="k",casting='unsafe')
    diff = np.average(new1,axis=0) - np.average(new2,axis=0)
    relative_diff_detail = (new1-new2)/new2
    relative_diff = np.average(relative_diff_detail,axis=0)
    return {
        "from": np.average(new1),
        "to":np.average(new2),
        "abs_diff": diff,
        "rela_diff" :relative_diff
    }

def data_formatter(input, type, rela_or_abs) -> str:
    """
    type: 目标字段的单位是百分比 OR 原始值
    rela_or_abs:
        abs: 百分比的字段输出 pp， 非百分比的字段输出原始值
        rela: 统一输出百分比
        raw：输出原始值的场景，按照type确定输出的是否为百分比
    """
    if type == "percent":
        if rela_or_abs == "abs":
            return str(float(np.round(input*100, 2))) + "pp"
        elif rela_or_abs == "rela":
            return str(float(np.round(input*100, 2))) + "%"
        elif rela_or_abs == "raw":
            return str(float(np.round(input*100, 2))) + "%" 
        else:
            pass
    elif type == "raw":
        if rela_or_abs == "abs":
            return str(float(np.round(input, 2)))
        elif rela_or_abs == "rela":
            return str(float(np.round(input*100, 2))) + "%"
        elif rela_or_abs == "raw": 
            return str(float(np.round(input, 2)))
        else:
            pass


def get_brief_conclusion(data_frame,config_dict):
    # 增加数据质控
    out_list = []
    data = data_frame
    out_list.append(data)
    # 获取 date range str
    date_seris = data[config_dict['date_field']]
    min_date = date_seris.min()
    max_date = date_seris.max()
    date_range_str = f"from_{min_date}_to_{max_date}"
    # END
    experiment_flag_field = config_dict['experiment_flag_field']
    # ###################################################
    brief_conclusion=[]
    total_conclusion = []
    for exp in config_dict['experiment_set']:
        if type(exp) != str:
            experiment_tag = f"实验组{exp}"
            control_tag = f"对照组{config_dict['control_set'][0]}"
            segment = f"* 【实验组{exp} vs 对照组{config_dict['control_set'][0]}】"
        else:
            experiment_tag = exp
            control_tag = config_dict['control_set'][0] 
            segment = f"\n【{exp} vs {config_dict['control_set'][0]}】"
        
        brief_conclusion.append(segment)
        total_conclusion.append(segment)
        ###################################################
        for item in config_dict['target_field']:
            field = item['key']
            field_type = item['type']
            if field in data.columns.to_list():
                print(f'processing {field} {field_type}')
            else:
                print(f'{field} is not in columns, please re-check')
                continue
            ###############################################
            # 切换成ndarray计算
            exp_data = data[data[experiment_flag_field]==exp][field].values
            control_data = data[data[experiment_flag_field]==config_dict['control_set'][0]][field].values
            diff = diff_calculation(exp_data,control_data)
            # print(diff)
            ###############################################
            from_ave = data_formatter(
                        input = diff['from'],
                        type=field_type,
                        rela_or_abs="raw"
                        )
            to_ave = data_formatter(
                        input = diff['to'],
                        type=field_type,
                        rela_or_abs="raw"
                        )
            abs_diff = data_formatter(
                        input = diff['abs_diff'],
                        type=field_type,
                        rela_or_abs="abs")
            rela_diff = data_formatter(
                        input=diff['rela_diff'],
                        type=field_type,
                        rela_or_abs="rela"
                        )
            ###############################################
            short_conclusion = f"  * {field}:{abs_diff}，{rela_diff}" 
            brief_conclusion.append(short_conclusion)
            conclusion = f"  * {field}:  {experiment_tag}: {from_ave} ，{control_tag}: {to_ave};  变化值 {abs_diff}，{rela_diff}"
            total_conclusion.append(conclusion)
    # ###################################################

    # 将 total conclusion dafaframe 化，并存入结论list
    df_total_conclusion = pd.DataFrame(total_conclusion)
    df_total_conclusion.columns = ["【结论汇总】"]
    out_list.append(df_total_conclusion)

    # 逐个指标输出 matrix
    for target_field in config_dict['target_field']:
        one_field_data = []
        for exp in config_dict['experiment_set']:
            matrix = generate_detail_matrix(
                dataframe=data,
                date_field=config_dict['date_field'],
                experiment_flag_field=experiment_flag_field,
                target_field=target_field['key'],
                experiment_set=config_dict['experiment_set'],
                control_set=config_dict['control_set'][0]
            )
            # 增加 title 作为 dafaFrame 的 top level index
            title_str =f"# {target_field['key']} detail analysis" 
            matrix.columns = pd.MultiIndex.from_product([[title_str],matrix.columns])
            # end
            # out_list.append(matrix)
            one_field_data.append(matrix)
        # 构造单指标聚合输出
        out_one_field = pd.concat(one_field_data,axis=1)
        out_one_field = out_one_field.loc[:,~out_one_field.columns.duplicated()]
        out_list.append(out_one_field)
    # 完成单指标输出
    return {
            "data":out_list,
            "project_title": config_dict['project_title'],
            "date_range":date_range_str,
            "brief_conclusion": brief_conclusion,
            "total_conclusion": total_conclusion
            }
                

def generate_detail_matrix(
        dataframe,
        date_field,
        experiment_flag_field,
        target_field,
        experiment_set,control_set) -> str:
    sub_matrix = dataframe.groupby(by=[date_field,experiment_flag_field])[target_field].agg(['mean'])
    sub_matrix = sub_matrix.unstack(level=1)
    sub_matrix.columns = sub_matrix.columns.droplevel()
    for exp in experiment_set:
        new_field_1 = f"absDiff_{exp}vs{control_set}"
        sub_matrix[new_field_1] = sub_matrix[exp] - sub_matrix[control_set]
        new_field_2 = f"relaDiff_{exp}vs{control_set}"
        sub_matrix[new_field_2] = sub_matrix[exp]/sub_matrix[control_set] - 1
    # 统一输出平均数
    sub_matrix.loc['mean'] = sub_matrix.mean()
    # 输出数据
    return sub_matrix
    

def out_put_to_file(data_frame,config_dict):
    out = get_brief_conclusion(data_frame,config_dict)
    project_title = out["project_title"]
    date_range = out['date_range']
    out_file_path = f"{project_title}_{date_range}.xlsx"
    out_file_path = out_file_path.replace("/","-").replace(":","-")
    outWriter = pd.ExcelWriter(out_file_path)
    # 构造输出
    startrow = 0
    count = 0
    for df in out['data']:
        count += 1
        if count <=2:
            df.to_excel(outWriter,startrow=startrow,index=False)
            startrow += len(df) + 1 + 2
        else:
            df.to_excel(outWriter,startrow=startrow)
            # index 不计入 len(df) 需要补充基数兼容
            startrow += len(df) + 3 + 2
    outWriter.close()
    return {
            "brief_conclusion": out["brief_conclusion"],
            "total_conclusion": out["total_conclusion"],
            "out_file_path":out_file_path,
            "target_field_detail":out["data"][1:]
    }