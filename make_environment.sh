#!/bin/bash
set -e

python_version=3.11.4
zlib_version=1.3.1
python_version_short=${python_version%.*}
echo python_version: $python_version
echo python_version_short: $python_version_short

# Create source directory
mkdir -p ~/src
cd ~/src

# Download and extract zlib source code
wget https://zlib.net/zlib-${zlib_version}.tar.gz
tar xzvf zlib-${zlib_version}.tar.gz
cd zlib-${zlib_version}

./configure --prefix=$HOME/local 

make && make install

# Download and extract Python source code
wget https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz
tar zxvf Python-${python_version}.tgz 
cd ~/src/Python-${python_version}

./configure --prefix=$HOME/opt/python${python_version_short} \
    CPPFLAGS="-I$HOME/local/include" \
    LDFLAGS="-L$HOME/local/lib" \
    --enable-optimizations

for f in Makefile*; do
    [ -f "$f" ] || continue
    sed -i.bak 's/-j0/-j6/g' "$f"
    rm -f "$f.bak"
done

make
make install