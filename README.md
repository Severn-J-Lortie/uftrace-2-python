# uftrace-2-python
Example repo showing how to use uftrace output in Python

## Requirements
- uftrace
- Python
- elfutils

## Testing data
Please store all testing data in the [team Sharepoint](https://queensuca.sharepoint.com/:f:/r/teams/GROUP-ELEC490498Group1/Shared%20Documents/General/Quicksilver%20Data?csf=1&web=1&e=kTx4b5).

## Visualizing test data

### Flamegraph

To see a flamegraph of the run, use the following command:
```
python generate-flamegraph.py --data-dir=<directory of run> --cpu=<CPUs to view> --fields=<fields to view>
```

To view energy and time stats of an aggregate run (the .gzip files `./trace-qs.sh` generates) run:
```
python get-stats.py --dir=<data directory of run>
```
You can also view a side-by-side comparision chart between two runs using:
```
python get-stats.py --compare <directory of run 1> <directory of run 2>
```
The above command will output a file `run-comparison.png` which shows the comparison.


## Compiling Uftrace

### Normal environments
You should be able to build uftrace following the instructions in their repositiory just fine.
The `misc/install-deps.sh` will get all dependencies.

### CAC
For the CAC, we cannot install dependencies with a package manager. We will need to build `elfutils` from source.

**Steps:**

To build elfutils:
1. Run `module avail python` to see which versions of Python are available. Note down the latest one.

2. Run `module load python/3.x.x` where `3.x.x` is the latest version.

3. `wget https://sourceware.org/elfutils/ftp/elfutils-latest.tar.bz2` to download the latest source.

4. `tar -xjf elfutils-latest.tar.bz2`

5. `cd elfutils-latest`

6. `./configure --prefix=$HOME/local --disable-debuginfod --enable-debuginfod=dummy`

7. `make`

8. `make install`

Now that elfutils is setup, we need to get uftrace and point it at our local installation:

1. `git clone git@github.com:namhyung/uftrace.git`
2. `cd uftrace`
3. Tell the compiler to use our local elfutils:
    ```
    export LD_LIBRARY_PATH=$HOME/local/lib:$LD_LIBRARY_PATH
    export CPATH=$HOME/local/include:$CPATH
    export LIBRARY_PATH=$HOME/local/lib:$LIBRARY_PATH
    export PKG_CONFIG_PATH=$HOME/local/lib/pkgconfig:$PKG_CONFIG_PATH
    ```
4.  Run the configure script and point it at the local include and lib directories:

    ```
    ./configure --prefix=$HOME/uftrace CPPFLAGS="-I$HOME/local/include" LDFLAGS="-L$HOME/local/lib"
    ```
5. `make`

6. `make install`

If all went well, you should be able to run this command:
`$HOME/uftrace/bin/uftrace --version` and the version information will be displayed. If you want you can add the uftrace/bin directory to your $PATH variable for ease of use:
`echo 'export PATH="$PATH:$HOME/uftrace/bin"' >> ~/.bashrc && source ~/.bashrc`. So now you can just use `uftrace` to invoke it.

## Running Tests
### Local
Simply run `./trace-qs.sh`. This is a bash script which will run Quicksilver 3 times and record the trace output into the ./data directory. The output will be in a GZIP file named with the current date and time. Each run is in its own folder.
### CAC

**sudo:** turbostat will require `sudo` to run. So, if you're going to queue this bash script up with `srun`, make sure that you modify the initial line: `sudo echo` to something like `echo "your_password" | sudo -S echo`.

**Quicksilver concerns:**
The CAC is tricker because you have to make sure that Quicksilver is compiled without OpenMPI enabled. For a long chain of reasons I won't get into now, you cannot run OpenMPI stuff on the CAC. So, just modify the Makefile in your Quicksilver repo to look like:
```
###############################################################################
### GCC -- with MPI and OpenMP
###############################################################################
# GCC -- without MPI, but with OpenMP
OPENMP_FLAGS = -DHAVE_OPENMP -fopenmp
OPENMP_LDFLAGS = -fopenmp
# Remove MPI_FLAGS since we are not using MPI:
# MPI_FLAGS = -DHAVE_MPI
OPTFLAGS = -O2 -pg

# Use a standard C++ compiler
CXX = g++
CXXFLAGS = -std=c++11 $(OPTFLAGS) -Wpedantic
# Exclude MPI_FLAGS from CPPFLAGS:
CPPFLAGS = $(OPENMP_FLAGS)
LDFLAGS = $(OPENMP_LDFLAGS)

```
and then `make clean && make` to recompile. From the on out it should work.

## Live Data
To start the turbostat recorder for InfluxDB, use 
```
python turbostat-influx.py <run_id>
```
where **run_id** is the associated run_id that Quicksilver data reporting will use
