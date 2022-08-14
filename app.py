import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DIM_NAMES = {
    'pdi': 'Power Distance Index',
    'idv': 'Individualism v. Collectivism',
    'mas': 'Masculinity v. Femininity',
    'uai': 'Uncertainty Avoidance Index',
    'ltowvs': 'Long- v. Short-Term Orientation',
    'ivr': 'Indulgence v. Restraint'
}

DIM_SELF_DEFAULTS = {
    'pdi': 20,
    'idv': 100,
    'mas': 20,
    'uai': 20,
    'ltowvs': 80,
    'ivr': 80
}

def load_data():
    # data source: https://geerthofstede.com/research-and-vsm/dimension-data-matrix/
    csv_path = 'https://docs.google.com/spreadsheet/ccc?key=16xeWRWQgh-7NGsaTOz4EnZkH9662Gy9T51K5lOBvW2E&output=csv'
    df_raw = pd.read_csv(csv_path)
    rows_no_null = ((df_raw=='#NULL!').sum(axis=1)==0)
    df_raw = df_raw[rows_no_null].reset_index(drop=True)
    int_cols = [col for col in df_raw.columns if col not in ['ctr', 'country']]
    df_raw[int_cols] = df_raw[int_cols].astype(int)
    return df_raw


def compute_similarity_score(df, dim_self, dim_weights):
    df_loss = df.copy()
    for dim in dim_self:
        print(dim_self[dim], df_loss[dim].values)
        df_loss[f"{dim}_loss"] = abs(dim_self[dim] - df_loss[dim]) * dim_weights[dim]
    df_loss['loss'] = df_loss[[col for col in df_loss.columns if '_loss' in col]].sum(axis=1)
    df_loss['similarity_score'] = (((100 * sum(dim_weights.values())) - df_loss['loss']) / (sum(dim_weights.values()))).round(1)
    return df_loss.sort_values('similarity_score')


def create_bar_fig(df_loss, barplot_hue_dim):
    df_plt = df_loss[['country', 'similarity_score']].sort_values('similarity_score', ascending=False)
    df_plt = df_loss.sort_values('similarity_score')
    df_plt = df_plt.rename(columns=DIM_NAMES)

    fig = px.bar(
        df_plt, 
        x="similarity_score", 
        y="country", 
        color=barplot_hue_dim, 
        orientation='h',
        hover_data=DIM_NAMES.values(),
        height=1000,
        labels={
                     "country": "",
                     "similarity_score": "Similarity score"
                 },
        range_color=[0,100]
        )

    fig.update_layout(
    
        font=dict(
            family="Arial",
            size=10,
            color="white"
            ),

        xaxis=dict(
            tickfont=dict(family='Arial', size=20, color='white')
            ),

        coloraxis=dict(
            colorbar=dict(
                tickfont=dict(size=14, color='white')
                )
            )
        )
    return fig


def create_radar_plot(df, countries_plot, dim_self, colors_plt = ['blue', 'red']):
    fig = go.Figure()

    # Plot 2 countries data
    for country, color_plt in zip(countries_plot, colors_plt):
        fig.add_trace(go.Scatterpolar(
            r=list(df.loc[df['country']==country, DIM_NAMES.keys()].values[0]),
            theta=list(DIM_NAMES.values()),
            fill='toself',
            name=country, 
            line=dict(color=color_plt),
        ))
        
        # Fill in final connection
        fig.add_trace(go.Scatterpolar(
            r=[list(df.loc[df['country']==country, DIM_NAMES.keys()].values[0])[-1], 
               list(df.loc[df['country']==country, DIM_NAMES.keys()].values[0])[0]],
            theta=[list(DIM_NAMES.values())[-1], list(DIM_NAMES.values())[0]],
            fill=None, 
            line=dict(color=color_plt),
            showlegend=False
        ))
        
    # Plot your preferences
    fig.add_trace(go.Scatterpolar(
        r=list(dim_self.values()),
        theta=list(DIM_NAMES.values()),
        fill=None,
        name='You', 
        line=dict(color='rgb(192,192,192)'),
        fillcolor=None
    ))

    # Fill in final connection
    fig.add_trace(go.Scatterpolar(
        r=[list(dim_self.values())[-1], list(dim_self.values())[0]],
        theta=[list(DIM_NAMES.values())[-1], list(DIM_NAMES.values())[0]],
        fill=None, 
        line=dict(color='rgb(192,192,192)'),
        fillcolor=None,
        showlegend=False
    ))

    # Formatting
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=False,
                range=[0, 100],
                showticklabels=False,
            )
        ),
        
        font=dict(
            family="Arial",
            size=14,
            color="white"
        ),
        
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5,
            font=dict(
                family="Arial",
                size=20,
                color="white"
            )
        ),
        
        height=500, 
        autosize=False,
    )
    return fig


df = load_data()
all_countries = df['country'].values

st.set_page_config(
    layout="wide",
    page_icon=':flags:',
    page_title="Hofstede's Dimensions"
)

st.title("Hofstede's cultural dimensions explorer")
st.write("Links: [[Dimension definitions]](https://www.mindtools.com/pages/article/newLDR_66.htm), [[Data source]](https://geerthofstede.com/research-and-vsm/dimension-data-matrix/), [[Freakonomics episode]](https://freakonomics.com/podcast/the-pros-and-cons-of-americas-extreme-individualism-ep-470-2/)")
st.header("Part 1 - Define your culture & rank countries")
col1, col2, col3 = st.columns([1, 1, 3])

# Define preference in 1st column
dim_self = {}
col1.text('Preferred dimension values')
for dim_name, dim_name_full in DIM_NAMES.items():
    dim_self[dim_name] = col1.slider(dim_name_full, 0, 100, DIM_SELF_DEFAULTS[dim_name], 5)

# Define weights in 2nd column
dim_weights = {}
col2.text('Dimension weighting')
for dim_name, dim_name_full in DIM_NAMES.items():
    dim_weights[dim_name] = col2.slider(f"{dim_name_full}, weight", 0.0, 1.0, 1.0, 0.1)

# Bar plot
barplot_hue_dim = col1.selectbox('Dimension for barplot color', DIM_NAMES.values(), index=0)
df_loss = compute_similarity_score(df, dim_self, dim_weights)
chart = col3.empty()
fig_bar = create_bar_fig(df_loss, barplot_hue_dim)
chart.plotly_chart(fig_bar, use_container_width=True)


# Define 2 countries to compare in 3rd column
st.header("Part 2 - Compare your ideal culture to 2 countries")
col1b, col2b = st.columns([1,3])
best_country_default = df_loss.sort_values('similarity_score', ascending=False).head(1)['country'].values[0]
selected_country1 = col1b.selectbox('Country 1 in radar plot', all_countries, index=int(df[df['country']==best_country_default].index[0]))
selected_country2 = col1b.selectbox('Country 2 in radar plot', all_countries, index=61)

# Create radar plot
chart_radar = col2b.empty()
fig_radar = create_radar_plot(df, [selected_country1, selected_country2], dim_self)
chart_radar.plotly_chart(fig_radar, use_container_width=True)
