import os, sys, io

import h5py
import numpy as np

import cProfile, pstats, time
import multiprocessing as mp

def extract(fname, t_intervals = 1, t_chunks = 'matched',
    compression = None, _profile = False, _verbosity = True):
    '''
    Extracts a BrainWave file from quantal data and stores in a chunked HDF5 file.

    Parameters
    ----
    fname : str
        The name of the file to load. By default, the new file is stored as this
        filename as well, but with a .hdf5 extension.
    t_intervals : float    (default 1), optional
        Intervals to partition the recording into. The recording will be
        extracted interval by interval (reshaping and converting to voltage).
        Higher values may lead to performance penalties.
    t_chunks : int, 'matched' or False, optional
        If int, data is chunked in slabs of (n_ch, n_ch, t_chunks). If
        'matched', data is chunked in slabs of (n_ch, n_ch, t_intervals). If
        False, data is not chunked.
    compression : str, 'gzip' or 'lzf' or None
    compression_level :
    _profile : boolean, optional
        Whether to enable cProfiling within the function for performance
        optimization. If True, returns a pstats.Stats object containing stats.
    _verbosity : boolean, optional
        Sets verbosity level of extraction.


    Usage
    ----
    #Extract the file
    >> extract('recording.brw')

    #Open the new hdf5 file as a recording
    >> rec = h5py.File('recording.hdf5', 'r')
    >> rec['volt'][0, 0, :] #Retrieve electrode[0, 0]'s voltage waveform
        #through time
    >> rec['time'][:] #Retrieve vector of all sample times in seconds.

    '''
    #Pre-run initialization
    if _profile is True:
        pr = cProfile.Profile()
        pr.enable()

    if t_chunks is 'matched':
        t_chunks = t_intervals

    #Check fpath and sys
    cwd = os.getcwd()

    #OS test
    platform = sys.platform
    if platform is 'darwin' or 'linux':
        fname_path = cwd + '/data/' + fname
    elif platform is 'win32' or 'win64':
        fname_path = cwd + '\\data\\' + fname


    new_fname_path = fname_path[0:-4] + '.hdf5'

    #Load data and create hdf5 to store processed data
    with h5py.File(fname_path,'r') as _rec, h5py.File(new_fname_path, 'w') as rec:

        #Extract recording parameters from the HDF5
        n_frames = _rec['3BRecInfo/3BRecVars/NRecFrames'][0]
        n_ch_x = _rec['3BRecInfo/3BMeaChip/NRows'][0]
        n_ch_y = _rec['3BRecInfo/3BMeaChip/NCols'][0]
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
        if t_chunks is not False:
            dset_volt = rec.create_dataset('volt', (n_ch_x, n_ch_y, n_frames),
                dtype = 'float32', chunks = (n_ch_x, n_ch_y, t_chunks),
                compression = compression)
        else:
            dset_volt = rec.create_dataset('volt', (n_ch_x, n_ch_y, n_frames),
                dtype = 'float32', chunks = False, compression = compression)

        dset_volt.attrs['units'] = 'uV'
        dset_volt.attrs['sampling rate'] = freq_sample
        dset_volt.attrs['dim0'] = 'Electrode num. in x dimension'
        dset_volt.attrs['dim1'] = 'Electrode num. in y dimension'
        dset_volt.attrs['dim2'] = 'Time index'

        time_array = np.arange(0, dt*n_frames, dt)
        dset_t = rec.create_dataset('time', (n_frames,), data = time_array)
        dset_t.attrs['units'] = 'seconds'
        dset_t.attrs['sampling rate'] = freq_sample

        ###
        t_start = np.arange(0, dt*n_frames, t_intervals)

        dset_raw = _rec['3BData/Raw']

        print(f'-----\nFile: {fname_path}')
        print('\r\t' + 'Extracting BRW... 0.0%', end = '')

        _timer0 = time.time()

        for ind, _t_start in enumerate(t_start):
            #Define start and end of times for this iteration
            if ind == len(t_start) - 1:
                _t_end = dt*n_frames
            else:
                _t_end = t_start[ind + 1]

            #Convert to indices
            _ind_start = int(_t_start * freq_sample) * n_ch_x*n_ch_y
            _ind_end = int(_t_end * freq_sample) * n_ch_x*n_ch_y

            _ind_t_start = int(_t_start * freq_sample)
            _ind_t_end = int(_t_end * freq_sample)
            _n_t = _ind_t_end - _ind_t_start

            #Store _v and process
            _v = np.array(dset_raw[_ind_start : _ind_end],
                dtype = 'float').reshape(n_ch_x, n_ch_y, _n_t)
            _to_add = - 1 * levels/2
            _to_mult = inversion * (v_max - v_min) / levels

            dset_volt.write_direct((_v + _to_add) * _to_mult,
                dest_sel=(np.s_[:, :, _ind_t_start : _ind_t_end]))

            #Print progress
            _timer = time.time()
            _t_step = (_timer - _timer0)

            progress = (ind+1)/len(t_start)*100
            curr_t_est = _t_step * (len(t_start)-(ind+1))
            print('\r\t' + f'Extracting... {progress:.1f}%' \
                + f'  |  Time remaining... {curr_t_est:.1f}s   ', end = '')

        print('\n\tExtracted.')

        if _profile is True:
            pr.disable()

            s = io.StringIO()
            ps = pstats.Stats(pr, stream = s).sort_stats('cumulative')
            ps.print_stats()
            print(s.getvalue())

            return ps

        else:
            return

def mp_extract(files, timeit = False, **kwargs):
    """Function which is a multiprocessing wrapper for extract() and takes all
    kwargs associated with that function.

    Parameters
    ---------
    files : list
        A list of filename strings to extract.
    **kwargs : dict
        A dictionary of kwargs to pass to extract().

    Returns
    --------
    """
    if timeit is True:
        t_start = time.time()

    n_cores = mp.cpu_count()
    n_files = len(files)

    print(f'Extracting {n_files} files on {n_cores} cores... ')

    #Start jobs
    jobs = []
    for ind in range(n_files):
        jobs.append(mp.Process(target = extract, args = (files[ind],),
            kwargs = kwargs))
        jobs[ind].start()

    #Wait for all jobs to end
    for ind in range(n_files):
        jobs[ind].join()

    if timeit is True:
        t_end = time.time()
        t_tot = t_end - t_start
        print('time elapsed: ' + str(t_tot) + 's')
