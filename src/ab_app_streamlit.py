#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :   ab_app_streamlit.py
@Time    :   2023/09/26 08:04:50
@Author  :   Jason XU 
@Version :   1.0
@Desc    :   None
'''

import streamlit as st
import pandas as pd
import numpy as np
import time,os,sys
import plotly.express as px
# 引用计算脚本
sys.path.append(os.path.abspath('.'))
from data_calculator import *

# 侧边栏目
## 数据获取
st.sidebar.title("Step1：载入数据")
uploaded_file = st.sidebar.file_uploader("上传数据文件(excel格式)")
if uploaded_file != None:
    data = pd.read_excel(uploaded_file)
    # 展示前3行数据作为预览
    st.sidebar.write(data.head(3))
else:
    time.sleep(1000)

## 配置选项
st.sidebar.title("Step2：关键字段配置")
### 配置主要字段表头
date_field = st.sidebar.selectbox('选择日期字段', data.columns)
## 方便后续时间截取，将日期字段统一修改为 date
# try:
#     data[date_field] = data[date_field].dt.date
try:
    # 兼容原始数据中的非日期字段
    data=pd.read_excel(uploaded_file,dtype={date_field:"datetime64[ns]"})
    data[date_field] = data[date_field].dt.date
    data.sort_values(by=date_field,ascending=False,inplace=True)
except:
    st.warning("请选择正确的存储日期的字段")

## 完成
experiment_flag_field = st.sidebar.selectbox('选择实验组字段', data.columns)

if len(set([date_field,experiment_flag_field])) == 1:
    time.sleep(1000)
else:
    pass

st.sidebar.title("Step3：计算细项配置")

### 选择实验组对照组
exp_list = set(data[experiment_flag_field].to_list())
experiment_sets = st.sidebar.multiselect("选择实验组",exp_list)
control_sets =st.sidebar.multiselect("选择对照组",exp_list - set(experiment_sets))
base_sets = st.sidebar.multiselect("选择基线组",exp_list - set(experiment_sets) - set(control_sets))

### 选择目标字段
target_columns = st.sidebar.multiselect("选择待分析字段", data.columns)

### 配置目标字段格式
if len(target_columns) >0:
    config_df = pd.DataFrame(
        [{"field": i, "是否百分比": True} for i in target_columns]
    )
    new_config_df = st.sidebar.data_editor(config_df)
    target_field_config = []
    for item in zip(new_config_df['field'].to_list(),new_config_df['是否百分比'].to_list()):
        target_field_config.append( {"key":item[0],"type":"percent" if item[1] else "raw"})

### 配置输出文件名称前缀    
form2 = st.sidebar.form(key="提交全部配置",clear_on_submit=False)
project_title=form2.text_input('请输入项目名称（将作为输出文件前缀）', 'Test_1234')
# 手动截取数据
date_start = form2.date_input("数据起始日期",value=data[date_field].min(),min_value=data[date_field].min(),max_value=data[date_field].max())
date_end = form2.date_input("数据终止日期",value=data[date_field].max(),min_value=data[date_field].min(),max_value=data[date_field].max())
submitted2 = form2.form_submit_button("提交计算配置，开始计算")

# 截取数据
data = data[(data[date_field]>=date_start) & (data[date_field]<=date_end)]

if submitted2 != True:
    time.sleep(1000)
else:
    pass

# 数据分析与输出部分

### 构造数据分析配置json
target_field_config = []
for item in zip(new_config_df['field'].to_list(),new_config_df['是否百分比'].to_list()):
    target_field_config.append( {"key":item[0],"type":"percent" if item[1] else "raw"})
# 合并为数据分析config
ab_config = {
    "project_title": project_title,
    "experiment_set": experiment_sets,
    "control_set": control_sets,
    "base_set": base_sets,
    "experiment_flag_field": experiment_flag_field,
    "date_field": date_field,
    "target_field": target_field_config
}

st.title("Part1: 计算配置与文件输出")
st.code(ab_config, language="json", line_numbers=False)
# 引用函数，完成计算
out = out_put_to_file(data_frame=data, config_dict=ab_config)
out_file_path ="file:////" + os.path.abspath('.')+ "\\" + out["out_file_path"]
st.text("Excel 数据分析报告（点击复制至浏览器，可自动下载）")
st.code(out_file_path, language="json", line_numbers=False)        

st.title("Part2: 核心结论输出")
col2_1,col2_2 = st.columns(2) 
with col2_1:
    st.text("简要结论输出")
    st.markdown(("\n").join(out['brief_conclusion']), unsafe_allow_html=False, help=None)
with col2_2:
    st.text("详细结论输出")
    st.markdown(("\n").join(out['total_conclusion']), unsafe_allow_html=False,  help=None)

st.title("Part3: 数据对比图")
for figure_field in target_columns:
# figure_field = st.selectbox("选择目标字段",options=target_columns)
    st.text("【" + figure_field + "】 数据对比图")
    figure_data = data[[date_field,experiment_flag_field,figure_field]]
    figure = px.line(
        data_frame=figure_data,
        x=date_field,
        y=figure_field,
        color=experiment_flag_field,
    )
    figure.update_xaxes(
    tickformatstops=[
        dict(dtickrange=[None, 86400000], value="%b %d\n%Y")
    ])
    figure.update_xaxes(dtick=86400000)
    figure.update_layout(yaxis_range=[0.8*min(figure_data[figure_field]), 1.1*max(figure_data[figure_field])])
    st.plotly_chart(figure_or_data=figure,theme="streamlit")
