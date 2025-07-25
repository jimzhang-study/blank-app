import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import io
import os # 导入 os 模块用于文件路径操作
from matplotlib.font_manager import FontProperties # 导入 FontProperties

# --- 设置页面基本信息 ---
st.set_page_config(layout="wide", page_title="China 营收预测仪表盘")

st.title("📊 中国商务实施服务营收预测")
st.markdown("---")

# --- 解决中文乱码和负号问题 ---
# 指定字体文件的路径
# 确保 'SourceHanSansSC-Regular.otf' 文件和你的 Python 脚本在同一个文件夹里
font_path = 'SourceHanSansSC-Regular.otf' 

# 检查字体文件是否存在，以防万一
if not os.path.exists(font_path):
    st.error(f"字体文件 '{font_path}' 未找到。请确保字体文件已放在脚本同一目录下。")
    st.stop() # 如果字体文件不存在，停止应用

# 创建 FontProperties 对象
font_prop = FontProperties(fname=font_path)

# 将字体设置应用到 Matplotlib
plt.rcParams['font.family'] = font_prop.get_name() # 使用 font_prop.get_name() 获取字体名称
plt.rcParams['axes.unicode_minus'] = False # 解决保存图像时负号 '-' 显示为方块的问题
# ------------------------------------

# --- 初始数据 (硬编码在脚本中) ---
# 这个数据只在保存文件不存在时作为“第一次”的启动数据
initial_main_data_csv_string = """
Year,Total Impl. Team Service Revenue (M USD),CRM Project Revenue (M USD),New Products Project Revenue (M USD),MNC Project Revenue (M USD),Domestic Project Revenue (M USD)
2025,5.50,4.95,0.55,5.44,0.06
2026,4.05,3.24,0.81,3.65,0.40
2027,4.08,2.86,1.22,3.26,0.82
"""

initial_new_products_types_csv_string = """
Product Type,2025 %,2026 %,2027 %
China CRM,95,90,80
Network,5,5,5
AI/Vault,0,5,15
"""

# --- 定义保存数据的文件路径 ---
MAIN_DATA_FILE = "veeva_main_data.csv"
NEW_PRODUCTS_DATA_FILE = "veeva_new_products_data.csv"

# --- 数据加载函数 ---
@st.cache_resource # 使用 st.cache_resource 缓存资源，这里是数据文件本身
def load_main_data():
    if os.path.exists(MAIN_DATA_FILE):
        df = pd.read_csv(MAIN_DATA_FILE)
        st.sidebar.success(f"已从 '{MAIN_DATA_FILE}' 加载数据。")
    else:
        df = pd.read_csv(io.StringIO(initial_main_data_csv_string))
        st.sidebar.info(f"'{MAIN_DATA_FILE}' 不存在，已加载初始数据。")
    df['Year'] = df['Year'].astype(int)
    return df

@st.cache_resource
def load_new_products_data():
    if os.path.exists(NEW_PRODUCTS_DATA_FILE):
        df = pd.read_csv(NEW_PRODUCTS_DATA_FILE)
        st.sidebar.success(f"已从 '{NEW_PRODUCTS_DATA_FILE}' 加载新产品数据。")
    else:
        df = pd.read_csv(io.StringIO(initial_new_products_types_csv_string))
        st.sidebar.info(f"'{NEW_PRODUCTS_DATA_FILE}' 不存在，已加载初始新产品数据。")
    return df


# --- 数据保存函数 ---
def save_data():
    st.session_state.main_df_data_raw.to_csv(MAIN_DATA_FILE, index=False)
    st.session_state.new_products_df.to_csv(NEW_PRODUCTS_DATA_FILE, index=False)
    st.sidebar.success("✅ 数据已保存！")


