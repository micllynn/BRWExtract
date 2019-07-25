# BRWExtract #

BRWExtract is an automated tool for reading multielectrode array data from .brw (BrainWave) files. It parses the raw quantal data into voltages for each channel, reshapes into channels, and writes to an (open-source) .hdf5 file with metadata embedded.


## Prerequisites ##

BRWExtract requires h5py and numpy.


## Basic usage ##

First, place data in the /data folder within /brw_extract/. Then, the <code>run.py</code> script provides a convenient tool for extraction:
```python
import brw_extract as brex

fname = 'recording.brw'
brex.extract(fname)
```

Opening extracted .hdf5 files:
```python
>>> import h5py

>>> f = h5py.open('data/recording.h5py', 'r')
>>> f['volt'][15, 24, :] #Get voltages at channel (15, 24) at all times
>>> f['time'][:] #All times
>>> f['volt'].attrs['units'] #Fetch units for dataset 'volt'
```

## Advanced extraction params ##

Multiple parameters can be set during extraction. <code>t_intervals</code> sets the time interval of chunks which are extracted sequentially (default 1 second). <code>t_chunks</code> sets whether the chunk size in the saved hdf5 file match the extracted chunk size ('matched'); alternatively, a precise chunk size in seconds can be set. <code>compression</code> can be 'lzf' or 'gzip'; lzf is slightly faster but offers less compression.

Full params can be viewed with <code>help(brex.extract)</code>
<<<<<<< HEAD
=======
```
>>>>>>> ca4045f04818df10ed5b5040fe8752628d4c5442
