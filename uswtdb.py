import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit_theme as stt
from PIL import Image
import urllib.request


df = pd.read_csv("https://raw.githubusercontent.com/chrisbaugh-user/USWTDB/master/uswtdb_v3_1_20200717.csv")
stt.set_theme({'primary': '#064658'})


sidebar_selector = st.sidebar.selectbox('Select Category:', ('Project Information', 'Wind Turbine Detailed Aggregation', 'Estimated Labor Costs', 'Turbine Map'))

def get_cp_agg(years, slider_choice):
    cp_df = df[(df['p_year'] >= years[0]) & (df['p_year'] <= years[1])]
    cp_df['capacity_MW'] = cp_df['t_cap']/1000

    if slider_choice == 't_county':
        mw_cap = cp_df.groupby([slider_choice, 't_state'])[['capacity_MW']].sum()
    else:
        mw_cap = cp_df.groupby(slider_choice)[['capacity_MW']].sum()

    mw_cap.sort_values(by='capacity_MW', inplace=True, ascending=False)
    mw_cap['Capacity CP'] = round((mw_cap['capacity_MW'] / mw_cap['capacity_MW'].sum()) * 100, 2)
    mw_cap['Capacity CP'] = mw_cap['Capacity CP'].astype(int)
    mw_cap['capacity_MW'] = mw_cap['capacity_MW'].astype(int)

    if slider_choice == 't_county':
        turbines_count = cp_df.groupby([slider_choice, 't_state'])[['case_id']].count()
    else:
        turbines_count = cp_df.groupby(slider_choice)[['case_id']].count()

    turbines_count.sort_values(by='case_id', inplace=True, ascending=False)
    turbines_count['Turbine CP'] = round((turbines_count['case_id'] / turbines_count['case_id'].sum()) * 100, 1)
    turbines_count['Turbine CP'] = turbines_count['Turbine CP'].astype(int)

    if slider_choice == 't_county':
        cp = turbines_count.merge(mw_cap, on=[slider_choice, 't_state'])
    else:
        cp = turbines_count.merge(mw_cap, on=slider_choice)
    cp.reset_index(inplace=True)
    cp = cp.rename(columns={'t_manu': 'Manufacturer', 'case_id': 'Turbines', 'capacity_MW': 'Capacity MW', 't_state':'State', 't_county':'County', 'p_name':'Project Name'})
    return cp


