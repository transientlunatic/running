python_version=3.11.4
zlib_version=1.3.1
python_version_short=${python_version%.*}
echo python_version: $python_version
echo python_version_short: $python_version_short
# Create source directory
mkdir ~/src
cd ~/src
# Download and extract zlib source code
wget https://zlib.net/zlib-${zlib_version}.tar.gz
tar xzvf zlib-${zlib_version}.tar.gz
cd zlib-${zlib_version}

 ./configure --prefix=$HOME/local 

 make && make install

# Download and extract Python source code
wget --no-check-certificate https://www.python.org/ftp/python/${python_version}/Python-${python_version}.tgz
tar zxvf Python-${python_version}.tgz 
cd ~/src/Python-${python_version}

./configure --prefix=$HOME/opt/python${python_version_short} \
    CPPFLAGS="-I$HOME/local/include" \
    LDFLAGS="-L$HOME/local/lib" \
    --enable-optimizations

sed -i 's/-j0/-j6/g' Makefile*

make
make install