# --- 自动计算并平衡数据的函数 ---
def calculate_and_balance_main_data():
    df_edited = st.session_state.main_df_data_raw.copy()

    # Streamlit data_editor 会在 on_change 发生时，将最新的编辑存储在这里
    if "edited_rows" in st.session_state.get("main_data_editor_key", {}):
        edited_rows = st.session_state["main_data_editor_key"]["edited_rows"]
        
        for row_idx, changes in edited_rows.items():
            current_row_before_edit = df_edited.loc[row_idx].copy()
            
            # 将data_editor中的最新编辑应用到df_edited的这一行
            for col, new_val in changes.items():
                df_edited.at[row_idx, col] = new_val

            epsilon = 1e-6 

            new_total = df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)']
            new_crm = df_edited.at[row_idx, 'CRM Project Revenue (M USD)']
            new_new_prod = df_edited.at[row_idx, 'New Products Project Revenue (M USD)']
            new_mnc = df_edited.at[row_idx, 'MNC Project Revenue (M USD)']
            new_domestic = df_edited.at[row_idx, 'Domestic Project Revenue (M USD)']

            modified_in_this_row = [col for col in changes.keys()]

            if 'Total Impl. Team Service Revenue (M USD)' in modified_in_this_row:
                if current_row_before_edit['Total Impl. Team Service Revenue (M USD)'] != 0:
                    factor = new_total / current_row_before_edit['Total Impl. Team Service Revenue (M USD)']
                else: 
                    factor = 1 
                    
                df_edited.at[row_idx, 'CRM Project Revenue (M USD)'] = current_row_before_edit['CRM Project Revenue (M USD)'] * factor
                df_edited.at[row_idx, 'New Products Project Revenue (M USD)'] = current_row_before_edit['New Products Project Revenue (M USD)'] * factor
                df_edited.at[row_idx, 'MNC Project Revenue (M USD)'] = current_row_before_edit['MNC Project Revenue (M USD)'] * factor
                df_edited.at[row_idx, 'Domestic Project Revenue (M USD)'] = current_row_before_edit['Domestic Project Revenue (M USD)'] * factor
            
            elif 'CRM Project Revenue (M USD)' in modified_in_this_row or \
                 'New Products Project Revenue (M USD)' in modified_in_this_row:
                calculated_total = new_crm + new_new_prod
                df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)'] = calculated_total
                
                if current_row_before_edit['Total Impl. Team Service Revenue (M USD)'] != 0:
                    factor = calculated_total / current_row_before_edit['Total Impl. Team Service Revenue (M USD)']
                else:
                    factor = 1
                
                df_edited.at[row_idx, 'MNC Project Revenue (M USD)'] = current_row_before_edit['MNC Project Revenue (M USD)'] * factor
                df_edited.at[row_idx, 'Domestic Project Revenue (M USD)'] = current_row_before_edit['Domestic Project Revenue (M USD)'] * factor

            elif 'MNC Project Revenue (M USD)' in modified_in_this_row or \
                 'Domestic Project Revenue (M USD)' in modified_in_this_row:
                calculated_total = new_mnc + new_domestic
                df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)'] = calculated_total

                if current_row_before_edit['Total Impl. Team Service Revenue (M USD)'] != 0:
                    factor = calculated_total / current_row_before_edit['Total Impl. Team Service Revenue (M USD)']
                else:
                    factor = 1
                
                df_edited.at[row_idx, 'CRM Project Revenue (M USD)'] = current_row_before_edit['CRM Project Revenue (M USD)'] * factor
                df_edited.at[row_idx, 'New Products Project Revenue (M USD)'] = current_row_before_edit['New Products Project Revenue (M USD)'] * factor
            
            # --- 最终校验和处理浮点数精度 ---
            if abs((df_edited.at[row_idx, 'CRM Project Revenue (M USD)'] + df_edited.at[row_idx, 'New Products Project Revenue (M USD)']) - df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)']) > epsilon:
                df_edited.at[row_idx, 'New Products Project Revenue (M USD)'] = df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)'] - df_edited.at[row_idx, 'CRM Project Revenue (M USD)']

            if abs((df_edited.at[row_idx, 'MNC Project Revenue (M USD)'] + df_edited.at[row_idx, 'Domestic Project Revenue (M USD)']) - df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)']) > epsilon:
                df_edited.at[row_idx, 'Domestic Project Revenue (M USD)'] = df_edited.at[row_idx, 'Total Impl. Team Service Revenue (M USD)'] - df_edited.at[row_idx, 'MNC Project Revenue (M USD)']

    st.session_state.main_df_data_raw = df_edited.round(2)


