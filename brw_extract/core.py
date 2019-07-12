import h5py
import numpy as np


def extract(fname, n_ch = 4096, time_intervals = 1):
    '''
    Extracts a BrainWave file from quantal data and stores in a chunked HDF5 file.

    Parameters
    ----
    fname : str
        The name of the file to load. By default, the new file is stored as this
        filename as well, but with a .hdf5 extension.

    n_ch : int    (default 4096)
        The number of channels. Must be a squared integer value.

    time_intervals : float    (default 1)
        Intervals to partition the recording into. The recording will be
        extracted interval by interval (reshaping and converting to voltage).
        Higher values may lead to performance penalties.

    Usage
    ----
    #Extract the file
    >> extract('recording.brw')

    #Open the new hdf5 file as a recording
    >> rec = h5py.File('recording.hdf5', 'r')
    >> rec['volt'][0, 0, :] #Retrieve electrode[0, 0]'s voltage waveform
        #through time
    >> rec['time'][5] #Retrieve time, in seconds, at index 5.

    '''
    new_fname = fname[0:-4] + '.hdf5'
    n_ch = int(n_ch)

    #Load data and create hdf5 to store processed data
    _rec = h5py.File(fname,'r')
    rec = h5py.File(new_fname, 'w')

    #Extract recording parameters from the HDF5
    n_frames = _rec['3BRecInfo/3BRecVars/NRecFrames'][0]
    n_ch_1d = np.sqrt(n_ch).astype(np.int)
    n_xyt = len(_rec['3BData/Raw'])

    freq_sample = _rec['3BRecInfo/3BRecVars/SamplingRate'][0]
    dt = 1/freq_sample

    #For converting binary representation into voltage:
    inversion = _rec['3BRecInfo/3BRecVars/SignalInversion']
    v_max = _rec['3BRecInfo/3BRecVars/MaxVolt'][0]
    v_min = _rec['3BRecInfo/3BRecVars/MinVolt'][0]

    n_bits = _rec['3BRecInfo/3BRecVars/BitDepth'][0]
    levels = 2**n_bits

    #Store some data
    dset_volt = rec.create_dataset('volt', (n_ch_1d, n_ch_1d, n_frames),
        dtype = 'f', chunks = True, compression="gzip")
    dset_volt.attrs['units'] = 'uV'
    dset_volt.attrs['dim1'] = 'Electrode in x dimension'
    dset_volt.attrs['dim2'] = 'Electrode in y dimension'
    dset_volt.attrs['dim3'] = 'Time'


    time = np.arange(0, dt*n_frames, dt)
    dset_t = rec.create_dataset('time', (n_frames,), data = time)
    dset_t.attrs['units'] = 'seconds'

    ###
    t_start = np.arange(0, dt*n_frames, time_intervals)

    for ind, _t_start in enumerate(t_start):
        #Define start and end of times for this iteration
        if ind == len(t_start) - 1:
            _t_end = dt*n_frames
        else:
            _t_end = t_start[ind + 1]

        #Convert to indices
        _ind_start = int(_t_start * freq_sample) * n_ch
        _ind_end = int(_t_end * freq_sample) * n_ch

        _ind_t_start = int(_t_start * freq_sample)
        _ind_t_end = int(_t_end * freq_sample)
        _n_t = _ind_t_end - _ind_t_start

        #Store _v and process
        _v = np.array(_rec['3BData/Raw'][_ind_start : _ind_end]).reshape(
            n_ch_1d, n_ch_1d, _n_t)
        rec['volt'][:, :, _ind_t_start : _ind_t_end] = \
            (_v * inversion - levels/2) * (v_max - v_min) / levels

        #Print progress
        progress = ind/len(t_start)*100
        print('\r' + f'Extracting BRW... {progress:.1f}'
            + '%', end = '')

    return
