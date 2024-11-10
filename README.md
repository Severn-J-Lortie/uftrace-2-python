# uftrace-2-python
Example repo showing how to use uftrace output in Python

## Requirements
- uftrace
- Python
- elfutils

## Getting started

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

