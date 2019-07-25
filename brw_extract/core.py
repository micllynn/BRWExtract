import os, sys, io, datetime

import h5py
import numpy as np

import cProfile, pstats, time
import multiprocessing as mp

def extract(fname, t_intervals = 1, t_chunks = 'matched',
    compression = 'lzf', _profile = False, _verbosity = True):
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

        levels_to_v_add = - 1 * levels/2
        levels_to_v_mult = inversion * (v_max - v_min) / levels

        #Store simple data (not voltage)
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

        ##################
        #Extract the brw voltage trace and place it in an .hdf5 dataset
        ##################
        dset_raw = _rec['3BData/Raw']

        chunk_size_t = np.argmin(np.abs(time_array - t_intervals))
        chunk_size = int(chunk_size_t * n_ch_x * n_ch_y)
        chunk_bookends = np.append(np.arange(0, len(dset_raw),
            chunk_size), len(dset_raw))

        print(f'-----\nFile: {fname_path}')
        print('\r\t' + 'Extracting BRW... 0.0%', end = '')

        _start_t = 0
        for ind, _start in enumerate(chunk_bookends[:-1]):
            _timer_start = time.time()

            #Define end time and reshaped t for this iteration
            _end = int(chunk_bookends[ind+1])
            _chunk_size_t = int((_end - _start) / (n_ch_x * n_ch_y))

            #**Store _v and process. 1. reshape into correct (t, x, y) dims.
            #2. Change axis order from (t, x, y) to (x, y, t), necessitating
            #two .swapaxes calls. More memory-efficient to do all at once.
            _v = np.array(dset_raw[_start : _end],
                dtype = 'float').reshape(_chunk_size_t, n_ch_x, n_ch_y) \
                .swapaxes(0, 2).swapaxes(0, 1)

            dset_volt[:, :, _start_t : _start_t + _chunk_size_t] = \
                (_v + levels_to_v_add) * levels_to_v_mult

            _start_t += _chunk_size_t #Update start vars

            #Print progress
            _t_step = (time.time() - _timer_start)

            progress = (ind+1)/len(chunk_bookends)*100
            curr_t_est_raw = _t_step * (len(chunk_bookends)-(ind+1))
            curr_t_est_fmat = str(datetime.timedelta(seconds=curr_t_est_raw))
            curr_t_est = curr_t_est_fmat[0:1] + 'h:' + curr_t_est_fmat[2:4] + \
                'm:' + curr_t_est_fmat[5:7] + 's'


            _pr = '\r\t' + f'Extracting... {progress:.1f}%' \
                + f'  |  Time remaining... ' + curr_t_est
            print(_pr, end = '')

        _pr_end = '\r\t** Extracted.' + ' ' * len(_pr)
        print(_pr_end)

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

    In progress - does not offer any real speedup versus extract().

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
