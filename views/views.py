import numpy as np
from flask import Blueprint, request
from marshmallow import ValidationError

import signal_utils as su
from signal_utils.common.sequences import generate_fbpsk

from .response import output_cases
from .schema import *

wave_views = Blueprint("wave_views", __name__, url_prefix="/generate")

@wave_views.route("/cw", methods=["GET"])
def get_cw():
    schema = CWSchema()

    try:
        data = schema.load(request.args)
        pulse = su.continuous_wave.generate_cw(data["sample_rate"], data["signal_length"])
        pulse = np.round(data["amplitude"] * pulse)

        return output_cases(pulse, data["form"], data["signal_length"], "CW", data["axes"], 4) #1 is temp num_pulses count

    except ValidationError as err:
        return {"errors": err.messages}, 400

@wave_views.route("/lfm", methods=["GET"])
def get_lfm():
    schema = LFMSchema()

    try:
        data = schema.load(request.args)
        pulse = su.linear_frequency_modulated.generate_lfm(data["sample_rate"], data["fstart"], data['fstop'], data["pri"], data["num_pulses"])
        pulse = np.round(data["amplitude"] * pulse)
        pulse = np.append(pulse, np.zeros(len(pulse)))
        pulse = np.tile(pulse, data["num_pulses"])

        return output_cases(pulse, data["form"], data["pri"], "lfm", data["axes"], data["num_pulses"])

    except ValidationError as err:
        return {"errors": err.messages}, 400

@wave_views.route("/bpsk", methods=["GET"])
def get_bpsk():
    schema = BPSKSchema()
    try:
        data = schema.load(request.args)

        pri = data["bit_length"] * (2**(data["num_bits"]-1))
        pulse = generate_fbpsk(data["cutoff_freq"], data["num_taps"],data["num_bits"], data["sample_rate"], data["bit_length"], data["sequence_type"], pri, data["num_pulses"])
        pulse = np.round(data["amplitude"] * pulse)

        return output_cases(pulse, data["form"], data["bit_length"], "bpsk", data["axes"], data["num_pulses"])

    except ValidationError as err:
        return {"errors": err.messages}, 400
