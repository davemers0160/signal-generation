import numpy as np
from flask import Blueprint, request
from marshmallow import ValidationError

import signal_utils as su
from signal_utils.common.sequences import generate_fbpsk, generate_rand_sequence
from views.form_typing import *

from .response import output_cases
from .schema import *

from signal_utils.common.generate_bpsk import generate_bpsk
from signal_utils.radar_pulse import filter_signal

wave_views = Blueprint("wave_views", __name__, url_prefix="/generate")

# generates the designated pulse where each pulse repetition interval (pri) = pulse width + zeros for the remaining space
# returns the pulse to be displayed by output_cases
@wave_views.route("/cw", methods=["GET"])
def get_cw(data, form, view):
    schema = CWSchema()

    try:
        data["form"] = form 
        data["axes"] = '' #dummy param
        data = schema.dump(data)
        convert_cw_types(data)
        pulse = su.continuous_wave.generate_cw(data["sample_rate"], data["pw"])
        pulse = get_pulse_blanks(pulse, 1, data["amplitude"], data["signal_length"], data["sample_rate"], data["pw"], "cw")

        pulse = np.round(data["amplitude"] * pulse)
        return output_cases(pulse, data["form"], data["signal_length"], "CW", data["axes"], 1, view)

    except ValidationError as err:
        return {"errors": err.messages}, 400


@wave_views.route("/lfm", methods=["GET"])
def get_lfm(data, form, view):
    schema = LFMSchema()
    try:
        data["form"] = form 
        data["axes"] = '' #dummy param
        data = schema.dump(data)
        convert_lfm_types(data)
        pulse = su.linear_frequency_modulated.generate_lfm(data["sample_rate"], data["fstart"], data['fstop'], data["pw"], data["num_pulses"])
        pulse = get_pulse_blanks(pulse, data["num_pulses"], data["amplitude"], data["pri"], data["sample_rate"],  data["pw"], "lfm")
        pulse = np.tile(pulse, data["num_pulses"])

        pulse = np.round(data["amplitude"] * pulse)
        return output_cases(pulse, data["form"], data["pri"], "lfm", data["axes"], data["num_pulses"], view)
    except ValidationError as err:
        return {"errors": err.messages}, 400  

#For each pulse, create a filtered bpsk with a randomly generated sequence
@wave_views.route("/bpsk", methods=["GET"])
def get_bpsk(data, form, view):
    schema = BPSKSchema()
    try:
        data["form"] = form 
        data["axes"] = '' #dummy param
        #data = schema.dump(data)
        convert_bpsk_types(data)
        final_pulse = np.empty(0)
        # num_bit = data["num_bits"]

        for __ in range(data["num_pulses"]):
            seq = generate_rand_sequence(data["seq_type"], data["num_bits"])

            # single_pulse = generate_fbpsk(data["cutoff_freq"], data["num_taps"], num_bit, data["sample_rate"], data["bit_length"], data["seq_type"], data["pulse_reps"], data["num_pulses"])
            single_pulse = generate_bpsk(seq, data["sample_rate"], data["bit_length"])
            single_pulse = get_pulse_blanks(single_pulse, data["num_pulses"], data["amplitude"], data["pulse_reps"], data["sample_rate"], 1, "bpsk")
            final_pulse = np.append(final_pulse,single_pulse)

        filtered_pulse = filter_signal(final_pulse, data["cutoff_freq"], data["num_taps"], data["sample_rate"])
        filtered_pulse = np.round(data["amplitude"] * filtered_pulse)
        return output_cases(filtered_pulse, data["form"], data["pulse_reps"], "bpsk", data["axes"], data["num_pulses"], view)

    except ValidationError as err:
        return {"errors": err.messages}, 400


#Returns the pulse with blanks spaces according
def get_pulse_blanks(pulse, num_pulses, amplitude, pri, sample_rate, pulse_width, wave_type):
    # pulse = np.round(amplitude * pulse)
    if wave_type == "cw":
        samples_per_pulse = round(pulse_width * sample_rate)
        samples_per_pri = round(pri*sample_rate)
        buffer_samples = np.zeros(max(0, int(samples_per_pri-samples_per_pulse))) #append this many 0s to get pri = pw + len(0s)
    elif wave_type == "lfm":
        samples_per_pulse = round(pulse_width*sample_rate)
        samples_per_pri = round(pri*sample_rate)
        buffer_samples = np.zeros(max(0, int(samples_per_pri-samples_per_pulse)))
    elif wave_type == "bpsk":
        samples_per_pulse = len(pulse) #get the length of a filtered pulse
        samples_per_pri = pri*sample_rate 
        buffer_samples = np.zeros(max(0, int(samples_per_pri-samples_per_pulse)))
    pulse = np.append(pulse, buffer_samples) #add the zeros onto the pulse

    return pulse
