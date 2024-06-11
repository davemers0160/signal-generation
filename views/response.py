from datetime import datetime
from io import BytesIO

import matplotlib
import numpy as np
import pandas as pd
import plotly.express as px
from flask import Response, render_template, send_file
from matplotlib.figure import Figure
from numpy.typing import NDArray
from plotly_resampler import register_plotly_resampler

from signal_utils.common.binary_file_ops import get_iq_bytes

register_plotly_resampler(mode='auto')  # improves plotly scalability
matplotlib.use("agg")  # limit matplotlib to png backend

def send_bytes_response(pulse_bytes: bytes, prefix: str):
    # get current time for file naming
    now = datetime.now()
    formatted_time = now.strftime("%Y%m%d_%H%M%S")

    return send_file(
        BytesIO(pulse_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=f"{prefix}_{formatted_time}.sc16"
    )

def send_interactive_graph(pulse: NDArray[np.complex_], t: NDArray[np.float_], abbr: str):
    df = pd.DataFrame({"real": np.real(pulse), "imag": np.imag(pulse)})
    fig = px.line(df,
        x=t,
        y=df.columns,
        title=f"{abbr.upper()} Graph"
    )
    fig.update_layout(xaxis_title="Time (s)", yaxis_title="Amplitude", height=750)
    fig_html = fig.to_html()

    return render_template("graph.jinja", fig_html=fig_html, title=f"{abbr.upper()} Graph")

def send_plot_image(pulse: NDArray[np.complex_], t: NDArray[np.float_], abbr: str, axes: str):
    fig = Figure()
    ax = fig.subplots()

    if axes.lower() == "iqvt":
        ax.plot(t, np.real(pulse), label="In-phase (I)")
        ax.plot(t, np.imag(pulse), label="Quadrature (Q)", linestyle="--")
        ax.set_title(f"{abbr.upper()} Signal in Time Domain")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
    elif axes.lower() == "ivq":
        ax.plot(np.real(pulse), np.imag(pulse))
        ax.set_title(f"{abbr.upper()} In-phase vs Quadrature")
        ax.set_xlabel("In-phase (I)")
        ax.set_ylabel("Quadrature (Q)")
    else:
        return {"errors": "Invalid graph axes request"}, 400

    ax.legend()

    buf = BytesIO()
    fig.savefig(buf, format="png")

    buf.seek(0)
    return send_file(
        buf,
        mimetype="image/png"
    )

def create_three_dim_graph(pulse: NDArray[np.complex_], t: NDArray[np.float_], abbr: str):
    df = pd.DataFrame({"real": np.real(pulse), "imag": np.imag(pulse)})
    fig = px.scatter_3d(df,
                        x = df.loc[:, "real"],
                        y = df.loc[:, "imag"],
                        z = t,
                        title = "3D Representation of " + abbr.upper()
                        )
    fig.update_layout(height = 800)
    fig.update_traces(marker=dict(size=5)) #size of markers
    fig_html = fig.to_html()

    return render_template("graph.jinja", fig_html=fig_html, title=f"{abbr.upper()} Graph")

def output_cases(pulse: NDArray[np.complex_], form: str, tstop: float, abbr: str, axes: str) -> Response:
    if form == "sc16":
        pulse_bytes = get_iq_bytes(pulse)
        return send_bytes_response(pulse_bytes, abbr)

    elif form == "png":
        t = np.linspace(0, tstop, pulse.shape[0])
        return send_plot_image(pulse, t, abbr, axes)

    elif form == "graph":
        t = np.linspace(0, tstop, pulse.shape[0])
        return send_interactive_graph(pulse, t, abbr)

    elif form == "threeDim":
        t = np.linspace(0, tstop, pulse.shape[0])
        return create_three_dim_graph(pulse, t, abbr)