# --- 计算百分比和比率 (只用于图表显示) ---
def calculate_percentages_and_ratios_for_display(df_input):
    df_display = df_input.copy()

    percentage_cols = [
        'CRM Project %', 'New Products Project %',
        'MNC Project %', 'Domestic Project %'
    ]
    for col in percentage_cols:
        if col not in df_display.columns:
            df_display[col] = 0.0

    for index, row in df_display.iterrows():
        total_revenue = row['Total Impl. Team Service Revenue (M USD)']

        # CRM vs 新产品
        crm_rev = row['CRM Project Revenue (M USD)']
        new_prod_rev = row['New Products Project Revenue (M USD)']
        df_display.at[index, 'CRM Project %'] = (crm_rev / total_revenue) * 100 if total_revenue != 0 else 0
        df_display.at[index, 'New Products Project %'] = (new_prod_rev / total_revenue) * 100 if total_revenue != 0 else 0

        # MNC vs 国内客户
        mnc_rev = row['MNC Project Revenue (M USD)']
        domestic_rev = row['Domestic Project Revenue (M USD)']
        df_display.at[index, 'MNC Project %'] = (mnc_rev / total_revenue) * 100 if total_revenue != 0 else 0
        df_display.at[index, 'Domestic Project %'] = (domestic_rev / total_revenue) * 100 if total_revenue != 0 else 0
        
    return df_display.round(2)

# --- 新产品类型数据校验函数 ---
def validate_new_product_percentages():
    df_new_products = st.session_state.new_products_df.copy()
    
    year_cols = [col for col in df_new_products.columns if col.endswith('%')]
    
    for year_col in year_cols:
        total_percent = df_new_products[year_col].sum()
        if abs(total_percent - 100) > 0.1: 
            st.warning(f"⚠️ **警告：** '{year_col}' 列的百分比总和为 {total_percent:.1f}%，不等于 100%。请调整。")
            
    st.session_state.new_products_df = df_new_products # 确保session state更新


# --- 页面布局 ---

# --- 初始化数据 (从文件加载或使用初始字符串) ---
if 'main_df_data_raw' not in st.session_state:
    st.session_state.main_df_data_raw = load_main_data()
    # 首次加载时调用平衡函数，确保初始数据是平衡的
    # 但由于load_main_data会从文件加载（如果存在），而文件可能已被编辑过
    # 这里的平衡功能主要是针对用户在data_editor中的后续编辑
    # 故首次加载不再强制平衡，假定文件是平衡的。
    # 如果文件可能不平衡，可以在这里调用 balance_revenue_data()

if 'new_products_df' not in st.session_state:
    st.session_state.new_products_df = load_new_products_data()
    validate_new_product_percentages() # 首次加载时也校验一次


# --- 左侧边栏的保存按钮 ---
st.sidebar.header("保存数据")
st.sidebar.button("💾 保存当前数据", on_click=save_data, help="将表格中的所有更改保存到 CSV 文件中。")
st.sidebar.markdown("---")
st.sidebar.info("下次启动应用时，将自动加载已保存的数据。")


# --- 1. 主要数据编辑区域 ---
st.header("1. 主要营收数据编辑")
st.info("💡 **操作提示：** 编辑表格中的**任何一个营收数字**，图表和关键指标将自动更新并保持各维度平衡！")

