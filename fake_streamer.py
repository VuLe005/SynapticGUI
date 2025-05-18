import time
import numpy as np
import pandas as pd
from math import pi
from threading import Thread
from recorder import data_queue, stop_event
from main import main  # your SynapticGUI launcher

# these will accumulate all the fake data
eeg_records = []
aux_records = []
ts_records  = []

def fake_stream():
    """
    Generate a synthetic EEG (8 channels) + aux (3 channels) sine/cosine stream
    at 10 Hz, pushing into data_queue.
    """
    n_eeg = 8
    n_aux = 3
    t = 0.0
    dt = 0.1  # 10 Hz

    while not stop_event.is_set():
        # one column of data
        eeg = np.sin(np.linspace(0, 2*pi, n_eeg) + t).reshape(n_eeg, 1)
        aux = np.cos(np.linspace(0, 2*pi, n_aux) + t).reshape(n_aux, 1)
        ts  = np.array([t])

        # push to GUI queue
        data_queue.put((eeg, aux, ts))

        # record for CSV
        eeg_records.append(eeg[:,0])
        aux_records.append(aux[:,0])
        ts_records.append(t)

        t += dt
        time.sleep(dt)

    # once stop_event is set (GUI closed), save to CSV
    eeg_arr = np.vstack(eeg_records).T   # shape (8, N)
    aux_arr = np.vstack(aux_records).T   # shape (3, N)

    # EEG CSV
    df_eeg = pd.DataFrame(
        eeg_arr.T,
        columns=[f"EEG_Channel_{i}" for i in range(eeg_arr.shape[0])]
    )
    df_eeg.to_csv("fake_eeg.csv", index=False)

    # Aux CSV
    df_aux = pd.DataFrame(
        aux_arr.T,
        columns=[f"Aux_Channel_{i}" for i in range(aux_arr.shape[0])]
    )
    df_aux.to_csv("fake_aux.csv", index=False)

if __name__ == "__main__":
    stop_event.clear()
    Thread(target=fake_stream, daemon=True).start()
    main()
    stop_event.set()
    time.sleep(0.2)
    print("Fake stream ended; CSVs written: fake_eeg.csv, fake_aux.csv")