def generate_turb_chart(df):
    tb_series = df.groupby('p_year')['case_id'].count()
    tb_cumsum = tb_series.cumsum()
    tb_cumsum = pd.DataFrame(tb_cumsum)

    cap_series = df.groupby('p_year')['t_cap'].sum() / 1000
    cap_cumsum = cap_series.cumsum()
    cap_cumsum = pd.DataFrame(cap_cumsum)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig = fig.add_trace(
        go.Scatter(x=tb_cumsum.index, y=tb_cumsum.case_id, name="Cummulative Turbine Installs", mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(
        go.Scatter(x=cap_cumsum.index, y=cap_cumsum.t_cap, name="Cummulative Capacity (MW)", marker_color='Black', mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(go.Bar(
        x=tb_series.index,
        y=tb_series,
        name='Turbine Installs/Year',
        marker_color='indianred',

    ))

    # Set x-axis title
    fig = fig.update_xaxes(title_text="Year")

    # Set y-axes titles
    fig = fig.update_yaxes(title_text="Turbine Installs/Year", secondary_y=False)
    fig = fig.update_yaxes(title_text="Cummulative", secondary_y=True)

    return fig

def generate_texas_chart(df):
    texas_df = df[df['t_state'] == 'TX']
    tb_series = texas_df.groupby('p_year')['case_id'].count()
    tb_cumsum = tb_series.cumsum()
    tb_cumsum = pd.DataFrame(tb_cumsum)

    cap_series = texas_df.groupby('p_year')['t_cap'].sum() / 1000
    cap_cumsum = cap_series.cumsum()
    cap_cumsum = pd.DataFrame(cap_cumsum)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig = fig.add_trace(
        go.Scatter(x=tb_cumsum.index, y=tb_cumsum.case_id, name="Cummulative Turbine Installs", mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(
        go.Scatter(x=cap_cumsum.index, y=cap_cumsum.t_cap, name="Cummulative Capacity (MW)", marker_color='Black',
                   mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(go.Bar(
        x=tb_series.index,
        y=tb_series,
        name='Turbine Installs/Year',
        marker_color='indianred',

    ))

    # Set x-axis title
    fig = fig.update_xaxes(title_text="Year")

    # Set y-axes titles
    fig = fig.update_yaxes(title_text="Turbine Installs/Year", secondary_y=False)
    fig = fig.update_yaxes(title_text="Cummulative", secondary_y=True)

    return fig

if sidebar_selector == 'Project Information':
    URL = 'https://raw.githubusercontent.com/chrisbaugh-user/USWTDB/blob/master/rigup-logo-v1_FS.png'

    with urllib.request.urlopen(URL) as url:
        with open('temp.jpg', 'wb') as f:
            f.write(url.read())
    
    
    image = Image.open('temp.jpg')
    st.image(image, use_column_width=True, caption='By: Chris Baugh (chrisbaugh@me.com)')
    st.title('United States Wind Turbine Database (USWTDB)')
    st.write('This dashboard was created to explore and understand the data from the United States Wind Turbine Database (USWTDB). The USWTDB provides the locations of land-based and offshore wind turbines in the United States, corresponding wind project information, and turbine technical specifications. The data set is maintained by the US Department of Energy, the U.S. Geological Survey (USGS), and the American Wind Energy Association (AWEA).')

elif sidebar_selector == 'Wind Turbine Detailed Aggregation':

    st.title('Wind Turbine Detailed Aggregation')

    installation_min = int(df.p_year.min())
    installation_max = int(df.p_year.max())

    agg_dropdown = st.selectbox('Group By:', ('State', 'County', 'Manufacturer', 'Project'))

    dropdown_dict = {'State': 't_state', 'County': 't_county', 'Manufacturer': 't_manu', 'Project': 'p_name'}

    year = st.slider('Installation Year', installation_min, installation_max, (installation_min, installation_max))

    cp_data = get_cp_agg(year, dropdown_dict[agg_dropdown])

    st.write(cp_data)

elif sidebar_selector == 'Estimated Labor Costs':
    st.title('Estimating Expected Maintanence Costs by Provider')
    st.write('The National Renewable Energy Laboratory estimates that a wind turbine will require between 100 and 350 hours of maintanence/year based on age and power output.')

    labor_df = pd.DataFrame()
    labor_df['Period (Years)'] = ['750 kW to <1 MW', '>1 MW to 2.5 MW']
    labor_df['1-5'] = [100, 200]
    labor_df['6-10'] = [150, 250]
    labor_df['11-15'] = [200, 300]
    labor_df['16-20'] = [250, 350]

    if st.checkbox('Show labor hour estimates'):
        st.subheader('Labor hour estimates')
        st.write(labor_df)

    st.write('Using the NREL estimates, we can estimate expected yearly maintenance costs by a couple of factors')

    data_slice = st.selectbox('Show Maintenance Costs By:', ('State', 'County', 'Manufacturer', 'Project'))
    cost_df = df
    cost_df['years_old'] = 2020 - cost_df['p_year']
    cost_df['maintenance hours'] = (cost_df['years_old'] * 9.39849624) + (cost_df['t_cap'] * 0.11428571)
    cost_df['maintenance cost'] = cost_df['maintenance hours'] * 50

    if data_slice == 'State':
        temp_df = cost_df.groupby('t_state')[['maintenance cost']].sum()
        st.write(temp_df.sort_values(by='maintenance cost', ascending=False))
    elif data_slice == 'County':
        temp_df = cost_df.groupby(['t_county', 't_state'])[['maintenance cost']].sum()
        st.write(temp_df.sort_values(by='maintenance cost', ascending=False))
    elif data_slice == 'Manufacturer':
        temp_df = cost_df.groupby('t_manu')[['maintenance cost']].sum()
        st.write(temp_df.sort_values(by='maintenance cost', ascending=False))
    elif data_slice == 'Project':
        temp_df = cost_df.groupby('p_name')[['maintenance cost']].sum()
        st.write(temp_df.sort_values(by='maintenance cost', ascending=False))

elif sidebar_selector == 'Turbine Map':
    st.title('Wind Turbines in the US')

    # get default year selectors for date slider
    installation_min = int(df.p_year.min())
    installation_max = int(df.p_year.max())

    # date slider to filter cp data table
    map_years = st.slider('Installation Year', installation_min, installation_max, (installation_min, installation_max))
    map_data = df[(df['p_year'] >= map_years[0]) & (df['p_year'] <= map_years[1])]
    map_data = map_data.rename(columns={"xlong": "lon", "ylat": "lat"})
    map_data = map_data[['case_id', 'lon', 'lat']]
    map_data = map_data.dropna()

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=30.263397,
            longitude=-97.744575,
            zoom=5,
            pitch=30,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=map_data,
                get_position='[lon, lat]',
                radius=20000,
                elevation_scale=20,
                elevation_range=[0, 10000],
                pickable=True,
                extruded=True,
            )
        ]
    ))
    
    
elif sidebar_selector == 'Deep Dive':
    st.title('US Wind Trends')

    st.write(
        'Since 2005, cumulative wind turbines in the US have increased almost 5x, while cumulative capacity has increased 13x. This difference is a result of the increases in average capacity per turbine which has increased by 57% since 2005 to 2.25 MW/turbine.')

    # chart

    st.plotly_chart(generate_turb_chart(df), use_container_width=True)

    st.write(
        'With the exception of 2013, the US wind market has recently seen impressive growth. Wind production slowed in 2013 as a result of an extension to the production tax credit (PTC) in January 2013 that altered PTC-eligibility guidelines to only require construction to have begun by the end of that year.')

    st.title('Texas Wind Trends')

    st.plotly_chart(generate_texas_chart(df), use_container_width=True)
