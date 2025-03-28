"""
Dash-based dashboard for visualizing sensor data.
"""
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from datetime import datetime, timedelta
import numpy as np

def create_dashboard(storage):
    """
    Create and configure the Dash application for the dashboard.
    
    Args:
        storage: MemoryStorage instance to get data from
    
    Returns:
        Dash application instance
    """
    # Create Dash app with Bootstrap theme
    app = dash.Dash(
        __name__,
        requests_pathname_prefix="/dashboard/",
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title="Echo Monitor"
    )
    
    # Define layout
    app.layout = dbc.Container([
        html.H1("Echo Monitor", className="mt-4 mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H3("Connected Devices"),
                html.Div(id="devices-table")
            ], width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H3("Temperature", className="mt-4"),
                dcc.Graph(id="temperature-graph"),
            ], width=6),
            dbc.Col([
                html.H3("Humidity", className="mt-4"),
                dcc.Graph(id="humidity-graph"),
            ], width=6),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.H3("Door Status", className="mt-4"),
                html.Div(id="door-status")
            ], width=6),
            dbc.Col([
                html.H3("Audio & Vibration", className="mt-4"),
                html.Div(id="audio-status")
            ], width=6),
        ]),
        
        # Auto-refresh component
        dcc.Interval(
            id="interval-component",
            interval=2000,  # in milliseconds (2 seconds)
            n_intervals=0
        )
    ], fluid=True)
    
    # Define callbacks for real-time updates
    @app.callback(
        Output("devices-table", "children"),
        [Input("interval-component", "n_intervals")]
    )
    def update_devices_table(_):
        devices = storage.get_connected_devices()
        
        if not devices:
            return html.Div("No devices connected", className="text-center text-muted my-4")
        
        # Create a simple table
        table_header = [
            html.Thead(html.Tr([
                html.Th("Device ID"),
                html.Th("Status"),
                html.Th("Last Seen")
            ]))
        ]
        
        rows = []
        for device in devices:
            status_badge = html.Span("Online", className="badge bg-success")
            last_seen = device.get("last_seen", "Unknown")
            if last_seen != "Unknown":
                try:
                    last_seen_dt = datetime.fromisoformat(last_seen)
                    last_seen = last_seen_dt.strftime("%H:%M:%S")
                except:
                    pass
                    
            rows.append(html.Tr([
                html.Td(device["device_id"]),
                html.Td(status_badge),
                html.Td(last_seen)
            ]))
        
        table_body = [html.Tbody(rows)]
        
        return dbc.Table(table_header + table_body, bordered=True, hover=True)
    
    @app.callback(
        [Output("temperature-graph", "figure"), 
         Output("humidity-graph", "figure")],
        [Input("interval-component", "n_intervals")]
    )
    def update_graphs(_):
        # Get latest data
        latest_data = storage.get_latest_sensor_data()
        print(f"Dashboard update - Latest data: {latest_data}")
        
        # Default empty graphs
        temp_fig = go.Figure()
        humid_fig = go.Figure()
        
        # If we have data, create some example graphs
        if latest_data:
            # For each device, show temperature
            for device_id, data in latest_data.items():
                # For this prototype, just create some demo data if no actual temp/humidity
                if "temperature" not in data:
                    # Synthetic data for visualization testing
                    times = [datetime.now() - timedelta(seconds=i*5) for i in range(20)]
                    temps_inside = [25 + np.sin(i/10) + np.random.randn()*0.5 for i in range(20)]
                    temps_outside = [20 + np.sin(i/8) + np.random.randn()*1.0 for i in range(20)]
                    
                    temp_fig.add_trace(go.Scatter(
                        x=times, y=temps_inside, mode='lines+markers',
                        name=f"{device_id} (Inside)"
                    ))
                    
                    temp_fig.add_trace(go.Scatter(
                        x=times, y=temps_outside, mode='lines+markers',
                        name=f"{device_id} (Outside)" 
                    ))
                    
                    # Humidity
                    humid_inside = [40 + np.sin(i/15)*10 + np.random.randn()*2 for i in range(20)]
                    humid_outside = [60 + np.cos(i/12)*15 + np.random.randn()*3 for i in range(20)]
                    
                    humid_fig.add_trace(go.Scatter(
                        x=times, y=humid_inside, mode='lines+markers',
                        name=f"{device_id} (Inside)"
                    ))
                    
                    humid_fig.add_trace(go.Scatter(
                        x=times, y=humid_outside, mode='lines+markers',
                        name=f"{device_id} (Outside)"
                    ))
                else:
                    # Get device history for the past 10 minutes
                    history = storage.get_sensor_history(device_id, limit=600)  # Get up to 10 minutes of data
                    
                    # Extract timestamps, temperatures and humidity from history
                    timestamps = []
                    inside_temps = []
                    outside_temps = []
                    inside_humids = []
                    outside_humids = []
                    
                    for entry in history:
                        # Try to parse timestamp
                        try:
                            timestamp = datetime.fromisoformat(entry.get("timestamp", datetime.now().isoformat()))
                            timestamps.append(timestamp)
                        except (ValueError, TypeError):
                            timestamps.append(datetime.now())
                        
                        # Get temperature values
                        temps = entry.get("temperature", {})
                        inside_temps.append(temps.get("inside", 0))
                        outside_temps.append(temps.get("outside", 0))
                        
                        # Get humidity values
                        humids = entry.get("humidity", {})
                        inside_humids.append(humids.get("inside", 0))
                        outside_humids.append(humids.get("outside", 0))
                    
                    # If no history, at least show current point
                    if not timestamps:
                        timestamps = [datetime.now()]
                        temps = data.get("temperature", {})
                        inside_temps = [temps.get("inside", 0)]
                        outside_temps = [temps.get("outside", 0)]
                        
                        humid = data.get("humidity", {})
                        inside_humids = [humid.get("inside", 0)]
                        outside_humids = [humid.get("outside", 0)]
                    
                    # Add traces with lines connecting the points
                    temp_fig.add_trace(go.Scatter(
                        x=timestamps, y=inside_temps, mode='lines+markers',
                        name=f"{device_id} (Inside)",
                        line=dict(width=2)
                    ))
                    
                    temp_fig.add_trace(go.Scatter(
                        x=timestamps, y=outside_temps, mode='lines+markers',
                        name=f"{device_id} (Outside)",
                        line=dict(width=2)
                    ))
                    
                    humid_fig.add_trace(go.Scatter(
                        x=timestamps, y=inside_humids, mode='lines+markers',
                        name=f"{device_id} (Inside)",
                        line=dict(width=2)
                    ))
                    
                    humid_fig.add_trace(go.Scatter(
                        x=timestamps, y=outside_humids, mode='lines+markers',
                        name=f"{device_id} (Outside)",
                        line=dict(width=2)
                    ))
        
        # Configure temp graph
        now = datetime.now()
        ten_minutes_ago = now - timedelta(minutes=10)
        
        temp_fig.update_layout(
            title="Temperature Readings",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            legend_title="Sensor",
            template="plotly_white",
            xaxis=dict(
                range=[ten_minutes_ago, now],
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="minute", stepmode="backward"),
                        dict(count=5, label="5m", step="minute", stepmode="backward"),
                        dict(count=10, label="10m", step="minute", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )
        
        # Configure humidity graph
        humid_fig.update_layout(
            title="Humidity Readings",
            xaxis_title="Time",
            yaxis_title="Humidity (%)",
            legend_title="Sensor",
            template="plotly_white",
            xaxis=dict(
                range=[ten_minutes_ago, now],
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="minute", stepmode="backward"),
                        dict(count=5, label="5m", step="minute", stepmode="backward"),
                        dict(count=10, label="10m", step="minute", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )
        
        return temp_fig, humid_fig
    
    @app.callback(
        [Output("door-status", "children"),
         Output("audio-status", "children")],
        [Input("interval-component", "n_intervals")]
    )
    def update_status_cards(_):
        # Get latest data
        latest_data = storage.get_latest_sensor_data()
        
        # Door status card
        door_status = html.Div([
            html.Div("No door data available", className="text-center text-muted")
        ], className="border p-3 rounded")
        
        # Audio status card
        audio_status = html.Div([
            html.Div("No audio/vibration data available", className="text-center text-muted")
        ], className="border p-3 rounded")
        
        if latest_data:
            for device_id, data in latest_data.items():
                # Door status
                if "tof" in data and data["tof"] and "door_closed" in data["tof"]:
                    door_closed = data["tof"]["door_closed"]
                    color = "success" if door_closed else "danger"
                    status_text = "CLOSED" if door_closed else "OPEN"
                    
                    door_status = dbc.Card([
                        dbc.CardBody([
                            html.H4("Cabinet Door", className="card-title"),
                            html.Div([
                                dbc.Badge(status_text, color=color, className="p-2 fs-4")
                            ], className="d-flex justify-content-center")
                        ])
                    ])
                
                # Audio/vibration - for prototype just show if available
                audio_count = 0
                vibration_count = 0
                
                if device_id in storage.audio_data:
                    audio_count = len(storage.audio_data[device_id])
                
                if device_id in storage.vibration_data:
                    vibration_count = len(storage.vibration_data[device_id])
                    
                audio_status = dbc.Card([
                    dbc.CardBody([
                        html.H4("Data Samples", className="card-title"),
                        html.Div([
                            html.P([
                                html.Strong("Audio samples: "), 
                                html.Span(str(audio_count))
                            ]),
                            html.P([
                                html.Strong("Vibration samples: "), 
                                html.Span(str(vibration_count))
                            ])
                        ])
                    ])
                ])
        
        return door_status, audio_status
    
    return app