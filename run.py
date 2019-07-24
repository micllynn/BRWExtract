import brw_extract as brex
import matplotlib.pyplot as plt

brex.extract('Slice3_Baseline.brw', compression = 'lzf')

#%%
import h5py
import matplotlib.pyplot as plt
import scipy.signal as sp_sig

file = 'data/Slice3_Baseline.hdf5'
f = h5py.File(file, 'r')

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.plot(f['volt'][0, 0, 0:4096*2])


f['volt'][0, 0, 0]
f['volt'][0, 0, 4096]
