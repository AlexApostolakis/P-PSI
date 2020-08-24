# P-PSI

Software for running ISCE topsStack and StaMPS steps parallelized on multicore environment\
_by National Observatory of Athens - Beyond team_ http://www.beyond-eocenter.eu/

### Installation

* Make sure that python 2 is available on your system (version 2.7.13 or later)
* ISCE 2 and StaMPS have to be installed and their configurations enabled in your environment (https://github.com/isce-framework/isce2, https://github.com/dbekaert/StaMPS)
* Copy or clone this repository's files and add the P-PSI/ISCE, P-PSI/StaMPS directory paths to your environment's PATH
* Install matlab engine for python 2 : https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

### Run

* __start topstack ISCE command 5 "pairs misreg" parallelized.__\
usage: start_pairs_misreg.py [-h] [-d WORKDIR] [-cpu MAXCPU] [-pq PREREQ]\
optional arguments:\
-h, --help  show this help message and exit\
-d WORKDIR, --workdir WORKDIR  Working directory. If not given it assumes   current directory.\
-cpu MAXCPU, --maxcpu MAXCPU maximum CPU number to use. If not given all available CPUs will be used.\
-pq PREREQ, --prereq PREREQ Activate prerequisite n: no, nsp: not same pairs. Default n\
_Example:_\
python start_pairs_misreg.py -d . -cpu 4

* __start ISCE topstack command 7 "geo2rdr_resample" parallelized.__\
usage: start_parallel.py [-h] [-f RUNFILE] [-rx REGEX] [-d WORKDIR] [-cpu MAXCPU] [-cmd COMMAND]\
optional arguments:\
-h, --help            show this help message and exit\
-f RUNFILE, --runfile RUNFILE Run commands file\
-rx REGEX, --regex REGEX Regex expression to determine a unique key for each\
command from the command file. If not given it will assign as key the row number of the command in the file to each command\
-d WORKDIR, --workdir WORKDIR Working directory. If not given it assumes current directory.\
-cpu MAXCPU, --maxcpu MAXCPU Maximum CPU number to use. If not given all available CPUs will be used.\
-cmd COMMAND, --command COMMAND Commands description name. Default: command\
_Example:_\
python start_parallel.py -d . -f run_7_geo2rdr_resample -rx "(?<=resamp_).*$" -cmd resamples

* __start StaMPS mt_prep_isce parallelized.__\
usage: mt_prep da_thresh [rg_patches az_patches rg_overlap az_overlap]\
da_thresh = (delta) amplitude dispersion typical values: 0.4 for PS, 0.6 for SB\
rg_patches (default 1)   = number of patches in range\
az_patches (default 1)   = number of patches in azimuth\
rg_overlap (default 50)  = overlapping pixels between patches in range\
az_overlap (default 50) = overlapping pixels between patches in azimuth\
**maxcpu (default 0) = maximum CPU number to utilize. 0 means all available CPUs**\
*Example:*\
mt_prep_isce_par 0.4 3 3 50 50 0

* __start StaMPS steps 1-5 parallelized.__\
usage: ps_run.py [-h] [-p PAR] [-a5 AGGR5B] [-a AGGR] [-cpu CPUNUMBER] [-pl] [-o OPTIMIZATION] [-d WORKINGDIR]\
optional arguments:\
-h, --help show this help message and exit\
-p PAR, --par PAR range n-m specifies which ps steps from 1 to 5 will run in paralllel. eg 1-2 will run steps 1,2 , with 0-0 no step runs (default: 0-0)\
-a5 AGGR5B, --aggr5b AGGR5B specifies run of aggregation step 5b : y for run n for not run (default: n)\
-a AGGR, --aggr AGGR  range n-m specifies which ps steps will run after
aggregation of PATCHES, from 6 to 8 eg 6-6 will run
step 6 only, with 0-0 no step runs (default: 0-0)\
-cpu CPUNUMBER, --cpunumber CPUNUMBER maximum CPU number to use\
-pl, --plist Create patch lists only\
-o OPTIMIZATION, --optimization OPTIMIZATION patch list optimization method: 'ps' for number of
candidates, 'patch' for number of patches. Default 'ps'\
-d WORKINGDIR, --workingdir WORKINGDIR working directory\
*Example:*\
python ps_run.py -p 1-5 -a5 y -a 6-8

**In the examples above "python" is referring to the python executable for python 2**

### Contact
alex.apostolakis@noa.gr
