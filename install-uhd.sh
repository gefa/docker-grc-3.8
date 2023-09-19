#!/bin/sh

# This script configures/builds/installs gnuradio from source
# After building, it deletes the build directory to keep image size small(ish)

set -e
set -x
UHD_COMMIT=UHD-3.15.LTS # for some reason this is not picked up from Dockerfile
# Initialize
git clone https://github.com/ettusresearch/uhd.git -b ${UHD_COMMIT} --depth 1

# Print git configuration
cd uhd
git status
git log

# Make build directory and enter
cd host
mkdir build
cd build

# Configure cmake
cmake ../ \
    -DCMAKE_BUILD_TYPE=Debug \
    -DENABLE_B200=${UHD_ENABLE_B200} \
    -DENABLE_EXAMPLES=${UHD_ENABLE_EXAMPLES} \
    -DENABLE_DOXYGEN=0 \
    -DENABLE_MANUAL=0 \
    -DENABLE_MAN_PAGES=0 \
    -DENABLE_OCTOCLOCK=0 \
    -DENABLE_ORC=0 \
    -DENABLE_USRP1=0 \
    -DENABLE_USRP2=${UHD_ENABLE_USRP2} \
    -DENABLE_UTILS=${UHD_ENABLE_UTILS}

# Build and install
make -j${MAKE_THREADS}
make install
ldconfig

# Clean up intermediate build results
cd ..
rm -rf build
