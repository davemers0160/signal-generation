import numpy as np
from flask import Blueprint, request
from marshmallow import ValidationError

import signal_utils as su
from signal_utils.common.sequences import maximal_length_sequence, random_tap_sequence
from signal_utils.common.generate_bpsk import generate_bpsk

from .response import output_cases
from .schema import *

wave_views = Blueprint("wave_views", __name__, url_prefix="/generate")

@wave_views.route("/cw", methods=["GET"])
def get_cw():
    schema = CWSchema()

    try:
        data = schema.load(request.args)
        pulse = su.continuous_wave.generate_cw(data["sample_rate"], data["signal_length"])

        return output_cases(pulse, data["form"], data["signal_length"], "CW")

    except ValidationError as err:
        return {"errors": err.messages}, 400

@wave_views.route("/radar", methods=["GET"])
def get_radar():
    schema = RadarSchema()

    try:
        data = schema.load(request.args)
        taps = random_tap_sequence(data["num_bits"])
        seq = maximal_length_sequence(data["num_bits"], np.array(taps))
        pulse = su.radar_pulse.generate_pulse(seq, data["sample_rate"], data["bit_length"], data["pri"], data["num_pulses"])
        pulse = np.round(data["amplitude"] * pulse)

        return output_cases(pulse, data["form"], data["bit_length"], "PW")

    except ValidationError as err:
        return {"errors": err.messages}, 400

@wave_views.route("/lfm", methods=["GET"])
def get_lfm():
    schema = LFMSchema()

    try:
        data = schema.load(request.args)
        pulse = su.linear_frequency_modulated.generate_lfm(data["sample_rate"], data["fstart"], data['fstop'], data["signal_length"])

        return output_cases(pulse, data["form"], data["signal_length"], "lfm")

    except ValidationError as err:
        return {"errors": err.messages}, 400

@wave_views.route("/bpsk", methods=["GET"])
def get_bpsk():
    schema = BPSKSchema()

    try:
        data = schema.load(request.args)
        taps = random_tap_sequence(data["num_bits"])
        seq = maximal_length_sequence(data["num_bits"], np.array(taps))
        pulse = generate_bpsk(seq, data["sample_rate"], data["bit_length"])

        #print("Data form information:" + data["form"])
        return output_cases(pulse, data["form"], data["bit_length"], "bpsk") #gives the different options for graph generation
        

    except ValidationError as err:
        return {"errors": err.messages}, 400
