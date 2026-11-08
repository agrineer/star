#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: GnuRadio LimeSDR-mini HRPT Receiver
# Author: PlanetaryImaging.org
# Description: Based on gr-noaa version
# Generated: Mon Dec 30 17:57:10 2019
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt4 import Qt
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import noaa
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.qtgui import Range, RangeWidget
from optparse import OptionParser
import math, os, time
import osmosdr
import sip
import sys
import time
from gnuradio import qtgui


class gr_hrpt_lime(gr.top_block, Qt.QWidget):

    def __init__(self, dirout='/data/pi/SCRB/process', freq=1698e6, gain=30, input_file='/data/pi/tmp/archive_iq/noaa-19_2019-12-15T23-41-25.iq', lo_freq=1565.0e6, satellite='noaa-19'):
        gr.top_block.__init__(self, "GnuRadio LimeSDR-mini HRPT Receiver")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("GnuRadio LimeSDR-mini HRPT Receiver")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "gr_hrpt_lime")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())


        ##################################################
        # Parameters
        ##################################################
        self.dirout = dirout
        self.freq = freq
        self.gain = gain
        self.input_file = input_file
        self.lo_freq = lo_freq
        self.satellite = satellite

        ##################################################
        # Variables
        ##################################################
        self.sym_rate = sym_rate = 600*1109
        self.samp_rate = samp_rate = 4.0e6
        self.sps = sps = samp_rate/sym_rate
        self.satellite_label = satellite_label = satellite
        self.pll_alpha = pll_alpha = 0.005
        self.outputfile_label = outputfile_label = dirout + '/'  + satellite + '_' + time.strftime('%Y_%m%d_%H%M', time.gmtime()) + '.hrpt'
        self.max_clock_offset = max_clock_offset = 100e-6
        self.max_carrier_offset = max_carrier_offset = 3*math.pi*100e3/samp_rate
        self.if_freq = if_freq = freq - lo_freq
        self.hs = hs = int(sps/2.0)
        self.gain_knob = gain_knob = gain
        self.clock_alpha = clock_alpha = 0.005

        ##################################################
        # Blocks
        ##################################################
        self._outputfile_label_tool_bar = Qt.QToolBar(self)

        if None:
          self._outputfile_label_formatter = None
        else:
          self._outputfile_label_formatter = lambda x: str(x)

        self._outputfile_label_tool_bar.addWidget(Qt.QLabel('Ouput File'+": "))
        self._outputfile_label_label = Qt.QLabel(str(self._outputfile_label_formatter(self.outputfile_label)))
        self._outputfile_label_tool_bar.addWidget(self._outputfile_label_label)
        self.top_grid_layout.addWidget(self._outputfile_label_tool_bar)
        self._gain_knob_range = Range(0, 70, 1, gain, 200)
        self._gain_knob_win = RangeWidget(self._gain_knob_range, self.set_gain_knob, 'Gain Knob', "counter_slider", int)
        self.top_grid_layout.addWidget(self._gain_knob_win)
        self._satellite_label_tool_bar = Qt.QToolBar(self)

        if None:
          self._satellite_label_formatter = None
        else:
          self._satellite_label_formatter = lambda x: str(x)

        self._satellite_label_tool_bar.addWidget(Qt.QLabel('Satellite'+": "))
        self._satellite_label_label = Qt.QLabel(str(self._satellite_label_formatter(self.satellite_label)))
        self._satellite_label_tool_bar.addWidget(self._satellite_label_label)
        self.top_grid_layout.addWidget(self._satellite_label_tool_bar)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_c(
        	1024, #size
        	samp_rate, #samp_rate
        	"", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1.5, 1.5)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)

        if not True:
          self.qtgui_time_sink_x_0.disable_legend()

        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 0, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in xrange(2):
            if len(labels[i]) == 0:
                if(i % 2 == 0):
                    self.qtgui_time_sink_x_0.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_0.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.pyqwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
        	1024, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	freq, #fc
        	samp_rate, #bw
        	"HRPT Frequency Spectrum", #name
        	1 #number of inputs
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.15)
        self.qtgui_freq_sink_x_0.set_y_axis(-55, -25)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(0.1)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)

        if not True:
          self.qtgui_freq_sink_x_0.disable_legend()

        if "complex" == "float" or "complex" == "msg_float":
          self.qtgui_freq_sink_x_0.set_plot_pos_half(not True)

        labels = ['HRPT Signal', '', '', '', '',
                  '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["red", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.pyqwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.pll = noaa.hrpt_pll_cf(pll_alpha, (pll_alpha**2)/4.0, max_carrier_offset)
        self.osmosdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "soapy=0,driver=lime" )
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(if_freq, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(gain_knob, 0)
        self.osmosdr_source_0.set_if_gain(0, 0)
        self.osmosdr_source_0.set_bb_gain(0, 0)
        self.osmosdr_source_0.set_antenna('LNAW', 0)
        self.osmosdr_source_0.set_bandwidth(samp_rate, 0)

        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(sps/2.0, (clock_alpha**2)/4.0, 0.5, clock_alpha, max_clock_offset)
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.deframer = noaa.hrpt_deframer()
        self.decoder = noaa.hrpt_decoder(True,False)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(hs, 1.0/hs, 4000, 1)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_short*1, outputfile_label, False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.analog_agc_xx_0 = analog.agc_cc(1e-6, 1.0, 1)
        self.analog_agc_xx_0.set_max_gain(65536)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_agc_xx_0, 0), (self.pll, 0))
        self.connect((self.analog_agc_xx_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.deframer, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.deframer, 0), (self.decoder, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.deframer, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.analog_agc_xx_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.pll, 0), (self.blocks_moving_average_xx_0, 0))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "gr_hrpt_lime")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_dirout(self):
        return self.dirout

    def set_dirout(self, dirout):
        self.dirout = dirout
        self.set_outputfile_label(self._outputfile_label_formatter(self.dirout + '/'  + self.satellite + '_' + time.strftime('%Y_%m%d_%H%M', time.gmtime()) + '.hrpt'))

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.set_if_freq(self.freq - self.lo_freq)
        self.qtgui_freq_sink_x_0.set_frequency_range(self.freq, self.samp_rate)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.set_gain_knob(self.gain)

    def get_input_file(self):
        return self.input_file

    def set_input_file(self, input_file):
        self.input_file = input_file

    def get_lo_freq(self):
        return self.lo_freq

    def set_lo_freq(self, lo_freq):
        self.lo_freq = lo_freq
        self.set_if_freq(self.freq - self.lo_freq)

    def get_satellite(self):
        return self.satellite

    def set_satellite(self, satellite):
        self.satellite = satellite
        self.set_outputfile_label(self._outputfile_label_formatter(self.dirout + '/'  + self.satellite + '_' + time.strftime('%Y_%m%d_%H%M', time.gmtime()) + '.hrpt'))
        self.set_satellite_label(self._satellite_label_formatter(self.satellite))

    def get_sym_rate(self):
        return self.sym_rate

    def set_sym_rate(self, sym_rate):
        self.sym_rate = sym_rate
        self.set_sps(self.samp_rate/self.sym_rate)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_sps(self.samp_rate/self.sym_rate)
        self.set_max_carrier_offset(3*math.pi*100e3/self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(self.freq, self.samp_rate)
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.osmosdr_source_0.set_bandwidth(self.samp_rate, 0)

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_hs(int(self.sps/2.0))
        self.digital_clock_recovery_mm_xx_0.set_omega(self.sps/2.0)

    def get_satellite_label(self):
        return self.satellite_label

    def set_satellite_label(self, satellite_label):
        self.satellite_label = satellite_label
        Qt.QMetaObject.invokeMethod(self._satellite_label_label, "setText", Qt.Q_ARG("QString", self.satellite_label))

    def get_pll_alpha(self):
        return self.pll_alpha

    def set_pll_alpha(self, pll_alpha):
        self.pll_alpha = pll_alpha
        self.pll.set_alpha(self.pll_alpha)
        self.pll.set_beta((self.pll_alpha**2)/4.0)

    def get_outputfile_label(self):
        return self.outputfile_label

    def set_outputfile_label(self, outputfile_label):
        self.outputfile_label = outputfile_label
        Qt.QMetaObject.invokeMethod(self._outputfile_label_label, "setText", Qt.Q_ARG("QString", self.outputfile_label))
        self.blocks_file_sink_0.open(self.outputfile_label)

    def get_max_clock_offset(self):
        return self.max_clock_offset

    def set_max_clock_offset(self, max_clock_offset):
        self.max_clock_offset = max_clock_offset

    def get_max_carrier_offset(self):
        return self.max_carrier_offset

    def set_max_carrier_offset(self, max_carrier_offset):
        self.max_carrier_offset = max_carrier_offset
        self.pll.set_max_offset(self.max_carrier_offset)

    def get_if_freq(self):
        return self.if_freq

    def set_if_freq(self, if_freq):
        self.if_freq = if_freq
        self.osmosdr_source_0.set_center_freq(self.if_freq, 0)

    def get_hs(self):
        return self.hs

    def set_hs(self, hs):
        self.hs = hs
        self.blocks_moving_average_xx_0.set_length_and_scale(self.hs, 1.0/self.hs)

    def get_gain_knob(self):
        return self.gain_knob

    def set_gain_knob(self, gain_knob):
        self.gain_knob = gain_knob
        self.osmosdr_source_0.set_gain(self.gain_knob, 0)

    def get_clock_alpha(self):
        return self.clock_alpha

    def set_clock_alpha(self, clock_alpha):
        self.clock_alpha = clock_alpha
        self.digital_clock_recovery_mm_xx_0.set_gain_omega((self.clock_alpha**2)/4.0)
        self.digital_clock_recovery_mm_xx_0.set_gain_mu(self.clock_alpha)


def argument_parser():
    description = 'Based on gr-noaa version'
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option, description=description)
    parser.add_option(
        "-d", "--dirout", dest="dirout", type="string", default='/data/pi/SCRB/process',
        help="Set Dirout [default=%default]")
    parser.add_option(
        "-f", "--freq", dest="freq", type="eng_float", default=eng_notation.num_to_str(1698e6),
        help="Set Frequency [default=%default]")
    parser.add_option(
        "-g", "--gain", dest="gain", type="intx", default=30,
        help="Set Gain [default=%default]")
    parser.add_option(
        "-i", "--input-file", dest="input_file", type="string", default='/data/pi/tmp/archive_iq/noaa-19_2019-12-15T23-41-25.iq',
        help="Set Input File [default=%default]")
    parser.add_option(
        "-l", "--lo-freq", dest="lo_freq", type="eng_float", default=eng_notation.num_to_str(1565.0e6),
        help="Set Local Oscilator Frequency [default=%default]")
    parser.add_option(
        "-s", "--satellite", dest="satellite", type="string", default='noaa-19',
        help="Set Satellite [default=%default]")
    return parser


def main(top_block_cls=gr_hrpt_lime, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(dirout=options.dirout, freq=options.freq, gain=options.gain, input_file=options.input_file, lo_freq=options.lo_freq, satellite=options.satellite)
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
