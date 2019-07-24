# BRWExtract #

BRWExtract is an automated tool for reading proprietary .brw (BrainWave) files storing multielectrode array data, parsing the data into voltages for each channel, and writing to an (open-source) .hdf5 file.


## Prerequisites ##

BRWExtract requires h5py and numpy.


## Basic usage ##

First, place any data in the /data folder within brw_extract. Then, individual files can be extracted like so:
```python
import brw_extract as brex

fname = 'recording.brw'
brex.extract(fname)
```

Opening extracted .hdf5 files:
```python
import h5py

fname = 'data/recording.h5py'
h5py.open(fname)
```


## Parameter tuning ##

By default,
