import streamlit as st
import numpy as np
import pandas as pd
import pydeck as pdk


df = pd.read_csv("https://raw.githubusercontent.com/chrisbaugh-user/USWTDB/master/uswtdb_v3_1_20200717.csv")

sidebar_selector = st.sidebar.selectbox('Select Category:', ('Project Information', 'Manufacturer Category Position', 'Estimated Labor Costs', 'Turbine Map'))

if sidebar_selector == 'Project Information':
    st.title('United States Wind Turbine Database (USWTDB)')
    st.write('This dashboard was created to explore and understand the data from the United States Wind Turbine Database (USWTDB). The USWTDB provides the locations of land-based and offshore wind turbines in the United States, corresponding wind project information, and turbine technical specifications. The data set is maintained by the US Department of Energy, the U.S. Geological Survey (USGS), and the American Wind Energy Association (AWEA).')

elif sidebar_selector == 'Manufacturer Category Position':
    st.title('Wind Turbine Manufacturer Catagory Position')

    #get default year selectors for date slider
    installation_min = int(df.p_year.min())
    installation_max = int(df.p_year.max())

    #date slider to filter cp data table
    years = st.slider('Installation Year', installation_min, installation_max, (installation_min, installation_max))

    #calculate cp
    cp_df = df[(df['p_year'] >= years[0]) & (df['p_year'] <= years[1])]
    cp_df['capacity_MW'] = cp_df.t_cap / 1000
    manufacturer = cp_df.groupby('t_manu')[['capacity_MW']].sum()
    manufacturer.sort_values(by='capacity_MW', inplace=True, ascending=False)
    manufacturer.capacity_MW = round(manufacturer.capacity_MW, 0).astype(int)
    turbines_count = cp_df.groupby('t_manu')[['case_id']].count()
    turbines_count.sort_values(by='case_id', inplace=True, ascending=False)
    manufacturer['Capacity CP'] = round((manufacturer['capacity_MW'] / manufacturer['capacity_MW'].sum()) * 100, 2)
    turbines_count['Turbine CP'] = round((turbines_count['case_id'] / turbines_count['case_id'].sum()) * 100, 2)
    manufacturer['Capacity CP'] = manufacturer['Capacity CP'].astype(int)
    turbines_count['Turbine CP'] = turbines_count['Turbine CP'].astype(int)
    cp = turbines_count.merge(manufacturer, on='t_manu')
    cp.reset_index(inplace=True)
    cp = cp.rename(columns={'t_manu': 'Manufacturer', 'case_id': 'Turbines', 'capacity_MW': 'Capacity MW'})

    st.write(cp)

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