edited_main_df_raw = st.data_editor(
    st.session_state.main_df_data_raw,
    num_rows="fixed",
    column_config={
        "Year": st.column_config.NumberColumn("年份", disabled=True),
        "Total Impl. Team Service Revenue (M USD)": st.column_config.NumberColumn("总营收 (百万美元)", format="%.2fM"),
        "CRM Project Revenue (M USD)": st.column_config.NumberColumn("CRM项目营收 (百万美元)", format="%.2fM"),
        "New Products Project Revenue (M USD)": st.column_config.NumberColumn("新产品营收 (百万美元)", format="%.2fM"),
        "MNC Project Revenue (M USD)": st.column_config.NumberColumn("MNC项目营收 (百万美元)", format="%.2fM"),
        "Domestic Project Revenue (M USD)": st.column_config.NumberColumn("国内客户营收 (百万美元)", format="%.2fM"),
    },
    key="main_data_editor_key",
    on_change=calculate_and_balance_main_data # 数据变化时调用平衡函数
)
st.session_state.main_df_data_raw = edited_main_df_raw # 更新 session state

# df 变量用于图表，基于 main_df_data_raw 计算百分比
df = calculate_percentages_and_ratios_for_display(st.session_state.main_df_data_raw) 

st.markdown("---")

# --- 2. 新产品类型编辑区域 ---
st.header("2. 新产品类型构成编辑")
st.info("💡 **操作提示：** 请确保每年新产品类型百分比的总和为 100%。")

edited_new_products_df = st.data_editor(
    st.session_state.new_products_df,
    num_rows="dynamic", # 允许添加/删除行
    column_config={
        "Product Type": st.column_config.TextColumn("产品类型", help="新产品类型名称"),
        "2025 %": st.column_config.NumberColumn("2025 %", format="%.0f%%", min_value=0, max_value=100),
        "2026 %": st.column_config.NumberColumn("2026 %", format="%.0f%%", min_value=0, max_value=100),
        "2027 %": st.column_config.NumberColumn("2027 %", format="%.0f%%", min_value=0, max_value=100),
    },
    key="new_products_data_editor_key",
    on_change=validate_new_product_percentages # 数据变化时校验
)
st.session_state.new_products_df = edited_new_products_df # 更新 session state

st.markdown("---")

# --- 3. 关键指标 (KPIs) ---
st.header("3. 关键指标 (KPIs)")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📊 预测起始年总营收", value=f"{df.loc[df['Year'] == df['Year'].min(), 'Total Impl. Team Service Revenue (M USD)'].iloc[0]:.2f}M USD")
with col2:
    st.metric(label="📈 预测末年总营收", value=f"{df.loc[df['Year'] == df['Year'].max(), 'Total Impl. Team Service Revenue (M USD)'].iloc[0]:.2f}M USD")
with col3:
    start_year_revenue = df.loc[df['Year'] == df['Year'].min(), 'Total Impl. Team Service Revenue (M USD)'].iloc[0]
    end_year_revenue = df.loc[df['Year'] == df['Year'].max(), 'Total Impl. Team Service Revenue (M USD)'].iloc[0]
    num_years = df['Year'].max() - df['Year'].min()
    if start_year_revenue != 0 and num_years > 0:
        cagr = ((end_year_revenue / start_year_revenue)**(1/num_years) - 1) * 100
        st.metric(label=f"📉 {df['Year'].min()}-{df['Year'].max()} CAGR", value=f"{cagr:.1f}%")
    else:
        st.metric(label="CAGR", value="N/A")
st.markdown("---")

# --- 4. 核心营收趋势图 ---
st.header("4. 营收趋势分析")
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(df['Year'], df['Total Impl. Team Service Revenue (M USD)'], marker='o', linestyle='-', color='blue')
ax1.set_title('Veeva China Commercial Service (Implementation Team) Revenue Trend')
ax1.set_xlabel('年份')
ax1.set_ylabel('营收 (百万美元)')
ax1.set_xticks(df['Year'])
ax1.grid(True, linestyle='--', alpha=0.7)
st.pyplot(fig1)
st.markdown("---")

# --- 5. 细分比例图 ---
st.header("5. 营收构成比例")

