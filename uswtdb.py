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


sidebar_selector = st.sidebar.selectbox('Select Category:', ('Project Information', 'Deep Dive', 'Wind Turbine Detailed Aggregation', 'US Turbine Map'))

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
        go.Scatter(x=tb_cumsum.index, y=tb_cumsum.case_id, name="Cumulative Turbine Installs", mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(
        go.Scatter(x=cap_cumsum.index, y=cap_cumsum.t_cap, name="Cumulative Capacity (MW)", marker_color='Black', mode='lines'),
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
    fig = fig.update_yaxes(title_text="Cumulative", secondary_y=True)

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
        go.Scatter(x=tb_cumsum.index, y=tb_cumsum.case_id, name="Cumulative Turbine Installs", mode='lines'),
        secondary_y=True,
    )

    fig = fig.add_trace(
        go.Scatter(x=cap_cumsum.index, y=cap_cumsum.t_cap, name="Cumulative Capacity (MW)", marker_color='Black',
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
    fig = fig.update_yaxes(title_text="Cumulative", secondary_y=True)

    return fig

def generate_texas_map(df):
    texas_df = df[df['t_state'] == 'TX']
    texas_df = texas_df[texas_df['p_year'] >= 2010]
    texas_df = texas_df.rename(columns={"xlong": "lon", "ylat": "lat"})
    texas_df = texas_df[['case_id', 'lon', 'lat']]
    texas_df = texas_df.dropna()
    return texas_df


def texas_capacity_cp(df):
    texas_cp = df[df['t_state'] == 'TX']
    texas_cp = texas_cp.groupby('p_year')[['t_cap']].sum()
    texas_cp = texas_cp.rename(columns={'t_cap': 'Texas'})

    all_cp = df.groupby('p_year')[['t_cap']].sum()
    all_cp = all_cp.rename(columns={'t_cap': 'All'})

    texas_cp = texas_cp.merge(all_cp, on='p_year')
    texas_cp['New Capacity'] = texas_cp['Texas'] / texas_cp['All']

    texas_cumsum = texas_cp[['Texas']].cumsum()
    all_cumsum = texas_cp[['All']].cumsum()

    texas_cumsum = texas_cumsum.merge(all_cumsum, on='p_year')
    texas_cumsum['Total Capacity'] = texas_cumsum['Texas'] / texas_cumsum['All']

    texas_cp = texas_cp[['New Capacity']].merge(texas_cumsum['Total Capacity'], on='p_year')
    texas_cp = texas_cp[2010:2019]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig = fig.add_trace(
        go.Scatter(x=texas_cp.index, y=texas_cp['New Capacity'], name="New Capacity %", mode='lines')
    )

    fig = fig.add_trace(
        go.Scatter(x=texas_cp.index, y=texas_cp['Total Capacity'], name="Total Capacity %", mode='lines')
    )

    fig = fig.update_xaxes(title_text="Year")

    # Set y-axes titles
    fig = fig.update_yaxes(title_text="Texas Share of Capacity", secondary_y=False)

    fig = fig.update_layout(yaxis=dict(tickformat='%.format.%3f', hoverformat='.3f'))

    return fig

def get_state_capcaity(df):
    by_state = df.groupby('t_state')[['t_cap']].count()
    by_state['Percent of US Wind Capacity'] = by_state['t_cap']/by_state['t_cap'].sum()
    by_state.sort_values(by='Percent of US Wind Capacity', ascending=False,inplace=True)
    by_state['Percent of US Wind Capacity'] = by_state['Percent of US Wind Capacity'].astype(float).map("{:.2%}".format)
    by_state = by_state.reset_index()
    by_state = by_state.rename(columns={'t_state': 'State'})
    by_state = by_state[0:12][['State', 'Percent of US Wind Capacity']]
    return by_state


def get_texas_manu(df):
    texas_manu = df[df['t_state'] == 'TX']
    texas_manu = texas_manu.replace({'Gamesa': 'Siemens', 'Siemens Gamesa Renewable Energy': 'Siemens'})
    texas_manu = texas_manu.groupby('t_manu')[['case_id']].count()
    texas_manu.sort_values(by='case_id', inplace=True, ascending=False)
    texas_manu['Percent of Texas Turbines'] = texas_manu['case_id'] / texas_manu['case_id'].sum()
    texas_manu = texas_manu[['Percent of Texas Turbines']]

    texas_manu = texas_manu.rename(columns={'t_manu': 'Manufacturer'})

    texas_manu = texas_manu[0:4]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig = fig.add_trace(go.Bar(
        x=texas_manu.index,
        y=texas_manu['Percent of Texas Turbines'],
        name='Turbine Installs/Year',
        marker_color='indianred',

    ))

    # Set x-axis title
    fig = fig.update_xaxes(title_text="Year")

    fig = fig.update_layout(yaxis=dict(tickformat='%.format.%3f', hoverformat='.3f'))

    # Set y-axes titles
    fig = fig.update_yaxes(title_text="Percent of Texas Turbines", secondary_y=False)

    return fig



if sidebar_selector == 'Project Information':
    URL = 'https://github.com/chrisbaugh-user/USWTDB/blob/master/rigup-logo-v1_FS.png?raw=True'

    with urllib.request.urlopen(URL) as url:
        with open('temp.jpg', 'wb') as f:
            f.write(url.read())
    
    
    image = Image.open('temp.jpg')
    st.image(image, use_column_width=True, caption='By: Chris Baugh (chrisbaugh@me.com)')
    
    st.title('United States Wind Turbine Database')
    st.write('This dashboard was created to explore and understand the data from the United States Wind Turbine Database (USWTDB). The USWTDB provides the locations of land-based and offshore wind turbines in the United States, corresponding wind project information, and turbine technical specifications. The data set is maintained by the U.S. Department of Energy (DOE), the U.S. Geological Survey (USGS), and the American Wind Energy Association (AWEA).')

elif sidebar_selector == 'Wind Turbine Detailed Aggregation':

    st.title('Wind Turbine Detailed Aggregation')

    installation_min = int(df.p_year.min())
    installation_max = int(df.p_year.max())

    agg_dropdown = st.selectbox('Group By:', ('State', 'County', 'Manufacturer', 'Project'))

    dropdown_dict = {'State': 't_state', 'County': 't_county', 'Manufacturer': 't_manu', 'Project': 'p_name'}

    year = st.slider('Installation Year', installation_min, installation_max, (installation_min, installation_max))

    cp_data = get_cp_agg(year, dropdown_dict[agg_dropdown])

    st.write(cp_data)


elif sidebar_selector == 'US Turbine Map':
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

    st.write('Since 2005, the number of wind turbines in the US has increased almost 5x, while the total capacity has increased 13x. This difference is a result of the increases in the capacity per turbine, which has increased by 57% since 2005 to 2.25 MW/turbine.')

    # chart

    st.plotly_chart(generate_turb_chart(df), use_container_width=True)

    st.write('With the exception of 2013, the US wind market has recently seen impressive growth. Wind production slowed in 2013 as a result of an extension to the production tax credit (PTC) in January 2013 that altered PTC-eligibility guidelines to only require construction to have begun by the end of that year.')

    st.write('Wind energy is concentrated in only a few states, with 12 states producing 80% of all wind power in the US. This is a result of wind only being viable in certain parts of the US, the tradeoffs between other renewables such as solar, as well as regulatory and cost considerations.')

    st.write(get_state_capcaity(df))

    st.title('Texas Wind Trends')

    st.write('Texas produces the most wind power of any US state, and if Texas was a country, it would rank fifth in the world (behind China, the United States, Germany, and India). In 2017, 15.7% of electricity generated in Texas came from wind.')

    st.plotly_chart(generate_texas_chart(df), use_container_width=True)

    st.write('The start of the wind power boom in Texas is partially the result of the state’s Renewable Portfolio Standard (RPS). While RPS helped kick off the wind boom in Texas, construction quickly outpaced the targets. The 2025 goal of 10,000 MW of renewable energy was reached 15 years early in 2010. Despite already hitting the RPS goal, in 2016, Texas had more wind power under construction than any other state currently has installed. Since 2010, 27% of added wind capacity in the US has been installed in Texas, and 35% since 2015, with most installations located in the Rio Grande Valley, West Texas, and the Texas Panhandle.')

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
    Research from the Berkeley Lab suggests that while RPS requirements can kickstart renewable energy production, they are not as correlated with new capacity, but rather create a floor for production (e.g.  2013). The continued production in Texas beyond RPS requirements is likely a result of:    
      
    1. Texas being the only state with its own power grid, which means that new investments and building long-distance transmission lines are done as lawmakers and state regulators see fit. The two other grids in North America (Western Interconnection and Eastern Interconnection) both service multiple states as well as Canada, requiring greater cooperation than Texas’ intrastate grid.      
    2. Texas does make investments in long-distance transmission lines, such as the $7 billion Competitive Renewable Energy Zone (CREZ) unveiled in 2014, which brings West Texas wind power to the Texas Triangle, as well as the Panhandle Renewable Energy Zone (PREZ)."""
    )

    st.write('These advantages are already translating into real world production as Texas has seen its share of new wind capacity steadily increased over the past decade. As Texas has maintained an advantage in new capacity, it has also seen it’s percentage of total wind capacity rise from 21% to 28% since 2013. Given the advantages Texas has in wind power production, it will likely maintain it’s production advantages for the foreseeable future.')

    st.plotly_chart(texas_capacity_cp(df), use_container_width=True)



    st.title('Year 10 Performance Drop and the Maintenance Opportunity')

    st.write('Wind Turbines tend to see reduced performance as they age, and as components fail and need to be replaced, creating downtime. While European Turbines degrade linearly, US turbine degradation does not appear to happen smoothly over time, but involves a step-change in performance after 10 years of operation.')

    st.write('The majority of wind projects in the US have taken advantage of the PTC, which provides wind plants with a production-based tax credit for their first 10 years of operation. This implies that efficiency of wind farms is not just efficiency loss from aging turbines, but US plants are operated differently after they age out of the 10-year PTC window. It appears that in the first 10 years of wind turbines life, the goal is to minimize turbine downtime and maintain turbines at a high level while they can still take advantage of the tax credit. After 10 years, a different maintenance optimization routine is applied.')

    st.write('Therefore, the highest priority maintenance (which is likely the highest priced maintenance due to opportunity costs) for US wind turbines is those that have been built in the last 10 years, and those that will be built in the future, both of which have and will be dominated by Texas.')

    st.title('Sizing and Capturing the Market')
    st.write('Due to the complexity, size, and cost of wind power generation, there are only a small number of manufacturers in the US. In Texas, the 4 biggest manufacturers represent 91% of total turbines. While many manufacturers employ their own technicians, there is currently a shortage of qualified technicians with the field expected to grow by 60% by 2028 according to the US Bureau of Labor Statistics. Given the advantages Texas has in wind power, a large portion of that growth will occur in Texas.')
    st.write('In the US, there are 6,600 technicians servicing 64,000 turbines meaning 1 technician per 10 wind turbines. Therefore, Texas needs around 1,500 technicians to satisfy its current number of wind turbines. The median salary for a wind turbine technician is $52,910, putting the Serviceable Available Market (SAM) at $350m/year in the US and $50-80m in Texas alone.')
    st.write('To be able to adequately capture the market, especially from a contractor model, RigUp will likely want technicians with direct experience on the relevant manufacturers hardware to provide a sufficient value proposition. In Texas, that means finding technicians with experience on GE, Siemens, Vestas, and Mitsubishi turbines.')

    st.plotly_chart(get_texas_manu(df), use_container_width=True)
    
    st.markdown("""## References""")
    st.markdown("""1. [U.S. Renewables Portfolio Standards - 2019 Annual Status Update](https://eta-publications.lbl.gov/sites/default/files/rps_annual_status_update-2019_edition.pdf)  
2. [Development of an Operations and Maintenance Cost Model to Identify Cost of Energy Savings for Low Wind Speed Turbines](https://www.nrel.gov/docs/fy08osti/40581.pdf)  
3. [How Does Wind Project Performance Change with Age in the United States?](https://emp.lbl.gov/publications/how-does-wind-project-performance)  
4. [The Great Texas Wind Power Boom](https://www.forbes.com/sites/judeclemente/2016/10/11/the-great-texas-wind-power-boom/#2f2b8997c6aa)
5. [Near-record growth propels wind power into first place as America’s largest renewable resource](https://web.archive.org/web/20170211080812/http://www.awea.org/MediaCenter/pressreleasev2.aspx?ItemNumber=9812)  
6. [U.S. Bureau of Labor Statistics - Wind Turbine Technicians](https://www.bls.gov/ooh/installation-maintenance-and-repair/wind-turbine-technicians.htm)  
                """)
