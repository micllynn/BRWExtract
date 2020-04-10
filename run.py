import brw_extract as brex

file_path = '/Volumes/Backup 5TB EVG/Brw data files/20191030 - OPTO'
fname = 'Slice1_Prot2_Baseline.brw'
file_path_output = '/Volumes/SSD data'

brex.extract(fname, file_path, file_path_output, t_intervals = 1, compression = 'lzf', t_chunks = True)




##