# --- CRM vs. New Products ---
st.subheader("1. CRM 项目 vs 新产品项目构成")
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.bar(df['Year'], df['CRM Project %'], color='lightgreen', label='CRM 项目')
ax3.bar(df['Year'], df['New Products Project %'], bottom=df['CRM Project %'], color='orange', label='新产品项目')
ax3.set_title('(CRM vs New Product) (%)')
ax3.set_xlabel('Year')
ax3.set_ylabel('Percentage (%)')
ax3.set_xticks(df['Year'])
ax3.set_ylim(0, 100)
ax3.yaxis.set_major_formatter(mtick.PercentFormatter())
ax3.legend(loc='lower right')
ax3.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig3)

# --- MNC vs. Domestic ---
st.subheader("2. MNC 项目 vs 国内客户项目构成")
fig4, ax4 = plt.subplots(figsize=(10, 5))
ax4.bar(df['Year'], df['MNC Project %'], color='purple', label='MNC 项目')
ax4.bar(df['Year'], df['Domestic Project %'], bottom=df['MNC Project %'], color='gold', label='国内客户项目')
ax4.set_title('(MNC vs Domestic) (%)')
ax4.set_xlabel('Year')
ax4.set_ylabel('Percentage (%)')
ax4.set_xticks(df['Year'])
ax4.set_ylim(0, 100)
ax4.yaxis.set_major_formatter(mtick.PercentFormatter())
ax4.legend(loc='lower right')
ax4.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig4)

st.markdown("---")

# --- 6. 新产品营收细分图 (新增) ---
st.header("6. 新产品营收细分")
st.info("💡 **新产品营收** 基于上方表格中的 '新产品项目营收' 和此表格中的百分比进行计算。")

# 从主数据获取每年的“新产品项目营收”总额
new_products_total_revenue_by_year = df.set_index('Year')['New Products Project Revenue (M USD)'].to_dict()

# 使用新产品类型数据绘制堆叠柱状图
df_new_products_types = st.session_state.new_products_df.copy()

# 将百分比列转换为数值列，方便计算
year_cols_percent = [f'{year} %' for year in df['Year'].unique()]
for col in year_cols_percent:
    df_new_products_types[col] = pd.to_numeric(df_new_products_types[col], errors='coerce').fillna(0) # 确保是数字

# 计算实际营收
df_new_products_revenue_for_plot = df_new_products_types[['Product Type']].copy()
for year in df['Year'].unique():
    year_percent_col = f'{year} %'
    total_np_rev_this_year = new_products_total_revenue_by_year.get(year, 0)
    df_new_products_revenue_for_plot[f'{year} Revenue (M USD)'] = (df_new_products_types[year_percent_col] / 100) * total_np_rev_this_year

# 绘制堆叠柱状图
fig_np, ax_np = plt.subplots(figsize=(10, 6))

bottom_values = [0] * len(df['Year'].unique()) # 初始化底部值

# 确保years_for_plot是整数，用于ax_np.bar的x轴
years_for_plot = df['Year'].unique().astype(int)

for idx, row in df_new_products_revenue_for_plot.iterrows():
    product_type = row['Product Type']
    revenues = [row[f'{year} Revenue (M USD)'] for year in df['Year'].unique()]
    
    ax_np.bar(years_for_plot, revenues, bottom=bottom_values, label=product_type)
    
    # 更新底部值
    bottom_values = [b + r for b, r in zip(bottom_values, revenues)]

ax_np.set_title('New Product segmentation(Millions $)', fontsize=14)
ax_np.set_xlabel('Year', fontsize=12)
ax_np.set_ylabel('Revenue (Millions $)', fontsize=12)
ax_np.set_xticks(years_for_plot)
ax_np.grid(axis='y', linestyle='--', alpha=0.7)
ax_np.legend(title='Product Type', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
st.pyplot(fig_np)

st.markdown("---")
st.info("💡 **操作提示：** 在 '主要营收数据编辑' 表格和 '新产品类型构成编辑' 表格中直接点击并修改数字，图表和关键指标将自动更新！")