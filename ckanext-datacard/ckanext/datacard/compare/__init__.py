import pandas as pd
import plotly.graph_objects as go

# data: dataframe with metrics as columns
# groups: categories in data, if None no grouping is done
def generate_datacard_plot(data, groups=None):

    assert data is not None
    if groups is not None: 
        assert len(data)==len(groups)

    if groups is None:
        return generate_datacard_plot_single(data)

    fig=go.Figure()
    print('-- figure created')
    
    # creating bar plot for each column in each dataframe
    for group in groups:
        subdata = data[group]
        for col in subdata.iloc[:, subdata.columns != 'Dataset']:
            # print('-- working on column: ', col)
            fig.add_trace( go.Bar(x=subdata['package'], y=subdata[col], name=col, visible=True) )

    # update layout with dropdown for each group making only the relevant bar plots visible        
    def create_layout_button(group, groups, data):

        def map_cols_to(group, boolVal, data):
            subdata = data[group]
            return [ boolVal for col in subdata.iloc[:, subdata.columns != 'Dataset'] ]

        visible = []
        [ visible.extend(map_cols_to(g, g==group, data)) for g in groups ]
        print('-- visible for group ', group, ' : ', visible)

        return dict(label = group,
                    method = 'update',
                    args = [{
                        'visible': visible,
                        'title': group,
                        'showlegend': True
                    }])
    
    fig.update_layout(updatemenus=[go.layout.Updatemenu(
        active = 0,
        buttons = [ create_layout_button(g, groups, data) for g in groups ]
        )
    ])

    print('Done with figure')
    fig.show()
    htmlText = ""
    #fig.write_html(htmlText, include_plotlyjs=False)
    print('Offline plot with data: ')
    htmlText = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
    print(htmlText)
    return htmlText

    # garbage return
    return(u'<a class="btn inspect-datacard" href="www.google.com">Inspect Datacard</a>')

def generate_datacard_plot_single(data):
    pass

# data: dataframe with metrics as columns
# groups: categories in data, if None no grouping is done
def generate_datacard_spreadsheet(data, groups):

    assert data is not None
    if groups is not None:
        assert len(data)==len(groups)

    tables = {}
    if groups is None:
        tables['Datacard'] = data.to_html(table_id='Datacard')
        return tables

    for group in groups:
        if group not in data:
            return None
        subdata = data[group]
        #subdata.set_option('colheader_justify', 'center')
        tables[group] = subdata.to_html(table_id=group, classes='dcstyle')
    print('---Generated tables: ', tables)
    return tables

