import glob, sys, time, serial, os
import pandas as pd
import numpy as np

from serial import Serial as PySerial
from threading import Thread, Event
from queue import Queue
# from psychopy.hardware import keyboard  # if you’re using PsychoPy for escape

from brainflow.board_shim import BoardShim, BrainFlowInputParams

# ─── Shared queue for GUI ───────────────────────────────────────
data_queue = Queue()

lsl_out       = False
save_dir      = 'data'
run           = 111
save_file_aux = os.path.join(save_dir, f'aux_run-{run}.npy')
save_file_eeg = os.path.join(save_dir, f'eeg_run-{run}.npy')
sampling_rate = 250
CYTON_BOARD_ID = 0
BAUD_RATE     = 115200
ANALOGUE_MODE = '/2'

# Used to signal stop from GUI
stop_event = Event()


def find_openbci_port():
    """Finds the port to which the Cyton Dongle is connected."""
    if sys.platform.startswith('win'):
        ports = [f'COM{i+1}' for i in range(256)]
    elif sys.platform.startswith(('linux', 'cygwin')):
        ports = glob.glob('/dev/ttyUSB*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/cu.usbserial*')
    else:
        raise EnvironmentError('Unsupported OS for serial scan')
    openbci_port = ''
    for port in ports:
        try:
            s = PySerial(port=port, baudrate=BAUD_RATE, timeout=1)
            s.write(b'v')
            time.sleep(1)
            resp = s.read_all().decode(errors='ignore')
            s.close()
            if 'OpenBCI' in resp:
                openbci_port = port
                break
        except Exception:
            continue
    if not openbci_port:
        raise OSError('Cannot find OpenBCI port.')
    return openbci_port


def run_brainflow():
    """Acquire data until stop_event is set, pushing into data_queue."""
    os.makedirs(save_dir, exist_ok=True)

    print(BoardShim.get_board_descr(CYTON_BOARD_ID))
    params = BrainFlowInputParams()
    if CYTON_BOARD_ID != 6:
        params.serial_port = find_openbci_port()
    else:
        params.ip_port = 9000

    board = BoardShim(CYTON_BOARD_ID, params)
    board.prepare_session()
    board.config_board('/0')
    board.config_board('//')
    board.config_board(ANALOGUE_MODE)
    board.start_stream(45000)

    def _acquire(q: Queue):
        while not stop_event.is_set():
            data = board.get_board_data()
            ts  = data[board.get_timestamp_channel(CYTON_BOARD_ID)]
            eeg = data[board.get_eeg_channels(CYTON_BOARD_ID)]
            aux = data[board.get_analog_channels(CYTON_BOARD_ID)]
            if ts.size:
                # push into the shared queue for GUI
                data_queue.put((eeg, aux, ts))
            time.sleep(0.1)

    Thread(target=_acquire, args=(data_queue,), daemon=True).start()

    # accumulate into arrays until stop
    eeg_data = np.zeros((len(board.get_eeg_channels(CYTON_BOARD_ID)), 0))
    aux_data = np.zeros((len(board.get_analog_channels(CYTON_BOARD_ID)), 0))
    # kb = keyboard.Keyboard()  # if you want PsychoPy ESC handling

    while not stop_event.is_set():
        time.sleep(0.1)
        # optional: check for ESC if using keyboard
        # if 'escape' in kb.getKeys():
        #     stop_event.set()
        #     break

    # teardown
    board.stop_stream()
    board.release_session()

    # save raw numpy
    np.save(save_file_aux, aux_data)
    np.save(save_file_eeg, eeg_data)

    # save CSV
    df_aux = pd.DataFrame(aux_data.T,
                          columns=[f'Aux_{i}' for i in range(aux_data.shape[0])])
    df_aux.to_csv(os.path.join(save_dir, f'aux_run-{run}.csv'), index=False)

    df_eeg = pd.DataFrame(eeg_data.T,
                          columns=[f'EEG_{i}' for i in range(eeg_data.shape[0])])
    df_eeg.to_csv(os.path.join(save_dir, f'eeg_run-{run}.csv'), index=False)


if __name__ == "__main__":
    run_brainflow()