FROM stgvozde/gnuradio-3.8:latest

# install zigbee stuff from Bastian
RUN git clone https://github.com/bastibl/gr-foo.git \
    && cd gr-foo \
    && git checkout maint-3.8 \
    && mkdir build \
    && cd build \
    && cmake .. \
    && make \
    && sudo make install \
    && sudo ldconfig

RUN git clone https://github.com/bastibl/gr-ieee802-15-4.git \
    && cd gr-ieee802-15-4 \
    && git checkout maint-3.8 \
    && mkdir build \
    && cd build \
    && cmake .. -DCMAKE_BUILD_TYPE=Debug \
    && make \
    && sudo make install \
    && sudo ldconfig

RUN git clone https://github.com/gefa/gr-ble.git \
&& cd gr-ble \
&& mkdir build \
&& cd build \
&& cmake .. -DCMAKE_BUILD_TYPE=Debug \
&& make \
&& sudo make install \
&& sudo ldconfig

RUN pip3 install names