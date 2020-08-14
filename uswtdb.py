import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit_theme as stt
from PIL import Image
import urllib.request
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


df = pd.read_csv("https://raw.githubusercontent.com/chrisbaugh-user/USWTDB/master/uswtdb_v3_1_20200717.csv")
stt.set_theme({'primary': '#064658'})


sidebar_selector = st.sidebar.selectbox('Select Category:', ('Project Information', 'Deep Dive', 'Wind Turbine Detailed Aggregation', 'Estimated Labor Costs', 'Turbine Map'))

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

def generate_texas_map(df):
    texas_df = df[df['t_state'] == 'TX']
    texas_df = texas_df[texas_df['p_year'] >= 2010]
    texas_df = texas_df.rename(columns={"xlong": "lon", "ylat": "lat"})
    texas_df = texas_df[['case_id', 'lon', 'lat']]
    texas_df = texas_df.dropna()
    return texas_df


def texas_cp(df):
    texas_df = df[df['t_state'] == 'TX']
    texas = texas_df.groupby('p_year')[['case_id']].count()
    all_df = df.groupby('p_year')[['case_id']].count()
    texas_cp = texas.merge(all_df, on='p_year')
    texas_cp['cp'] = texas_cp.case_id_x / texas_cp.case_id_y
    texas_cp = texas_cp[2010:2020]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig = fig.add_trace(
        go.Scatter(x=texas_cp.index, y=texas_cp.cp, name="Cummulative Turbine Installs", mode='lines')
    )

    fig = fig.update_xaxes(title_text="Year")

    # Set y-axes titles
    fig = fig.update_yaxes(title_text="Texas CP", secondary_y=False)

    return fig



if sidebar_selector == 'Project Information':
    URL = 'https://github.com/chrisbaugh-user/USWTDB/blob/master/rigup-logo-v1_FS.png?raw=True'

    with urllib.request.urlopen(URL) as url:
        with open('temp.jpg', 'wb') as f:
            f.write(url.read())
    
    
    image = Image.open('temp.jpg')
    st.image(image, use_column_width=True, caption='By: Chris Baugh (chrisbaugh@me.com)')
    st.title('United States Wind Turbine Database')
    st.write('This dashboard was created to explore and understand the data from the United States Wind Turbine Database (USWTDB). The USWTDB provides the locations of land-based and offshore wind turbines in the United States, corresponding wind project information, and turbine technical specifications. The data set is maintained by the US Department of Energy (DOE), the U.S. Geological Survey (USGS), and the American Wind Energy Association (AWEA).')

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

    st.write(
        'Texas produces the most wind power of any U.S. state, and if Texas was a country, it would rank fifth in the world (behind China, the United States, Germany, and India). In 2017, 15.7% of electricity generated in Texas came from wind according to ERCOT. The wind power boom in Texas is partially the result of expansion of the states’ Renewable Portfolio Standard (RPS), which increased production of renewable energy sources.')

    st.plotly_chart(generate_texas_chart(df), use_container_width=True)

    st.write('While RPS standards help kick off the wind boom in Texas, the 2025 goal of 10,000 MW of renewable energy was reached 15 years early in 2010. Despite already hitting their RPS goals, since 2010, 27% of added wind capacity in the US has been installed in Texas, and 35% since 2015, with most installations happening around the Rio Grande Valley, West Texas, and the Texas Panhandle.')

    deep_dive_map = generate_texas_map(df)

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=30.263397,
            longitude=-97.744575,
            zoom=4,
            pitch=30,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=deep_dive_map,
                get_position='[lon, lat]',
                radius=20000,
                elevation_scale=20,
                elevation_range=[0, 10000],
                pickable=True,
                extruded=True,
            )
        ]
    ))

    st.markdown("""
    Research from the Berkeley Lab suggests that while RPS requirements can kickstart renewable energy production, they create a floor for production (e.g.  2013). The continued production in Texas beyond RPS requirements is likely a result of:  
      
    1. Texas being the only state with its own power grid (ERCOT) which means that new investments and building long-distance transmission lines are done as lawmakers and state regulators see fit, while all other electrical grids in North America span multiple states and in some cases countries.    
    2. Texas does make investments in long-distance transmission lines, such as the $7 billion Competitive Renewable Energy Zone (CREZ) unveiled in 2014 which brings West Texas wind power to the Texas Triangle, as well as the Panhandle Renewable Energy Zone (PREZ). """
    )

    st.write('For these reasons, Texas will likely maintain its dominance in wind power production for the foreseeable future. ')

    st.title('Year 10 Performance Drop and the Maintenance Opportunity')

    st.write('Wind Turbines tend to see reduced performance as they age and components fail and need to be replaced, creating downtime. While European Turbines degrade linearly, this degradation does not appear to happen smoothly over time, but involves a step-change in performance after 10 years of operation. ')

    st.write('The majority of wind projects in the US have taken advantage of the PTC, which provides wind plants with a production-based tax credit for their first 10 years of operation. This implies that efficiency of wind farms is not just efficiency loss from aging turbines, but US plants are operated differently after they age out of the 10-year PTC window. It appears that in the first 10 years of wind turbines life, the goal is to minimize turbine downtime and maintain turbines at a high level while they can still take advantage of the tax credit. After 10 years, a different maintenance optimization routine is applied.')

    st.write('Therefore, the highest priority maintenance (which is likely the highest priced maintenance due to opportunity costs) for US wind turbines is those that have been built in the last 10 years, and those that will be built in the future, both of which have been dominated by Texas.')

    st.plotly_chart(texas_cp(df), use_container_width=True)
