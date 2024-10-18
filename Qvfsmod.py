# -*- coding: utf-8 -*-
"""
/***************************************************************************

                              -------------------
        begin                : 2024-08-09
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Iñigo Barberena Ruiz
        email                : inigo.barberena@unavarra.es

 ***************************************************************************/
"""



from PyQt5 import QtWidgets,QtGui
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QThread,pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog,QButtonGroup,QRadioButton,QSpacerItem,QSizePolicy
# Initialize Qt resources from file resources.py
from resources import *
# Import the code for the dialog
from ui.Qvfsmod_dialog import qvfsmodDialog
from ui.user_defined_storm_type import user_defined_storm_dialog
from ui.hydrograph_dialog import output_hydrograph
from ui.overland_flow import overland_flow
from ui.buffer_segment import buffer_segment
from ui.infiltration_soil_properties import infiltration_soil_properties
from ui.soil_characteristic_curves import soil_characteristic_curves
from ui.buffer_properties import buffer_properties
from ui.water_quality import water_quality
from ui.incoming_sediment import incoming_sediment
from ui.vfsmod_hyetograph import vfsmod_hyetograph
from ui.hyetograph import hyetograph
from ui.vfsmod_hydrograph import vfsmod_hydrograph
from ui.warning_message import warning_message
from ui.warning_message_calibration import warning_message_calibration
from ui.design_results import design_results
from ui.design_results_graph import design_results_graph
from ui.calibration_advanced_settings import calibration_advanced_settings
from ui.sedimentograph_output import sedimentograph_output
from ui.user_output_1 import user_output_1
from ui.user_output_2 import user_output_2
from ui.osp_results import osp_results
from ui.runoff_graph import runoff_graph
from ui.sediment_graph import sediment_graph
from ui.owq_results import owq_results
from ui.osm_results import osm_results
from ui.ohy_results import ohy_results
from ui.og2_results import og2_results
from ui.og1_results import og1_results
from ui.irn_results import irn_results
from ui.iro_results import iro_results
from ui.owq_graph import owq_graph
from ui.owq_graph_balance import owq_graph_balance
from ui.calibration_progress import calibration_progress
from ui.calibration_results_sedimentograph import calibration_results_sedimentograph
from ui.calibration_results_hydrograph import calibration_results_hydrograph

#Local libraries
from libraries.SALib.sample import saltelli
from libraries.SALib.analyze import sobol
from libraries.SALib.sample.morris import sample as sample_morris 
from libraries.SALib.analyze.morris import analyze as analyze_morris

from libraries.SALib.sample.fast_sampler import sample as sample_fast
from libraries.SALib.analyze.fast import analyze as analyze_fast

from scipy.optimize import differential_evolution, minimize
from multiprocessing import Pool
import psutil
import time
import concurrent.futures
from pathlib import Path
import os.path
import pandas as pd
import subprocess
import shutil
import numpy as np
import re
from scipy.interpolate import interp1d
from scipy import stats
from itertools import product
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.ticker as tkr
from matplotlib.ticker import FuncFormatter
from PyQt5.QtWidgets import QVBoxLayout,QTableWidgetItem,QProgressDialog,QLabel, QLineEdit

import sys


class qvfsmod:
    """QGIS Plugin Implementation."""

    def __init__(self):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """


        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        
        #Save the directory of the plugin
        self.plugin_directory = os.path.dirname(__file__)
        
        #Initializce GUI
        self.initGui()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('qvfsmod', message)


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
  
        #Instantiate dialogs
        self.dlg_base = qvfsmodDialog()
        self.dlg_user_storm = user_defined_storm_dialog()
        self.dlg_overland_flow = overland_flow()
        self.dlg_buffer_segment = buffer_segment()
        self.dlg_infiltration_soil = infiltration_soil_properties()
        self.dlg_soil_curves = soil_characteristic_curves()
        self.dlg_buffer_properties = buffer_properties()
        self.dlg_water_quality = water_quality()
        self.dlg_incoming_sediment = incoming_sediment()
        self.dlg_vfsmod_hyetograph = vfsmod_hyetograph()
        self.dlg_vfsmod_hydrograph = vfsmod_hydrograph()
        self.dlg_warning_message = warning_message()
        self.dlg_warning_message_calibration = warning_message_calibration()
        self.dlg_design_results = design_results()
        self.dlg_design_results_graph = design_results_graph()
        self.dlg_calibration_advanced_settings = calibration_advanced_settings()
        self.dlg_sedimentograph_output = sedimentograph_output()
        self.dlg_user_output_1 = user_output_1()
        self.dlg_user_output_2 = user_output_2()
        self.dlg_osp_results = osp_results()
        self.dlg_runoff_graph = runoff_graph()
        self.dlg_sediment_graph = sediment_graph()
        self.dlg_owq_results = owq_results()
        self.dlg_osm_results = osm_results()
        self.dlg_ohy_results = ohy_results()
        self.dlg_og2_results = og2_results()
        self.dlg_og1_results = og1_results()
        self.dlg_iro_results = iro_results()
        self.dlg_irn_results = irn_results()
        self.dlg_owq_graph = owq_graph()
        self.dlg_owq_graph_balance = owq_graph_balance()
        self.dlg_calibration_progress = calibration_progress()
        self.dlg_calibration_results_sedimentograph = calibration_results_sedimentograph()
        self.dlg_calibration_results_hydrograph = calibration_results_hydrograph()
        
        #Set working directory
        self.dlg_base.working_directory_vfsmod.textChanged.connect(self.set_working_directory)
        
        #If the storm type is user defined, then emerges a dialog to add the data
        self.dlg_base.storm_type.currentIndexChanged.connect(self.user_defined_storm_type)
        
        #Calibration results
        self.dlg_base.calibration_result_hydrograph.clicked.connect(self.dlg_calibration_results_hydrograph.show)
        self.dlg_base.calibration_result_sedimentograph.clicked.connect(self.dlg_calibration_results_sedimentograph.show)
        self.dlg_calibration_results_hydrograph.results.textChanged.connect(self.update_graph_calibration_hydrograph)
        self.dlg_calibration_results_hydrograph.one_one.toggled.connect(self.update_graph_calibration_hydrograph)
        self.dlg_calibration_results_sedimentograph.results.textChanged.connect(self.update_graph_calibration_sedimentograph)
        self.dlg_calibration_results_sedimentograph.one_one.toggled.connect(self.update_graph_calibration_sedimentograph)
        
        #Stacked widget
        self.dlg_base.pushButton_6.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_folder))
        self.dlg_base.pushButton_7.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_uh))
        self.dlg_base.pushButton_8.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_vfs))
        self.dlg_base.pushButton_5.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_simple))
        self.dlg_base.pushButton_14.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_advanced))
        self.dlg_base.pushButton_15.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_hydrograph))
        self.dlg_base.pushButton_16.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_sedimentograph))
        self.dlg_base.pushButton_21.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sensitivity_analysis))
        self.dlg_base.pushButton_24.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sobol_results))
        
        self.dlg_base.folder_selection.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_folder))
        self.dlg_base.uh.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_uh))
        self.dlg_base.vfs.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_vfs))
        self.dlg_base.simple_design.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_simple))
        self.dlg_base.advanced_design.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_advanced))
        self.dlg_base.calibration_hydrograph.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_hydrograph))
        self.dlg_base.calibration_sedimentograph.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_sedimentograph))
        self.dlg_base.sensitivity_parameters.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sensitivity_analysis))
        self.dlg_base.sobol_results.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sobol_results))
        self.dlg_base.local_results.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.oat_results))
        self.dlg_base.execution_uncertainity.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.uncertainity_page))
        self.dlg_base.results_uncertainity.clicked.connect(lambda: self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_results_uncertainity))
        
        #Conditions to show differente stacked widgets pages
        self.dlg_base.calibration.clicked.connect(self.show_calibration_buttons)
        self.dlg_base.pushButton_10.clicked.connect(self.show_calibration_buttons)
        
        self.dlg_base.design.clicked.connect(self.show_design_buttons)
        self.dlg_base.pushButton_9.clicked.connect(self.show_design_buttons)
        
        self.dlg_base.sensitivity_analysis.clicked.connect(self.show_sensitivity_buttons)
        self.dlg_base.pushButton_11.clicked.connect(self.show_sensitivity_buttons)
        
        
        #In the dialog base, if a button is clicked then uncheck the rest
        base_buttons = [[self.dlg_base.pushButton_6,self.dlg_base.folder_selection],
            [self.dlg_base.pushButton_7,self.dlg_base.uh],
            [self.dlg_base.pushButton_8,self.dlg_base.vfs],
            [self.dlg_base.pushButton_9,self.dlg_base.design],
            [self.dlg_base.pushButton_5,self.dlg_base.simple_design],
            [self.dlg_base.pushButton_14,self.dlg_base.advanced_design],
            [self.dlg_base.pushButton_10,self.dlg_base.calibration],
            [self.dlg_base.pushButton_15,self.dlg_base.calibration_hydrograph],
            [self.dlg_base.pushButton_16,self.dlg_base.calibration_sedimentograph],
            [self.dlg_base.pushButton_11,self.dlg_base.sensitivity_analysis],
            [self.dlg_base.pushButton_21,self.dlg_base.sensitivity_parameters],
            [self.dlg_base.pushButton_24,self.dlg_base.sobol_results],
            [self.dlg_base.pushButton_12,self.dlg_base.uncertainity]]
        self.group_uno = QButtonGroup(None)
        self.group_dos = QButtonGroup(None)
        for i in base_buttons:
            self.group_uno.addButton(i[0])
            self.group_dos.addButton(i[1])
        self.group_uno.setExclusive(True)
        self.group_dos.setExclusive(True)

        #Close osp results dialog
        self.dlg_osp_results.close_dialog.clicked.connect(self.dlg_osp_results.close)
        
        #Select directory of the project for UH and for VFSMOD
        self.dlg_base.select_directory_vfsmod.clicked.connect(self.select_directory_vfsmod)
        
        #Select UH project file
        self.dlg_base.select_lis.clicked.connect(self.select_lis)
        
        #Select UH input file
        self.dlg_base.select_inp.clicked.connect(self.select_inp)
        
        #Select location of UH outputs
        self.dlg_base.browse_hydrograph.clicked.connect(self.select_iro)
        self.dlg_base.browse_hyetograph.clicked.connect(self.select_irn)
        self.dlg_base.browse_sedimentograph.clicked.connect(self.select_isd)
        self.dlg_base.browse_output1.clicked.connect(self.select_out)
        self.dlg_base.browse_output2.clicked.connect(self.select_hyt)
        
        #Select location of VFSMOD files
        self.dlg_base.browse_vfsmod_project.clicked.connect(self.select_prj)
        self.dlg_base.browse_overland.clicked.connect(self.select_ikw)
        self.dlg_base.browse_infiltration.clicked.connect(self.select_iso)
        self.dlg_base.browse_buffer.clicked.connect(self.select_igr)
        self.dlg_base.browse_incoming.clicked.connect(self.select_isd_vfsmod)##
        self.dlg_base.browse_storm.clicked.connect(self.select_irn_vfsmod)##
        self.dlg_base.browse_source.clicked.connect(self.select_iro_vfsmod) ##
        self.dlg_base.browse_water.clicked.connect(self.select_iwq)
        
        self.dlg_base.browse_sediment.clicked.connect(self.select_og1)
        self.dlg_base.browse_flow.clicked.connect(self.select_og2)
        self.dlg_base.browse_hydrograph_2.clicked.connect(self.select_ohy)
        self.dlg_base.browse_waterland.clicked.connect(self.select_osm)
        self.dlg_base.browse_overall.clicked.connect(self.select_osp)
        self.dlg_base.browse_quality.clicked.connect(self.select_owq)
        
        #Change files names if the name of the files is changed
        self.dlg_base.name_files.textChanged.connect(self.update_file_names)
        
        self.dlg_design_results.graph.clicked.connect(self.dlg_design_results_graph.show)
        self.dlg_design_results.design_file.textChanged.connect(self.update_design_results)
        
        
        #Execution button
        self.dlg_base.execute.clicked.connect(self.uh_execution)
        
        
        #Images in the interface
        self.add_images()
        
        # put the elements in the combobox
        self.dlg_base.storm_type.addItems(["I","IA","II","III","User"])
        self.dlg_base.soil_type.addItems(["Clay","Silty clay","Sandy clay","Silty clay loam","Clay loam","Sandy clay loam","Silt","Silt loam","Loam",
            "Very fine sandy loam","Fine sandy loam","Sandy loam","Coarse sandy loam","Loamy very fine sand","Loamy fine sandy",
            "Loamy sand","Loamy coarse sand","Very fine sandy","Fine sand","Sand","Coarse sand"])
        self.dlg_base.combo_water.addItems(["1. Pesticides","2. Solute Transport","3. Multi-Reactive"])
        self.dlg_water_quality.calculation.addItems(["No calculation","Degradation changes with temperature and moisture","Degradation only","Degradation changes with temperature","Degradation changes with moisture"])
        self.dlg_water_quality.trapping_equation.addItems(["Sabbagh","Refit Sabbagh","Mass balance","Chen"])
        self.dlg_calibration_advanced_settings.objective_function.addItems(["RMSE","NSE","NNSE"])
        
        self.dlg_water_quality.trapping_equation.currentIndexChanged.connect(self.update_pesticide_coefficients)
        self.dlg_water_quality.frame_2.hide()
        
        #Add to combobox the values that could be graphed in the design process
        self.dlg_design_results_graph.column.addItems(["Total Runoff from source (mm)","Total Runoff from Source (m3)",
            "Total Runoff out from Filter (mm)","Total Runoff out from Filter (m3)","Total Infiltration in Filter",
            "Mass Sediment Input to Filter","Concentration Sediment in Runoff from source Area",
            "Mass Sediment Output from Filter","Concentration Sediment in Runoff exiting the Filter",
            "Sediment Delivery Ratio","Runoff Delivery Ratio"])
        
        #When combobox changed in design graph the update the graph
        self.dlg_design_results_graph.column.currentIndexChanged.connect(self.update_design_graph)
        
        #Watch results from design process
        self.dlg_base.view_results_design.clicked.connect(self.dlg_design_results.show)
        
        #If no pesticide mass balance/residue calculation is requested then hide frame
        self.dlg_water_quality.calculation.currentIndexChanged.connect(self.hide_mass_balance_frame)
        self.dlg_water_quality.frame_5.hide()
        #Modify table of water quality
        self.dlg_water_quality.tableWidget.verticalHeader().setVisible(False)
        self.dlg_water_quality.tableWidget.setColumnWidth(0, 100) 
        self.dlg_water_quality.tableWidget.setColumnWidth(1, 230)
        self.dlg_water_quality.tableWidget.setColumnWidth(2, 250)
        self.dlg_water_quality.days.textChanged.connect(self.change_rows_water_quality)
        
        #If text of the outputs is changed then check if the output exist for UH
        lineEdits = [self.dlg_base.uh_file,self.dlg_base.uh_input,self.dlg_base.line_hydrograph,
            self.dlg_base.line_hyetograph,self.dlg_base.line_sedimentograph,self.dlg_base.line_output_1,self.dlg_base.line_output_2]
        for i in lineEdits:
            i.textChanged.connect(self.check_uh_output_exist)
        
        #The same for VFSMOD
        lineEdits = [self.dlg_base.line_sediment,self.dlg_base.line_flow,self.dlg_base.line_hydrograph_2,
            self.dlg_base.line_waterland,self.dlg_base.line_overall,self.dlg_base.line_quality]
        for i in lineEdits:
            i.textChanged.connect(self.check_vfsmod_output_exist)
        
        #When project file name changes then update to design, calibration, sensitivity analysis and uncertainity
        self.dlg_base.name_files.textChanged.connect(self.update_project_files)
        
        #Check if added outputs exist in UH and in VFSMOD
        self.check_uh_output_exist()
        self.check_vfsmod_output_exist()
        
        #Quit the warning advice
        self.dlg_warning_message.ok.clicked.connect(self.dlg_warning_message.close)
        
        #Show outputs
        #UH
        self.dlg_base.output_hydrograph.clicked.connect(self.dlg_iro_results_show)
        self.dlg_iro_results.graph.clicked.connect(self.show_hydrograph)
        self.dlg_base.output_hyetograph.clicked.connect(self.dlg_irn_results_show)
        self.dlg_irn_results.graph.clicked.connect(self.show_hyetograph)
        
        self.dlg_base.output_sedimentograph.clicked.connect(self.show_sedimentograph_results)
        self.dlg_base.output_output1.clicked.connect(self.show_output_1_results)
        self.dlg_base.output_output2.clicked.connect(self.show_output_2_results)
        #VFSMOD
        self.dlg_base.output_overall.clicked.connect(self.show_osp_results)
        self.dlg_osp_results.runoff_graph.clicked.connect(self.show_runoff_results)
        self.dlg_osp_results.sediment_graph.clicked.connect(self.show_sediment_results)
        self.dlg_base.output_quality.clicked.connect(self.show_owq_results)
        self.dlg_base.output_waterland.clicked.connect(self.show_osm_results)
        self.dlg_base.output_hydrograph_2.clicked.connect(self.show_ohy_results)
        self.dlg_base.output_flow.clicked.connect(self.show_og2_results)
        self.dlg_base.output_sediment.clicked.connect(self.show_og1_results)
        
        #Show owq results graph
        self.dlg_owq_results.graph.clicked.connect(self.show_owq_graph)
        self.dlg_owq_results.balance_graph.clicked.connect(self.show_owq_graph_balance)
        
        #Disable combobox of water quality and add condition to set enable it. Same with the rest of the widgets
        self.dlg_base.combo_water.setVisible(False)
        #Water quality properties
        self.dlg_base.label_quality_properties.setVisible(False)
        self.dlg_base.line_water.setVisible(False)
        self.dlg_base.edit_water.setVisible(False)
        self.dlg_base.browse_water.setVisible(False)
        #Water quality summary
        self.dlg_base.label_water_summary.setVisible(False)
        self.dlg_base.line_quality.setVisible(False)
        self.dlg_base.browse_quality.setVisible(False)
        self.dlg_base.output_quality.setVisible(False)
        self.dlg_base.water_quality.stateChanged.connect(self.water_quality_dialog)
        self.dlg_base.water_quality.stateChanged.connect(self.update_ikw_pesticide)
        
        #Enable second layer in infiltration - soil properties
        self.dlg_infiltration_soil.frame_5.setVisible(False)
        self.dlg_infiltration_soil.radio_one.toggled.connect(self.show_second_layer)
        
        #Enable water table dialog option
        self.dlg_infiltration_soil.frame_6.setVisible(False)
        self.dlg_infiltration_soil.check_water_table.stateChanged.connect(self.show_water_table)
        
        #Enable Input h_e(m)? in infiltration soil properties dialog
        self.dlg_infiltration_soil.line_input.setVisible(False)
        self.dlg_infiltration_soil.check_input.stateChanged.connect(self.show_input_soil_properties)
        
        #When text changed in vertical saturated K, then update the other units
        self.dlg_infiltration_soil.line_vertical_ms.textChanged.connect(self.update_k_units_cmh_1)
        self.dlg_infiltration_soil.line_vertical_cmh.textChanged.connect(self.update_k_units_ms_1)
        self.dlg_infiltration_soil.line_vertical_ms_2.textChanged.connect(self.update_k_units_cmh_2)
        self.dlg_infiltration_soil.line_vertical_cmh_2.textChanged.connect(self.update_k_units_ms_2)
        
        
        #Appear the VFSMOD editing dialogs
        self.dlg_base.edit_overland.clicked.connect(self.dlg_overland_flow_show)
        self.dlg_overland_flow.edit_segment.clicked.connect(self.dlg_buffer_segment_show)
        self.dlg_base.edit_infiltration.clicked.connect(self.dlg_infiltration_soil_show)
        self.dlg_infiltration_soil.show_parameters.clicked.connect(self.show_soil_curves)
        self.dlg_base.edit_buffer.clicked.connect(self.dlg_buffer_properties_show)
        self.dlg_base.edit_water.clicked.connect(self.dlg_water_quality_show)
        self.dlg_base.edit_incoming.clicked.connect(self.dlg_incoming_sediment_show)
        self.dlg_base.edit_storm.clicked.connect(self.add_hyetograph_to_dialog)
        self.dlg_base.edit_source.clicked.connect(self.add_hydrograph_to_dialog)
        

        #Enable/disable edition in water quality dialog
        self.enable_disable_water_quality_dialog()
        self.dlg_water_quality.check_direct.stateChanged.connect(self.enable_disable_water_quality_dialog)
        
        #Add and remove rows for the buffer segment
        self.dlg_buffer_segment.add_row.clicked.connect(self.add_row)
        self.dlg_buffer_segment.remove_row.clicked.connect(self.remove_row)
        
        #Add and remove rows for the vfsmod hyetograph
        self.dlg_vfsmod_hyetograph.add.clicked.connect(self.vfsmod_hyetograph_add_row)
        self.dlg_vfsmod_hyetograph.remove.clicked.connect(self.vfsmod_hyetograph_remove_row)
        #Same for hydrograph
        self.dlg_vfsmod_hydrograph.add.clicked.connect(self.vfsmod_hydrograph_add_row)
        self.dlg_vfsmod_hydrograph.remove.clicked.connect(self.vfsmod_hydrograph_remove_row)
        
        #Select .lis and .prj from the local files to the design
        self.dlg_base.browse_design_uh.clicked.connect(self.select_lis_design)
        self.dlg_base.browse_design_vfs.clicked.connect(self.select_prj_design)
        
        #If text changed in the file of the UH project, in the design, then add the storm duration, buffer length and spacing
        self.dlg_base.design_uh_file.textChanged.connect(self.add_storm_duration_to_design)
        self.dlg_base.design_vfs_file.textChanged.connect(self.add_vfs_length_spacing)
        
        #Update the graph of the results of design
        self.dlg_design_results_graph.threshold.textChanged.connect(self.update_design_graph)
        
        #Run design
        self.dlg_base.design_run.clicked.connect(self.run_design_part_one)
        
        
        #Update values of .ikw file
        self.dlg_overland_flow.save_continue.clicked.connect(self.create_ikw_file)
        self.dlg_overland_flow.save_close.clicked.connect(lambda _, b = True:self.create_ikw_file(b))
        self.dlg_overland_flow.close_dialog.clicked.connect(self.dlg_overland_flow.close)
        
        #Update values of .iso file
        self.dlg_infiltration_soil.save_continue.clicked.connect(self.create_iso_file)
        self.dlg_infiltration_soil.save_close.clicked.connect(lambda _, b = True:self.create_iso_file(b))
        self.dlg_infiltration_soil.close_dialog.clicked.connect(self.dlg_infiltration_soil.close)
        
        #Update values of .igr file
        self.dlg_buffer_properties.save_continue.clicked.connect(self.create_igr_file)
        self.dlg_buffer_properties.save_close.clicked.connect(lambda _, b = True:self.create_igr_file(b))
        self.dlg_buffer_properties.close_dialog.clicked.connect(self.dlg_buffer_properties.close)
        
        #Update values of .iwq file
        self.dlg_incoming_sediment.save_continue.clicked.connect(self.create_isd_file)
        self.dlg_incoming_sediment.save_close.clicked.connect(lambda _, b = True:self.create_isd_file(b))
        self.dlg_incoming_sediment.close_dialog.clicked.connect(self.dlg_incoming_sediment.close)
        
        #Update values of .irn file
        self.dlg_vfsmod_hyetograph.save_continue.clicked.connect(self.create_irn_file)
        self.dlg_vfsmod_hyetograph.save_close.clicked.connect(lambda _, b = True:self.create_irn_file(b))
        self.dlg_vfsmod_hyetograph.close_dialog.clicked.connect(self.dlg_vfsmod_hyetograph.close)
        
        #Update values of segment of buffer
        self.dlg_buffer_segment.close_dialog.clicked.connect(self.dlg_buffer_segment.close)
        
        #Update values of .iro file
        self.dlg_vfsmod_hydrograph.save_continue.clicked.connect(self.create_iro_file)
        self.dlg_vfsmod_hydrograph.save_close.clicked.connect(lambda _, b = True:self.create_iro_file(b))
        self.dlg_vfsmod_hydrograph.close_dialog.clicked.connect(self.dlg_vfsmod_hydrograph.close)
        
        #Update values of .isd file
        self.dlg_water_quality.save_continue.clicked.connect(self.create_iwq_file)
        self.dlg_water_quality.save_close.clicked.connect(lambda _, b = True:self.create_iwq_file(b))
        self.dlg_water_quality.close_dialog.clicked.connect(self.dlg_water_quality.close)
        
        #Run VFSMOD
        self.dlg_base.run_vfsmod.clicked.connect(self.run_vfsmod)
        
        #In calibration only one of VFS length or spacing can be activated
        self.dlg_base.design_length.stateChanged.connect(lambda _, b = "length":self.uncheck_length_spacing(b))
        self.dlg_base.design_spacing.stateChanged.connect(lambda _, b = "spacing":self.uncheck_length_spacing(b))
        
        #Button to add information to the sensitivity table and to uncertainity
        self.dlg_base.add.clicked.connect(self.add_sensitivity_table)
        self.dlg_base.add_uncertainity.clicked.connect(self.add_uncertainity_table)
        #Button to delete information of the sensitivity table an to uncertainity
        self.dlg_base.remove.clicked.connect(self.delete_sensitivity_table)
        self.dlg_base.remove_uncertainity.clicked.connect(self.delete_uncertainity_table)
        
        #Show design graph 
        self.dlg_design_results.graph.clicked.connect(self.show_design_graph)
        
        #Browse csv results design
        self.dlg_design_results.browse_design.clicked.connect(self.browse_design_results_csv)
        
        #In design disable lineEdits depending on selection
        self.dlg_base.specific.toggled.connect(self.disable_storm_line_edits_design)
        self.dlg_base.design_length.clicked.connect(self.disable_storm_line_edits_design)
        self.dlg_base.design_spacing.clicked.connect(self.disable_storm_line_edits_design)
        self.disable_storm_line_edits_design() #by default
        
        #In calibration enable/disable lineEdits depending on selection
        #First with the hidrograph
        self.hydrology_checks = [[[self.dlg_base.no_vertical,self.dlg_base.change_vertical,self.dlg_base.calibrate_vertical],[self.dlg_base.new_vertical,self.dlg_base.min_vertical,self.dlg_base.max_vertical]],
            [[self.dlg_base.no_average,self.dlg_base.change_average,self.dlg_base.calibrate_average],[self.dlg_base.new_average,self.dlg_base.min_average,self.dlg_base.max_average]],
            [[self.dlg_base.no_saturated,self.dlg_base.change_saturated,self.dlg_base.calibrate_saturated],[self.dlg_base.new_saturated,self.dlg_base.min_saturated,self.dlg_base.max_saturated]],
            [[self.dlg_base.no_initial,self.dlg_base.change_initial,self.dlg_base.calibrate_initial],[self.dlg_base.new_initial,self.dlg_base.min_initial,self.dlg_base.max_initial]],
            [[self.dlg_base.no_maximum,self.dlg_base.change_maximum,self.dlg_base.calibrate_maximum],[self.dlg_base.new_maximum,self.dlg_base.min_maximum,self.dlg_base.max_maximum]],
            [[self.dlg_base.no_fraction,self.dlg_base.change_fraction,self.dlg_base.calibrate_fraction],[self.dlg_base.new_fraction,self.dlg_base.min_fraction,self.dlg_base.max_fraction]],
            [[self.dlg_base.no_width,self.dlg_base.change_width,self.dlg_base.calibrate_width],[self.dlg_base.new_width,self.dlg_base.min_width,self.dlg_base.max_width]],
            [[self.dlg_base.no_length,self.dlg_base.change_length,self.dlg_base.calibrate_length],[self.dlg_base.new_length,self.dlg_base.min_length,self.dlg_base.max_length]],
            [[self.dlg_base.no_manning,self.dlg_base.change_manning,self.dlg_base.calibrate_manning],[self.dlg_base.new_manning,self.dlg_base.min_manning,self.dlg_base.max_manning]],
            [[self.dlg_base.no_slope,self.dlg_base.change_slope,self.dlg_base.calibrate_slope],[self.dlg_base.new_slope,self.dlg_base.min_slope,self.dlg_base.max_slope]]]
        for i in self.hydrology_checks:
            i[0][0].toggled.connect(self.draw_calibration_hydrology)
            i[0][1].toggled.connect(self.draw_calibration_hydrology)
            i[0][2].toggled.connect(self.draw_calibration_hydrology)
        
        #The same for sedimentograph
        self.sedimentograph_checks = [[[self.dlg_base.no_spacing,self.dlg_base.change_spacing,self.dlg_base.calibrate_spacing],[self.dlg_base.new_spacing,self.dlg_base.min_spacing,self.dlg_base.max_spacing]],
            [[self.dlg_base.no_roughness,self.dlg_base.change_roughness,self.dlg_base.calibrate_roughness],[self.dlg_base.new_roughness,self.dlg_base.min_roughness,self.dlg_base.max_roughness]],
            [[self.dlg_base.no_height,self.dlg_base.change_height,self.dlg_base.calibrate_height],[self.dlg_base.new_height,self.dlg_base.min_height,self.dlg_base.max_height]],
            [[self.dlg_base.no_bare,self.dlg_base.change_bare,self.dlg_base.calibrate_bare],[self.dlg_base.new_bare,self.dlg_base.min_bare,self.dlg_base.max_bare]],
            [[self.dlg_base.no_coarse,self.dlg_base.change_coarse,self.dlg_base.calibrate_coarse],[self.dlg_base.new_coarse,self.dlg_base.min_coarse,self.dlg_base.max_coarse]],
            [[self.dlg_base.no_incoming,self.dlg_base.change_incoming,self.dlg_base.calibrate_incoming],[self.dlg_base.new_incoming,self.dlg_base.min_incoming,self.dlg_base.max_incoming]],
            [[self.dlg_base.no_porosity,self.dlg_base.change_porosity,self.dlg_base.calibrate_porosity],[self.dlg_base.new_porosity,self.dlg_base.min_porosity,self.dlg_base.max_porosity]],
            [[self.dlg_base.no_class,self.dlg_base.change_class,self.dlg_base.calibrate_class],[self.dlg_base.new_class,self.dlg_base.min_class,self.dlg_base.max_class]],
            [[self.dlg_base.no_density,self.dlg_base.change_density,self.dlg_base.calibrate_density],[self.dlg_base.new_density,self.dlg_base.min_density,self.dlg_base.max_density]]]
        for i in self.sedimentograph_checks:
            i[0][0].toggled.connect(self.draw_calibration_sedimentograph)
            i[0][1].toggled.connect(self.draw_calibration_sedimentograph)
            i[0][2].toggled.connect(self.draw_calibration_sedimentograph)
        
        #Show advances settings of calibration
        self.dlg_base.advanced_hydrograph.clicked.connect(self.dlg_calibration_advanced_settings.show)
        self.dlg_base.advanced_sedimentograph.clicked.connect(self.dlg_calibration_advanced_settings.show)
        self.dlg_calibration_advanced_settings.close_dialog.clicked.connect(self.dlg_calibration_advanced_settings.close)
        
        #Browse files in calibration
        self.dlg_base.browse_project.clicked.connect(lambda _, b = ["prj",self.dlg_base,self.dlg_base.vfs_project]:self.browse_files_calibration(b))
        self.dlg_base.browse_hydrograph_calibration.clicked.connect(lambda _, b = ["txt",self.dlg_base,self.dlg_base.hydrograph_file]:self.browse_files_calibration(b))
        self.dlg_base.browse_project_sedimentograph.clicked.connect(lambda _, b = ["prj",self.dlg_base,self.dlg_base.vfs_file]:self.browse_files_calibration(b))
        self.dlg_base.browse_sedimentograph_calibration.clicked.connect(lambda _, b = ["txt",self.dlg_base,self.dlg_base.sedimentograph_file]:self.browse_files_calibration(b))
        
        #Run calibration
        self.dlg_base.run_hydrograph.clicked.connect(self.run_calibration_hydrograph)
        self.dlg_base.run_sedimentograph.clicked.connect(self.run_calibration_sedimentograph)
        
        #Add distributions to combobox
        self.dlg_base.distributions.addItems(["Uniform","Logaritmic uniform","Triangular","Normal","Lognormal","Normal truncated"])
        self.dlg_base.distributions_uncertainity.addItems(["Uniform","Logaritmic uniform","Triangular","Normal","Lognormal","Normal truncated"])
        
        #Change bounds in sensitivity dialog if distribution changed
        self.dlg_base.distributions.currentIndexChanged.connect(self.change_bounds_sensitivity)
        self.dlg_base.oat.toggled.connect(self.change_bounds_sensitivity)
        self.dlg_base.oat.toggled.connect(self.distribution_parameters)
        #Add new parameters to distribution in sensitivity dialog
        self.dlg_base.distributions.currentIndexChanged.connect(self.distribution_parameters)
        
        #Same for uncertainity analysis
        self.dlg_base.distributions_uncertainity.currentIndexChanged.connect(self.change_bounds_uncertainity)
        self.dlg_base.distributions_uncertainity.currentIndexChanged.connect(self.distribution_parameters_uncertainity)
        
        #Change number of samples in dialog depending on sensitivity analysis metod
        self.dlg_base.sobol.toggled.connect(self.change_sensitivity_method)
        self.dlg_base.morris.toggled.connect(self.change_sensitivity_method)
        self.dlg_base.fast.toggled.connect(self.change_sensitivity_method)
        self.dlg_base.trajectories.textChanged.connect(self.change_sensitivity_method)
        
        #Set checked true OAT
        self.dlg_base.oat.setChecked(True)
        
        #Sensitivity analysis dialog buttons
        buttons = [self.dlg_base.all_parameters,self.dlg_base.rainfall_event,
            self.dlg_base.source_area,self.dlg_base.erosion_parameters,
            self.dlg_base.buffer_dimensions,self.dlg_base.kinematic_wave,
            self.dlg_base.infiltration,self.dlg_base.buffer_vegetation,self.dlg_base.incoming_sediment, self.dlg_base.water_quality_button]
        #Dictionary for the sensitivity parameters and information of the place where is saved {Name: [extension, row, column, uh/vfs]}
        self.sensitivity_parameters = {"Rainfall (mm)":["inp",0,0,"uh"],"Storm duration (h)":["inp",0,4,"uh"],"Curve number":["inp",0,1,"uh"],
                "Source Area Length along the slope (m)":["inp",0,5,"uh"], "Source Area Slope as a fraction":["inp",0,6,"uh"],"Source Area (ha)":["inp",0,2,"uh"],
                "Soil erodibility (K)":["inp",3,0,"uh"],"Percent organic matter":["inp",5,0,"uh"],"Crop factor":["inp",3,1,"uh"],"Particle Class Diameter":["inp",3,3,"uh"],"Practice Factor":["inp",3,2,"uh"],
                "Buffer length (m)":["ikw",2,0,"vfs"],"Width of the Strip (m)":["ikw",1,0,"vfs"],"Filter Manning n (RNA s/m^1/3)":["ikw","nan","nan","vfs"],"Average Filter Slope":["ikw","nan","nan","vfs"],
                "Number of Nodes":["ikw",2,1,"vfs"],"Time Weight Factor":["ikw",2,2,"vfs"],"Number of Elemental Nodal Points":["ikw",2,5,"vfs"],"Courant Number":["ikw",2,3,"vfs"],"Maximum Iterations":["ikw",2,4,"vfs"],
                "Vertical Saturated K":["iso",0,0,"vfs"],"Average Suction at the Wetting Front":["iso",0,1,"vfs"],"Initial Water Content":["iso",0,3,"vfs"],"Saturated Water Content":["iso",0,2,"vfs"],"Maximum Surface Storage":["iso",0,4,"vfs"],"Fraction of the filter where ponding is checked":["iso",0,5,"vfs"],
                "Spacing for grass stems (cm)":["igr",0,0,"vfs"],"Roughness-Grass Mannings n VN":["igr",0,1,"vfs"],"Height of grass (cm)":["igr",0,2,"vfs"],"Roughness-Bare surface Mannings n (Vn2)":["igr",0,3,"vfs"],
                "Incoming flow sediment concentration (g/cm^3)":["isd",0,2,"vfs"],"Sediment particle size diameter d50 (cm)":["isd",1,0,"vfs"],"Porosity of deposited sediment as a fraction":["isd",0,3,"vfs"],"Portion of Particles from incoming sediment \nwith diameter >0.0037 cm":["isd",0,1,"vfs"],"Sediment particle density (g/cm^3)":["isd",1,1,"vfs"],
                "Linear sorption coefficient (L/Kg)":["iwq",1,1,"vfs"],"Adsorption coefficient (L/Kg)":["iwq",1,1,"vfs"],"Organic Carbon (%)":["iwq",1,2,"vfs"],"Clay in incoming sediment (%)":["iwq",2,0,"vfs"],"Pesticide half-life (days)":["iwq",4,1,"vfs"],"Topsoil field capacity (m3/m3)":["iwq",4,2,"vfs"],"Total pesticide mass per unit area source field (mg/m2)":["iwq",4,3,"vfs"],"Surface mixing layer thickness (cm)":["iwq",4,4,"vfs"],"Dispersion length of chemical (m)":["iwq",4,5,"vfs"],"Runoff remobilized VFS residue \nfrom last event (mg/m2)":["iwq",4,6,"vfs"]}
        for i in buttons:
            i.clicked.connect(lambda _, b = i:self.show_buttons_sensitivity_dialog(b))
        
        #Same for uncertainity
        buttons = [self.dlg_base.all_parameters_2,self.dlg_base.rainfall_event_2,
            self.dlg_base.source_area_2,self.dlg_base.erosion_parameters_2,
            self.dlg_base.buffer_dimensions_2,self.dlg_base.kinematic_wave_2,
            self.dlg_base.infiltration_2,self.dlg_base.buffer_vegetation_2,self.dlg_base.incoming_sediment_2, self.dlg_base.water_quality_button_2]
        for i in buttons:
            i.clicked.connect(lambda _, b = i:self.show_buttons_uncertainity_dialog(b))
        
        #Search sensitivity parameter
        self.dlg_base.search.textChanged.connect(self.search_sensitivity_parameter)
        
        #Search uncertainity parameter
        self.dlg_base.search_uncertainity.textChanged.connect(self.search_uncertainity_parameter)
        
        #Run sensitivity analysis
        self.dlg_base.accept.clicked.connect(self.run_sensitivity_analysis_part_one)
        
        #Run uncertainity analysis
        self.dlg_base.run_uncertainity.clicked.connect(self.run_uncertainity_analysis_part_one)
        
        #Show sensitivity results
        self.dlg_base.sobol_results.clicked.connect(self.show_graph_sensitivity_global)
        self.dlg_base.local_results.clicked.connect(self.show_graph_sensitivity_oat)
        
        #Show uncertainity results
        self.dlg_base.results_uncertainity.clicked.connect(self.show_graph_sensitivity_uncertainity)
        
        #Browse file sensitivity graph
        self.dlg_base.browse.clicked.connect(self.browse_files_sensitivity_results)
        self.dlg_base.browse_2.clicked.connect(self.browse_files_sensitivity_results_sobol)
        self.dlg_base.browse_fast_csv.clicked.connect(self.browse_files_sensitivity_results_fast)
        
        #Browse calibration results
        self.dlg_calibration_results_hydrograph.browse.clicked.connect(self.browse_files_calibration_hydrograph)
        self.dlg_calibration_results_sedimentograph.browse.clicked.connect(self.browse_files_calibration_sedimentograph)
        
        #Update sensitivity graph for Sobol
        self.dlg_base.csv_results_2.textChanged.connect(self.update_sensitivity_graph_global)
        check_boxes = [self.dlg_base.runoff_source_mm_2,self.dlg_base.runoff_source_m3_2,
            self.dlg_base.runoff_filter_mm_2,self.dlg_base.runoff_filter_m3_2,
            self.dlg_base.infiltration_filter_m3_2,self.dlg_base.sediment_input_2,
            self.dlg_base.concentration_sediment_2,self.dlg_base.sediment_output_2,
            self.dlg_base.sediment_runoff_exit_2,self.dlg_base.sediment_delivery_2,
            self.dlg_base.runoff_delivery_2,self.dlg_base.radio_morris, self.dlg_base.radio_fast,self.dlg_base.radio_sobol]
        for i in check_boxes:
            i.toggled.connect(lambda checked, rb=i: self.update_sensitivity_graph_global() if checked else None)
        
        #Update sensitivity graph for OAT
        check_boxes = [self.dlg_base.runoff_source_mm_3,self.dlg_base.runoff_source_m3_3,
            self.dlg_base.runoff_filter_mm_3,self.dlg_base.runoff_filter_m3_3,
            self.dlg_base.infiltration_filter_m3_3,self.dlg_base.sediment_input_3,
            self.dlg_base.concentration_sediment_3,self.dlg_base.sediment_output_3,
            self.dlg_base.sediment_runoff_exit_3,self.dlg_base.sediment_delivery_3,
            self.dlg_base.runoff_delivery_3,
            self.dlg_base.input_output,self.dlg_base.absolute,self.dlg_base.relative_base,self.dlg_base.relative_sensitivity]
        for i in check_boxes:
            i.toggled.connect(lambda checked, rb=i: self.update_sensitity_graph_oat() if checked else None)
            
        #Update sensitivity graph for uncertainity
        check_boxes = [self.dlg_base.runoff_source_mm_4,self.dlg_base.runoff_source_m3_4,
            self.dlg_base.runoff_filter_mm_4,self.dlg_base.runoff_filter_m3_4,
            self.dlg_base.infiltration_filter_m3_4,self.dlg_base.sediment_input_4,
            self.dlg_base.concentration_sediment_4,self.dlg_base.sediment_output_4,
            self.dlg_base.sediment_runoff_exit_4,self.dlg_base.sediment_delivery_4,
            self.dlg_base.runoff_delivery_4]
        for i in check_boxes:
            i.toggled.connect(lambda checked, rb=i: self.update_graph_uncertainity() if checked else None)
        
        #Browse files in sensitivity analysis
        self.dlg_base.browse_uh.clicked.connect(lambda _, b = "lis":self.browse_files_sensitivity(b))
        self.dlg_base.browse_vfs.clicked.connect(lambda _, b = "prj":self.browse_files_sensitivity(b))
        self.dlg_base.browse_file.clicked.connect(lambda _, b = "csv":self.browse_files_sensitivity(b))
        
        #Browse files in uncertainity analysis
        self.dlg_base.browse_uh_uncertainity.clicked.connect(lambda _, b = "lis":self.browse_files_uncertainity(b))
        self.dlg_base.browse_vfs_uncertainity.clicked.connect(lambda _, b = "prj":self.browse_files_uncertainity(b))
        self.dlg_base.browse_file_uncertainity.clicked.connect(lambda _, b = "csv":self.browse_files_uncertainity(b))
        
        #Add base value to dialog in OAT sensitivity analysis
        self.dlg_base.uh_file_sensitivity.textChanged.connect(self.add_base_value_dialog_oat)
        self.dlg_base.vfs_file_sensitivity.textChanged.connect(self.add_base_value_dialog_oat)
        self.dlg_base.parameter_name.textChanged.connect(self.add_base_value_dialog_oat)
        
        
        #Disable the ability to modify the timestep of the user defined storm and center items
        self.set_timestep_non_editable()
        
        #Add values of the inp file to the dialog
        self.dlg_base.uh_input.textChanged.connect(self.add_values_inp_dialog)
        self.dlg_base.uh_file.textChanged.connect(self.add_values_uh_outputs_dialog)
        
        #Add filepaths to vfs when prj is changed
        self.dlg_base.line_project_vfsmod.textChanged.connect(self.add_values_vfs_outputs_dialog)
        
        #Default values
        self.default_values()
        
        
        
        #Change table of buffer segments when buffer length is changed
        self.dlg_overland_flow.length.textChanged.connect(self.update_buffer_length_table)
        
        #Update buffer segment graph when table is changed
        self.dlg_buffer_segment.tableWidget.itemChanged.connect(self.update_buffer_segment_graph)
        #Same for vfsmod hyetograph and hydrograph
        self.dlg_vfsmod_hydrograph.tableWidget.itemChanged.connect(self.update_vfsmod_hydrograph_graph)
        self.dlg_vfsmod_hyetograph.tableWidget.itemChanged.connect(self.update_vfsmod_hyetograph_graph)
        
        #Browse csv of oat sensitivity analysis
        self.dlg_base.browse_oat_csv.clicked.connect(self.browse_csv_oat)
        
        #Same for uncertainity
        self.dlg_base.browse_uncertainity_csv.clicked.connect(self.browse_csv_uncertainity)
        
        #Add inputs to OAT results dialog
        self.dlg_base.csv_results_oat.textChanged.connect(self.add_inputs_oat_results)
        
        #Update uncertainity graph
        self.dlg_base.csv_results_uncertainity.textChanged.connect(self.update_graph_uncertainity)
    
    
    def update_buffer_length_table(self):
        """Method to update the buffer segment table when buffer length is changed"""
        #We obtain information of ikw file
        ikw = self.obtain_direction_vfsmod(self.dlg_base.line_overland.text())
        if os.path.exists(ikw):
            with open(ikw, "r") as archivo:
                lineas = archivo.readlines()
            
            number_segments = int(lineas[3])
            df = pd.DataFrame(data = {"Distance":[list(map(float, lineas[x].split()))[0] for x in range(4,4+number_segments)],
                                 "Manning":[list(map(float, lineas[x].split()))[1] for x in range(4,4+number_segments)],
                                 "Slope":[list(map(float, lineas[x].split()))[2] for x in range(4,4+number_segments)]})
        else:
            df = self.original_buffer_segments
            
        actual_length = max(df["Distance"])
        length_to_change = float(self.dlg_overland_flow.length.text())
        if length_to_change <= actual_length:
            df = df[df["Distance"]<=length_to_change]
            df.loc[df.index[-1], "Distance"] = length_to_change
        else:
            df.loc[df.index[-1], "Distance"] = length_to_change
        
        #Add the information to the table
        self.dlg_buffer_segment.tableWidget.itemChanged.disconnect(self.update_buffer_segment_graph) #disconnect. if not each time there is a row update it will be connected
        self.dlg_buffer_segment.tableWidget.setRowCount(0)
        self.dlg_buffer_segment.tableWidget.setRowCount(len(df))
        for fila in range(len(df)):
            for columna in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[fila,columna]))
                self.dlg_buffer_segment.tableWidget.setItem(fila, columna, item)
                item.setTextAlignment(Qt.AlignCenter)
        
        #Connect again
        self.dlg_buffer_segment.tableWidget.itemChanged.connect(self.update_buffer_segment_graph)
        #Update graph
        if hasattr(self, 'ax_buffer_segment'):
            self.update_buffer_segment_graph()
    
    def set_working_directory(self):
        """Method to set the directory of the project"""
        self.working_directory = self.dlg_base.working_directory_vfsmod.text()
    
    def change_rows_water_quality(self):
        """Method to add/delete rows from the water quality dialog"""
        try:
            num_rows = int(self.dlg_water_quality.days.text())
            self.dlg_water_quality.tableWidget.setRowCount(num_rows)
            for row in range(num_rows):
                item = QTableWidgetItem(str(row+1))
                self.dlg_water_quality.tableWidget.setItem(row, 0, item) 
        except:
            pass
        
    def hide_mass_balance_frame(self):
        """Method to show/hide frame for mass balance calculation in water quality"""
        if self.dlg_water_quality.calculation.currentIndex() == 0:
            self.dlg_water_quality.frame_5.hide()
        else: 
            self.dlg_water_quality.frame_5.show()
    
    def add_inputs_oat_results(self):
        """Method to add inputs into oat sensitivity results"""
        #First delete previous layout if it exits
        if self.dlg_base.inputs_oat.layout() is not None:
            for i in reversed(range(self.dlg_base.inputs_oat.layout().count())): 
                widget = self.dlg_base.inputs_oat.layout().itemAt(i).widget()
                if widget is not None: 
                    widget.deleteLater()  # Eliminar el widget
            self.dlg_base.inputs_oat.layout().deleteLater()
        #Then create
        if os.path.exists(self.obtain_direction_vfsmod(self.dlg_base.csv_results_oat.text())):
            try:
                layout = QVBoxLayout()
                # Crear un QLabel con el texto que quieras
                label = QLabel("Inputs")

                # Añadir el QLabel al layout
                layout.addWidget(label)
                
                #Name of inputs
                with open(self.obtain_direction_vfsmod(self.dlg_base.csv_results_oat.text()), mode='r', encoding='utf-8') as file:
                    lines = file.read().splitlines()
                inputs = lines[1].split(":")[-1].split(",")
                
                self.dictionary_radio_inputs = {}
                # Crear y añadir varios QRadioButton
                for opcion in inputs:
                    radio_button = QRadioButton(opcion)
                    #Connect funciton but only one time
                    radio_button.toggled.connect(lambda checked, rb=radio_button: self.update_sensitity_graph_oat() if checked else None)
                    self.dictionary_radio_inputs[radio_button] = opcion
                    layout.addWidget(radio_button)
                
                #add spacer
                spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
                layout.addItem(spacer)

                # Establecer el layout en el frame `self.dlg_base.inputs_oat`
                self.dlg_base.inputs_oat.setLayout(layout)
            except:
                pass
    
    
    def show_graph_sensitivity_oat(self):   
        """Method to add OAT sensitivity analysis graph"""
        if not hasattr(self, 'canvas_sensitivity_graph_oat'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_sensitivity_graph_oat = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_base.frame_24)
            self.dlg_base.frame_24.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_sensitivity_graph_oat)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_sensitivity_graph_oat.figure.clear()
        
        #Then we create the graph
        self.ax_oat = self.canvas_sensitivity_graph_oat.figure.subplots()
         
    def update_sensitity_graph_oat(self):
        if len(self.dictionary_radio_inputs)>1:
            for i in self.dictionary_radio_inputs:
                if i.isChecked():
                    input_parameter = self.dictionary_radio_inputs[i]
                    break
        #Warning messages
        ruta = self.obtain_direction_vfsmod(self.dlg_base.csv_results_oat.text())
        if os.path.exists(ruta):
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            #If the csv is not of a OAT sensitivity analysis then give error
            if lineas[0]!="OAT sensitivity results" + '\n':
                self.warning_message("Please select a csv file that contains OAT sensitivity analysis results")
                return
                
            #Clear graph before drawing
            self.ax_oat.clear()
            
            #Obtain data 
            with open(self.obtain_direction_vfsmod(self.dlg_base.csv_results_oat.text()), mode='r', encoding='utf-8') as file:
                lines = file.read().splitlines()
            # Ignorar la primera línea ("OAT sensitivity results")
            lines = lines[1:]
            for i in range(len(lines)):
                if lines[i] == f"{input_parameter} results":
                    columns = lines[i+1].split(",")
                    rows = []
                    for k in range(i+2,len(lines)):
                        if lines[k][:2]=="--":
                            break
                        rows.append(lines[k].split(","))
                    break
            df = pd.DataFrame(rows, columns=columns)
            
            #Get output
            if self.dlg_base.runoff_source_mm_3.isChecked():output_column = "Total Runoff from source (mm)"
            elif self.dlg_base.runoff_source_m3_3.isChecked():output_column = "Total Runoff from Source (m3)"
            elif self.dlg_base.runoff_filter_mm_3.isChecked():output_column = "Total Runoff out from Filter (mm)"
            elif self.dlg_base.runoff_filter_m3_3.isChecked():output_column = "Total Runoff out from Filter (m3)"
            elif self.dlg_base.infiltration_filter_m3_3.isChecked():output_column = "Total Infiltration in Filter (m3)"
            elif self.dlg_base.sediment_input_3.isChecked():output_column = "Mass Sediment Input to Filter (kg)"
            elif self.dlg_base.concentration_sediment_3.isChecked():output_column = "Concentration Sediment in Runoff from source Area (g/L)"
            elif self.dlg_base.sediment_output_3.isChecked():output_column = "Mass Sediment Output from Filter (kg)"
            elif self.dlg_base.sediment_runoff_exit_3.isChecked():output_column = "Concentration Sediment in Runoff exiting the Filter (g/L)"
            elif self.dlg_base.sediment_delivery_3.isChecked():output_column = "Sediment Delivery Ratio"
            elif self.dlg_base.runoff_delivery_3.isChecked():output_column = "Runoff Delivery Ratio"
            
            x = [float(x) for x in df[input_parameter]]
            y = [float(x) for x in df[output_column]]
            
            base_input = x[0]
            base_output = y[0]
            
            unique_pairs = {}
            for xi, yi in zip(x, y):
                if xi not in unique_pairs:
                    unique_pairs[xi] = yi

            # Extraer los pares únicos y ordenarlos por el valor de x
            x_sorted = sorted(unique_pairs.keys())
            y_sorted = [unique_pairs[xi] for xi in x_sorted]
            
            #Input output graph
            if self.dlg_base.input_output.isChecked():
                #Create graph
                self.ax_oat.plot(x_sorted, y_sorted, marker='o', linestyle='-', color='b')
                #Separador de miles
                def formato_con_separador(valor, pos):
                    if max(list(y_sorted))>10:
                        return "{:,.0f}".format(valor)
                    else:
                        return "{:,.2f}".format(valor)
                self.ax_oat.xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                self.ax_oat.yaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                #Labels
                self.ax_oat.set_xlabel(input_parameter,size = 14,family="arial",weight = "bold",color = "black")
                self.ax_oat.set_ylabel(output_column,size = 14,family="arial",weight = "bold",color = "black")
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph_oat.draw()
            
            #Absolute sensitivity graph
            elif self.dlg_base.absolute.isChecked():
                absolute_sensitivity = []
                for i in range(len(x_sorted)-1):
                    absolute_sensitivity.append((y_sorted[i+1]-y_sorted[i])/(x_sorted[i+1]-x_sorted[i]))
                #Create graph
                self.ax_oat.plot(x_sorted[:-1], absolute_sensitivity, marker='o', linestyle='-', color='b')
                #Separador de miles
                def formato_con_separador(valor, pos):
                    if max(list(absolute_sensitivity))>10:
                        return "{:,.0f}".format(valor)
                    else:
                        return "{:,.2f}".format(valor)
                self.ax_oat.xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                self.ax_oat.yaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                #Labels
                self.ax_oat.set_xlabel(input_parameter,size = 14,family="arial",weight = "bold",color = "black")
                self.ax_oat.set_ylabel(f"Absolute sensitivity\n{output_column}",size = 14,family="arial",weight = "bold",color = "black")
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph_oat.draw()
            
            #Relative sensitivity graph respect to base
            elif self.dlg_base.relative_base.isChecked():
                relative_sensitivity = []
                for i in range(len(x_sorted)-1):
                    try:
                        relative_sensitivity.append((y_sorted[i+1]-base_output)/(x_sorted[i+1]-base_input)*(base_input/base_output))
                    except ZeroDivisionError:
                        relative_sensitivity.append(np.nan)
                #Create graph
                self.ax_oat.plot(x_sorted[:-1], relative_sensitivity, marker='o', linestyle='-', color='b')
                #Separador de miles
                def formato_con_separador(valor, pos):
                    if max(list(relative_sensitivity))>10:
                        return "{:,.0f}".format(valor)
                    else:
                        return "{:,.2f}".format(valor)
                self.ax_oat.xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                self.ax_oat.yaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                #Labels
                self.ax_oat.set_xlabel(input_parameter,size = 14,family="arial",weight = "bold",color = "black")
                self.ax_oat.set_ylabel(f"Base relative sensitivity\n{output_column}",size = 14,family="arial",weight = "bold",color = "black")
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph_oat.draw()
            
            
            #Relative sensitivity graph
            elif self.dlg_base.relative_sensitivity.isChecked():
                relative_sensitivity = []
                for i in range(len(x_sorted)-1):
                    try:
                        relative_sensitivity.append((y_sorted[i+1]-y_sorted[i])/(x_sorted[i+1]-x_sorted[i])*(x_sorted[i]/y_sorted[i]))
                    except ZeroDivisionError:
                        relative_sensitivity.append(np.nan)
                #Create graph
                self.ax_oat.plot(x_sorted[:-1], relative_sensitivity, marker='o', linestyle='-', color='b')
                #Separador de miles
                def formato_con_separador(valor, pos):
                    if max(list(relative_sensitivity))>10:
                        return "{:,.0f}".format(valor)
                    else:
                        return "{:,.2f}".format(valor)
                self.ax_oat.xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                self.ax_oat.yaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                #Labels
                self.ax_oat.set_xlabel(input_parameter,size = 14,family="arial",weight = "bold",color = "black")
                self.ax_oat.set_ylabel(f"Relative sensitivity\n{output_column}",size = 14,family="arial",weight = "bold",color = "black")
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph_oat.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph_oat.draw()
    
    def show_graph_sensitivity_uncertainity(self):
        """Method to add the graph of sensitivity analysis for uncertainity"""
        if not hasattr(self, 'canvas_uncertainity_graph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_uncertainity_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_base.frame_68)
            self.dlg_base.frame_68.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_uncertainity_graph)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_uncertainity_graph.figure.clear()
    
    
    def update_graph_uncertainity(self):
        """Mehtod to update uncertainity graph"""
        #Warning messages
        ruta = self.obtain_direction_vfsmod(self.dlg_base.csv_results_uncertainity.text())
        if os.path.exists(ruta):
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            #If the csv is not of a Uncertainity sensitivity analysis then give error
            if lineas[0]!="Uncertainity analysis results" + '\n':
                self.warning_message("Please select a csv file that contains Uncertainity analysis results")
                return
                
            #Clear graph before drawing
            #Create and clear axis before drawing
            self.canvas_uncertainity_graph.figure.clear()
            self.ax_uncertainity = self.canvas_uncertainity_graph.figure.subplots(1,2)
            
            #Obtain data 
            with open(ruta, "r") as archivo:
                 lines = archivo.readlines()
            # Ignorar la primera línea ("Uncertainity analysis results")
            parameters = lines[1].split(":")[1].split(",")
            columns = [x.replace('\n', '') for x in lines[2].split(",")]
            rows = []
            for i in range(3,len(lines)):
                rows.append([float(x) for x in lines[i].split(",")])

            df = pd.DataFrame(rows, columns=columns)
            
            #Delete rows with error
            df = df[df.Error==0]
            
            #Get output
            if self.dlg_base.runoff_source_mm_4.isChecked():output_column = "Total Runoff from source (mm)"
            elif self.dlg_base.runoff_source_m3_4.isChecked():output_column = "Total Runoff from Source (m3)"
            elif self.dlg_base.runoff_filter_mm_4.isChecked():output_column = "Total Runoff out from Filter (mm)"
            elif self.dlg_base.runoff_filter_m3_4.isChecked():output_column = "Total Runoff out from Filter (m3)"
            elif self.dlg_base.infiltration_filter_m3_4.isChecked():output_column = "Total Infiltration in Filter (m3)"
            elif self.dlg_base.sediment_input_4.isChecked():output_column = "Mass Sediment Input to Filter (kg)"
            elif self.dlg_base.concentration_sediment_4.isChecked():output_column = "Concentration Sediment in Runoff from source Area (g/L)"
            elif self.dlg_base.sediment_output_4.isChecked():output_column = "Mass Sediment Output from Filter (kg)"
            elif self.dlg_base.sediment_runoff_exit_4.isChecked():output_column = "Concentration Sediment in Runoff exiting the Filter (g/L)"
            elif self.dlg_base.sediment_delivery_4.isChecked():output_column = "Sediment Delivery Ratio"
            elif self.dlg_base.runoff_delivery_4.isChecked():output_column = "Runoff Delivery Ratio"
            
            y = [float(x) for x in df[output_column]]
            
            bins = 30
            self.ax_uncertainity[0].hist(y, bins=bins, edgecolor='black')
            #Separador de miles
            def formato_con_separador(valor, pos):
                if max(list(y))>10:
                    return "{:,.0f}".format(valor)
                else:
                    return "{:,.2f}".format(valor)
            self.ax_uncertainity[0].xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
            #Labels
            self.ax_uncertainity[0].set_xlabel(output_column,size = 12,family="arial",weight = "bold",color = "black")
            self.ax_uncertainity[0].set_ylabel("Frequency",size = 12,family="arial",weight = "bold",color = "black")
            
            ax2 = self.ax_uncertainity[0].twinx()
            x_sorted = np.sort(y)
            # Calcular la frecuencia acumulativa
            y = np.arange(1, len(x_sorted) + 1) / len(x_sorted)
            # Graficar la frecuencia acumulativa con líneas
            ax2.plot(x_sorted, y, linestyle='-', marker='',color = "black")
            ax2.set_ylabel("Cumulative Frequency",size = 12,family="arial",weight = "bold",color = "black")
            #Put ax2 in the front
            self.ax_uncertainity[0].set_zorder(1)
            ax2.set_zorder(2)
            
            #Box plot
            self.ax_uncertainity[1].boxplot([float(x) for x in df[output_column]])
            self.ax_uncertainity[1].set_xticks([])
            # Añadir título y etiquetas
            self.ax_uncertainity[1].set_ylabel(output_column,size = 12,family="arial",weight = "bold",color = "black")
            
            
            #Add table
            table = self.dlg_base.tableWidget
            table.setRowCount(1)
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["25th percentile","50th percentile","75th percentile","Average","Kurtosis","Skewness"])
            #Add values
            data = [float(x) for x in df[output_column]]
            values = [np.percentile(data, 25),np.percentile(data, 50),np.percentile(data, 75),
                np.mean(data),stats.kurtosis(data),stats.skew(data)]
            for k,i in enumerate(values):
                item = QTableWidgetItem(str(round(i,2)))
                table.setItem(0,k,item)
                item.setTextAlignment(Qt.AlignCenter)
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_uncertainity_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_uncertainity_graph.figure.subplots_adjust(left=0.1, bottom=0.2)
            #Draw canvas
            self.canvas_uncertainity_graph.draw()
    
    def add_base_value_dialog_oat(self):
        """Method to add the base value to the dialog of sensitivity when using OAT"""
        if self.dlg_base.oat.isChecked() and self.dlg_base.parameter_name.text()!="":
            parameter = self.dlg_base.parameter_name.text()
            extension = self.sensitivity_parameters[parameter][0]
            row = self.sensitivity_parameters[parameter][1]
            column = self.sensitivity_parameters[parameter][2]
            process = self.sensitivity_parameters[parameter][3]
            
            if extension == "inp":
                path = self.obtain_direction_vfsmod(self.dlg_base.uh_file_sensitivity.text())
            else:
                path = self.obtain_direction_vfsmod(self.dlg_base.vfs_file_sensitivity.text())
            
            if os.path.exists(path) and os.path.isfile(path):
                #First we open the file and obtain the direction of the copying file
                with open(path, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==extension:
                        path_input = i.split("=")[-1]
                if not os.path.isabs(path_input): #relative path
                    path_input = os.path.join(os.path.dirname(path), path_input)
                path_input = path_input.replace("\n", "") #take out the line jumps
                
                
                if os.path.exists(path_input):  
                    with open(path_input, 'r') as file:
                        lineas = file.readlines()
                    if parameter == "Filter Manning n (RNA s/m^1/3)" or parameter == "Average Filter Slope":
                        number_segments = int(lineas[3])
                        df = pd.DataFrame(data = {"Distance":[list(map(float, lineas[x].split()))[0] for x in range(4,4+number_segments)],
                                                 "Roughness":[list(map(float, lineas[x].split()))[1] for x in range(4,4+number_segments)],
                                                 "Slope":[list(map(float, lineas[x].split()))[2] for x in range(4,4+number_segments)]})
                        if parameter == "Filter Manning n (RNA s/m^1/3)":
                            value = sum(df["Roughness"])/len(df)
                        elif parameter == "Average Filter Slope":
                            value = round(sum(df["Slope"])/len(df),4)
                    else:
                        value = self.add_values_dialog(lineas,row,column,self.dlg_base.rainfall,retrieve = True)
                        
                    self.dlg_base.first.setText(str(value))

                    
                    
                
    def disable_storm_line_edits_design(self):
        """Method to enable disable lineEdits in designe"""
        storms_time = [self.dlg_base.lineEdit_4,self.dlg_base.lineEdit_5,self.dlg_base.lineEdit_6,self.dlg_base.lineEdit_7,
                self.dlg_base.lineEdit_8,self.dlg_base.lineEdit_9,self.dlg_base.lineEdit_10]
        storms_increment = [self.dlg_base.start,self.dlg_base.end,self.dlg_base.increment]
        vfs = [self.dlg_base.lower_length,self.dlg_base.upper_length,self.dlg_base.increment_length]
        spacing = [self.dlg_base.lower_spacing,self.dlg_base.upper_spacing,self.dlg_base.increment_spacing]
        #Storm
        if self.dlg_base.specific.isChecked():
            for i in storms_time:
                i.setEnabled(True)
                i.setStyleSheet("background-color: #f0f0f0;")
            for k in storms_increment:
                k.setEnabled(False)
                k.setStyleSheet("background-color: #d9d9d9;")
        else:
            for i in storms_time:
                i.setEnabled(False)
                i.setStyleSheet("background-color: #d9d9d9;")
            for k in storms_increment:
                k.setEnabled(True)
                k.setStyleSheet("background-color: #f0f0f0;")
        #Vegetation and spacing
        if self.dlg_base.design_length.isChecked():
            for i in vfs:
                i.setEnabled(True)
                i.setStyleSheet("background-color: #f0f0f0;")
            for k in spacing:
                k.setEnabled(False)
                k.setStyleSheet("background-color: #d9d9d9;")
        elif self.dlg_base.design_spacing.isChecked():
            for i in vfs:
                i.setEnabled(False)
                i.setStyleSheet("background-color: #d9d9d9;")
            for k in spacing:
                k.setEnabled(True)
                k.setStyleSheet("background-color: #f0f0f0;")
        else:
            for i in vfs:
                i.setEnabled(False)
                i.setStyleSheet("background-color: #d9d9d9;")
            for k in spacing:
                k.setEnabled(False)
                k.setStyleSheet("background-color: #d9d9d9;")
    
    def show_calibration_buttons(self):
        """Method to add buttons to show calibration buttons and to show the dialog"""
        #For the two frames
        if self.dlg_base.frame_16.isVisible():
            self.dlg_base.frame_16.setVisible(False)
            self.dlg_base.frame_18.setVisible(False)
        else:
            self.dlg_base.frame_16.setVisible(True)
            self.dlg_base.frame_18.setVisible(True)
            #Show dialog
            if self.dlg_base.calibration_hydrograph.isChecked():
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_hydrograph)
            else:
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_calibration_sedimentograph)
                

    def show_design_buttons(self):
        """Method to add buttons to show design buttons and to show the dialog"""
        #For the two frames
        if self.dlg_base.frame_52.isVisible():
            self.dlg_base.frame_52.setVisible(False)
            self.dlg_base.frame_53.setVisible(False)
        else:
            self.dlg_base.frame_52.setVisible(True)
            self.dlg_base.frame_53.setVisible(True)
            #Show dialog
            if self.dlg_base.simple_design.isChecked():
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_simple)
            else:
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_design_advanced)
                
    def show_sensitivity_buttons(self):
        """Method to add buttons to show sensitivity buttons and to show the dialog"""
        #For the two frames
        if self.dlg_base.frame_54.isVisible():
            self.dlg_base.frame_54.setVisible(False)
            self.dlg_base.frame_55.setVisible(False)
        else:
            self.dlg_base.frame_54.setVisible(True)
            self.dlg_base.frame_55.setVisible(True)
            #Show dialog
            if self.dlg_base.sensitivity_parameters.isChecked():
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sensitivity_analysis)
            else:
                self.dlg_base.stackedWidget.setCurrentWidget(self.dlg_base.page_sobol_results)
    
    def add_values_vfs_outputs_dialog(self):
        """Method to add filepaths of prj"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_project_vfsmod.text())
        dictionary = {"ikw":self.dlg_base.line_overland,"iso":self.dlg_base.line_infiltration,"igr":self.dlg_base.line_buffer,
            "isd":self.dlg_base.line_incoming,"irn":self.dlg_base.line_storm,"iro":self.dlg_base.line_source,"iwq":self.dlg_base.line_water,
            "og1":self.dlg_base.line_sediment,"og2":self.dlg_base.line_flow,"ohy":self.dlg_base.line_hydrograph_2,
            "osm":self.dlg_base.line_waterland,"osp":self.dlg_base.line_overall,"owq":self.dlg_base.line_quality}
        #Add text
        water_quality = False
        if os.path.exists(path):  
            try:
                with open(path, 'r') as file:
                    lineas = file.readlines() 
                for i in lineas:
                    if i[:3] in list(dictionary.keys()):
                        ikw = i.split("=")[-1]
                        if not os.path.isabs(ikw): #relative path
                            ikw = os.path.join(os.path.dirname(ruta), ikw)
                        ikw = ikw.replace("\n", "") #take out the line jumps
                        text = os.path.relpath(ikw, self.dlg_base.working_directory_vfsmod.text())
                        dictionary[i[:3]].setText(text)
                    if i[:3] == "iwq":
                        water_quality = True
                        
            except:
                pass
                
        #Check water quality
        if water_quality:
            self.dlg_base.water_quality.setChecked(True)
            
        
    def add_values_uh_outputs_dialog(self):
        """Method to add .lis output paths and inp to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.uh_file.text())
        dictionary = {"inp":self.dlg_base.uh_input,"iro":self.dlg_base.line_hydrograph,"irn":self.dlg_base.line_hyetograph,
            "isd":self.dlg_base.line_sedimentograph,"out":self.dlg_base.line_output_1,"hyt":self.dlg_base.line_output_2}

        if os.path.exists(path):  
            try:
                with open(path, 'r') as file:
                    lineas = file.readlines() 
                for i in lineas:
                    if i[:3] in list(dictionary.keys()):
                        ikw = i.split("=")[-1]
                        if not os.path.isabs(ikw): #relative path
                            ikw = os.path.join(os.path.dirname(ruta), ikw)
                        ikw = ikw.replace("\n", "") #take out the line jumps
                        text = os.path.relpath(ikw, self.dlg_base.working_directory_vfsmod.text())
                        dictionary[i[:3]].setText(text)
            except:
                pass
    
    def add_values_inp_dialog(self):
        """Method to add values of the inp to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.uh_input.text())
        #Disconnect storm type
        self.dlg_base.storm_type.currentIndexChanged.disconnect(self.user_defined_storm_type)
        if os.path.exists(path):  
            try:
                with open(path, 'r') as file:
                    lineas = file.readlines()  
                #Rainfall
                self.add_values_dialog(lineas,0,0,self.dlg_base.rainfall)
                #Curve number
                self.add_values_dialog(lineas,0,1,self.dlg_base.curve_number)
                #Storm duration
                self.add_values_dialog(lineas,0,4,self.dlg_base.storm_duration)
                #Storm type
                storm_type = int(self.add_values_dialog(lineas,0,3,self.dlg_base.storm_type,True))
                self.dlg_base.storm_type.setCurrentIndex(storm_type-1)
                #Source Length
                self.add_values_dialog(lineas,0,5,self.dlg_base.length_source)
                #Slope
                self.add_values_dialog(lineas,0,6,self.dlg_base.slope_source)
                #Area
                self.add_values_dialog(lineas,0,2,self.dlg_base.area_source)
                #K
                self.add_values_dialog(lineas,3,0,self.dlg_base.k_factor)
                #Organic
                self.add_values_dialog(lineas,5,0,self.dlg_base.organic_matter)
                #C
                self.add_values_dialog(lineas,3,1,self.dlg_base.crop_factor)
                #Soil Type
                soil_type = lineas[2][:-30].strip()
                soil_index = ["Clay","Silty clay","Sandy clay","Silty clay loam","Clay loam","Sandy clay loam","Silt","Silt loam","Loam",
                    "Very fine sandy loam","Fine sandy loam","Sandy loam","Coarse sandy loam","Loamy very fine sand","Loamy fine sandy",
                    "Loamy sand","Loamy coarse sand","Very fine sandy","Fine sand","Sand","Coarse sand"].index(soil_type)
                self.dlg_base.soil_type.setCurrentIndex(soil_index)
                #dp
                self.add_values_dialog(lineas,3,3,self.dlg_base.particle_diameter)
                #P
                self.add_values_dialog(lineas,3,2,self.dlg_base.practice_factor)
                #R
                r = int(self.add_values_dialog(lineas,4,0,self.dlg_base.williams,True))
                if r==1: self.dlg_base.williams.setChecked(True)
                elif r==2: self.dlg_base.creams_gleams.setChecked(True)
            
            except:
                pass
        #Connect storm type
        self.dlg_base.storm_type.currentIndexChanged.connect(self.user_defined_storm_type)
    
    def dlg_overland_flow_show(self):
        """Method to add values of the ikw to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_overland.text())
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                    lineas = file.readlines()
                #Simulation title
                self.add_values_dialog(lineas,0,0,self.dlg_overland_flow.simulation_title)
                #Length
                self.add_values_dialog(lineas,2,0,self.dlg_overland_flow.length)
                #Width
                self.add_values_dialog(lineas,1,0,self.dlg_overland_flow.width)
                #Nodes
                self.add_values_dialog(lineas,2,1,self.dlg_overland_flow.nodes)
                #Time weight
                self.add_values_dialog(lineas,2,2,self.dlg_overland_flow.time)
                #Number element nodal
                self.add_values_dialog(lineas,2,5,self.dlg_overland_flow.nodal)
                #Petrov
                self.add_values_dialog(lineas,2,7,self.dlg_overland_flow.petrov)
                #Courant
                self.add_values_dialog(lineas,2,3,self.dlg_overland_flow.courant)
                #Maximum iterations
                self.add_values_dialog(lineas,2,4,self.dlg_overland_flow.maximum)
                #Output element
                self.add_values_dialog(lineas,2,6,self.dlg_overland_flow.output)
                
                #Update table of segments
                number_segments = int(lineas[3])
                df = pd.DataFrame(data = {"Distance":[list(map(float, lineas[x].split()))[0] for x in range(4,4+number_segments)],
                                     "Roughness":[list(map(float, lineas[x].split()))[1] for x in range(4,4+number_segments)],
                                     "Slope":[list(map(float, lineas[x].split()))[2] for x in range(4,4+number_segments)]})
                
                self.dlg_buffer_segment.tableWidget.itemChanged.disconnect(self.update_buffer_segment_graph)
                self.dlg_buffer_segment.tableWidget.setRowCount(len(df))
                for fila in range(len(df)):
                    for columna in range(len(df.columns)):
                        item = QTableWidgetItem(str(df.iloc[fila,columna]))
                        self.dlg_buffer_segment.tableWidget.setItem(fila, columna, item)
                        item.setTextAlignment(Qt.AlignCenter)
                
                self.dlg_buffer_segment.tableWidget.itemChanged.connect(self.update_buffer_segment_graph)
                self.update_buffer_segment_graph()
                
            except:
                pass
        #Show graph
        self.dlg_overland_flow.show()
                
    
    def dlg_infiltration_soil_show(self):
        """Method to add values of the iso to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_infiltration.text())
        if os.path.exists(path):
            with open(path, 'r') as file:
                lineas = file.readlines()
            
            #K
            self.add_values_dialog(lineas,0,0,self.dlg_infiltration_soil.line_vertical_ms)
            #Average suction
            self.add_values_dialog(lineas,0,1,self.dlg_infiltration_soil.line_average)
            #Initial water content
            self.add_values_dialog(lineas,0,3,self.dlg_infiltration_soil.line_initial)
            #Saturated water content
            self.add_values_dialog(lineas,0,2,self.dlg_infiltration_soil.line_saturated)
            #Maximum surface storage
            self.add_values_dialog(lineas,0,4,self.dlg_infiltration_soil.line_maximum)
            #Fraction of the filter
            self.add_values_dialog(lineas,0,5,self.dlg_infiltration_soil.line_fraction)
            
            #Shallow water table
            if len(lineas)>8:
                self.dlg_infiltration_soil.check_water_table.setChecked(True)
                #Water table depth 
                self.add_values_dialog(lineas,1,0,self.dlg_infiltration_soil.line_water_depth)
                #Soil Characteristic
                soil = int(self.add_values_dialog(lineas,2,0,self.dlg_infiltration_soil.line_vertical_ms,True))
                if soil ==1: self.dlg_infiltration_soil.radioButton_3.setChecked(True)
                elif soil ==2: self.dlg_infiltration_soil.radioButton_4.setChecked(True)
                #Hydraulic conductivity
                hydraulic=int(self.add_values_dialog(lineas,3,0,self.dlg_infiltration_soil.line_vertical_ms,True))
                if hydraulic ==1: self.dlg_infiltration_soil.radioButton_5.setChecked(True)
                elif hydraulic ==2: self.dlg_infiltration_soil.radioButton_6.setChecked(True)
                elif hydraulic ==3: self.dlg_infiltration_soil.radioButton_7.setChecked(True)
                
                #Soil curve parameters
                self.add_values_dialog(lineas,2,1,self.dlg_soil_curves.lineEdit)
                self.add_values_dialog(lineas,2,2,self.dlg_soil_curves.lineEdit_2)
                self.add_values_dialog(lineas,2,3,self.dlg_soil_curves.lineEdit_3)
                self.add_values_dialog(lineas,2,4,self.dlg_soil_curves.lineEdit_4)
                self.add_values_dialog(lineas,3,1,self.dlg_soil_curves.lineEdit_5)
                self.add_values_dialog(lineas,3,1,self.dlg_soil_curves.lineEdit_5)
                self.add_values_dialog(lineas,3,2,self.dlg_soil_curves.lineEdit_6)
                #Ansiotropy
                self.add_values_dialog(lineas,4,0,self.dlg_infiltration_soil.line_input)
                
            else:
                self.dlg_infiltration_soil.check_water_table.setChecked(False)
            
            
        #Show dialog
        self.dlg_infiltration_soil.show()
    
    def dlg_buffer_properties_show(self):
        """Method to add values of the igr to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_buffer.text())
        if os.path.exists(path):
            with open(path, 'r') as file:
                lineas = file.readlines()
            
            #Spacing
            self.add_values_dialog(lineas,0,0,self.dlg_buffer_properties.spacing_grass)
            #Height
            self.add_values_dialog(lineas,0,2,self.dlg_buffer_properties.height_grass)
            #Feedback
            self.add_values_dialog(lineas,0,4,self.dlg_buffer_properties.feedback)
            #Roughness-Grass
            self.add_values_dialog(lineas,0,1,self.dlg_buffer_properties.roughness_grass)
            #Roughness-Bare
            self.add_values_dialog(lineas,0,3,self.dlg_buffer_properties.roughness_bare)
            
        
        #Show dialog
        self.dlg_buffer_properties.show()
    
    def dlg_incoming_sediment_show(self):
        """Method to add values of the isd to the dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_incoming.text())
        if os.path.exists(path):
            with open(path, 'r') as file:
                lineas = file.readlines()
            #Concentration
            self.add_values_dialog(lineas,0,2,self.dlg_incoming_sediment.line_concentration)
            #Class
            self.add_values_dialog(lineas,0,0,self.dlg_incoming_sediment.line_class)
            #Diameter
            self.add_values_dialog(lineas,1,0,self.dlg_incoming_sediment.line_size)
            #Porosity
            self.add_values_dialog(lineas,0,3,self.dlg_incoming_sediment.line_porosity)
            #Portion
            self.add_values_dialog(lineas,0,1,self.dlg_incoming_sediment.line_portion)
            #Density
            self.add_values_dialog(lineas,1,1,self.dlg_incoming_sediment.line_sediment)
        
        #Show dialog
        self.dlg_incoming_sediment.show()
    
    def dlg_water_quality_show(self):
        """Method to add values of thw iwq file to dialog"""
        path = self.obtain_direction_vfsmod(self.dlg_base.line_water.text())
        if os.path.exists(path):
            with open(path, 'r') as file:
                lineas = file.readlines()
            #Direct input
            direct = int(self.add_values_dialog(lineas,1,0,self.dlg_water_quality.line_kd, True))
            if direct == 1: self.dlg_water_quality.check_direct.setChecked(False)
            else: self.dlg_water_quality.check_direct.setChecked(True)
            #Kd
            if direct == 0:
                self.add_values_dialog(lineas,1,1,self.dlg_water_quality.line_kd)
            #KOC
            if direct == 1:
                self.add_values_dialog(lineas,1,1,self.dlg_water_quality.line_koc)
                #OC
                self.add_values_dialog(lineas,1,2,self.dlg_water_quality.line_oc)
            #Clay content
            self.add_values_dialog(lineas,2,0,self.dlg_water_quality.line_clay)
            try: #if igr line does not exist
                #Pesticide mass balance
                igr = self.add_values_dialog(lineas,3,0,self.dlg_water_quality.calculation, True)
                self.dlg_water_quality.calculation.setCurrentIndex(int(igr))
                if int(igr)>0:
                    #Days
                    self.add_values_dialog(lineas,4,0,self.dlg_water_quality.days)
                    #Pesticide half life
                    self.add_values_dialog(lineas,4,1,self.dlg_water_quality.half_life)
                    #Top soil field capacity
                    self.add_values_dialog(lineas,4,2,self.dlg_water_quality.field_capacity)
                    #Pesticide mass entering filter
                    self.add_values_dialog(lineas,4,3,self.dlg_water_quality.mass)
                    #Surface mixing
                    self.add_values_dialog(lineas,4,4,self.dlg_water_quality.thickness)
                    #Air temperature and water content
                    temperatures = re.findall(r"[-+]?\d*\.\d+|\d+", lineas[5].split("(")[0])
                    water_contents = re.findall(r"[-+]?\d*\.\d+|\d+", lineas[6].split("(")[0])
                    self.dlg_water_quality.tableWidget.setRowCount(len(temperatures))
                    for fila in range(len(temperatures)):
                        #Day
                        item = QTableWidgetItem(str(fila+1))
                        self.dlg_water_quality.tableWidget.setItem(fila, 0, item)
                        item.setTextAlignment(Qt.AlignCenter)
                        #Temperature
                        item = QTableWidgetItem(temperatures[fila])
                        self.dlg_water_quality.tableWidget.setItem(fila, 1, item)
                        item.setTextAlignment(Qt.AlignCenter)
                        #Water content
                        item = QTableWidgetItem(water_contents[fila])
                        self.dlg_water_quality.tableWidget.setItem(fila, 2, item)
                        item.setTextAlignment(Qt.AlignCenter)
            except:
                pass
    
        #Show dialog
        self.dlg_water_quality.show()
        
    def add_values_dialog(self,lineas,row, column, lineEdit,retrieve =False):
        """Method to add values from the files to the dialog"""
        try:
            value = lineas[row].strip().split()[column]
            if not retrieve:
                lineEdit.setText(value)
            else:
                return value
        except:
            pass
    
    def show_og1_results(self):
        """Method to show og1 results"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_sediment.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_og1_results.textEdit.setPlainText(contenido)
        
        #Show dialog
        self.dlg_og1_results.show()
    
    def show_og2_results(self):
        """Method to show og2 results"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_flow.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_og2_results.textEdit.setPlainText(contenido)
        
        #Show dialog
        self.dlg_og2_results.show()
    
    def show_ohy_results(self):
        """Method to show ohy results"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_hydrograph_2.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_ohy_results.textEdit.setPlainText(contenido)
        
        #Show dialog
        self.dlg_ohy_results.show()
    
    def show_osm_results(self):
        """Method to show osm results"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_waterland.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_osm_results.textEdit.setPlainText(contenido)
        
        #Show dialog
        self.dlg_osm_results.show()
    
    def show_owq_results(self):
        """Method to show owq results"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_quality.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_owq_results.textEdit.setPlainText(contenido)
        
        #Show dialog
        self.dlg_owq_results.show()
    
    def show_owq_graph_balance(self):
        """Method to show the dialog with water quality balance graph"""
        #Obtain results
        ruta = self.obtain_direction_vfsmod(self.dlg_base.line_quality.text())
        if os.path.exists(ruta):
            #Obtain values
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            for i in range(len(lineas)):
                if lineas[i] == " Pesticide mass balance, degradation & remobilization\n":
                    fila = i
            #Function to obtain infomation of owq file
            def obtain_information(text):
                for i in range(fila,len(lineas)):
                    if lineas[i].split("=")[-1]==text+"\n":
                        return float(lineas[i].split("=")[0].split("m")[0])
            
            pesticide_input = obtain_information(" Pesticide input (mi)")
            pesticide_output = obtain_information(" Pesticide output (mo)")
            pesticide_outflow_solid = obtain_information(" Pesticide outflow in solid phase (mop)")
            pesticide_outflow_liquid = obtain_information(" Pesticide outflow in liquid phase (mod)")
            pesticide_trapped_vfs = obtain_information(" Pesticide trapped in VFS (mf)")
            pesticide_trapped_sediment = obtain_information(" Pesticide trapped with sediment (mfsed)")
            pesticide_trapped_mixing_layer = obtain_information(" Pesticide trapped in mixing layer (mfml)")
            pesticide_mixing_layer_last_event = obtain_information(" Pesticide in mixing layer from last event (mfml0)")
            total_surface_residue = obtain_information("mfml+mfsed+mfml0)")
            total_surface_residue_after_degradation = obtain_information(" Total surface residue after degradation (  3 days)")
            dissolved_surface_residue_after_degradation = obtain_information(" Dissolved surface residue after degradation (  3 days)")
            sorbed_surface_residue_after_degradation = obtain_information(" Sorbed surface residue after degradation (  3 days)")
            next_event_residue_remobilization = obtain_information("1)")
   
            name_variables = ["Pesticide input","Pesticide trapped in VFS","Pesticide trapped with sediment","Pesticide trapped in mixing layer",
                "Pesticide in mixing layer from last event","Total surface residue","Pesticide output","Pesticide outflow in solid phase",
                "Pesticide outflow in liquid phase","Total surface residue after degradation","Dissolved surface residue after degradation",
                "Sorbed surface residue after degradation","Next event residue remobilization"]
            value_variables = [pesticide_input,pesticide_trapped_vfs,pesticide_trapped_sediment,pesticide_trapped_mixing_layer,
                pesticide_mixing_layer_last_event,total_surface_residue,pesticide_output,pesticide_outflow_solid,
                pesticide_outflow_liquid,total_surface_residue_after_degradation,dissolved_surface_residue_after_degradation,
                sorbed_surface_residue_after_degradation,next_event_residue_remobilization]
            
            #Create graph
            #Add layout
            #If canvas exist then clear. If not then create it. 
            if not hasattr(self, 'canvas_owq_graph_balance'):
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_owq_graph_balance = FigureCanvas(plt.Figure(figsize=(15, 6)))
                
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_owq_graph_balance.frame)
                self.dlg_owq_graph_balance.frame.setLayout(layout)
                
                # Añadir el canvas al layout
                layout.addWidget(self.canvas_owq_graph_balance)
                
            else:
                # Si ya existe, simplemente limpiar el canvas
                self.canvas_owq_graph_balance.figure.clear()
        
            self.ax_owq_graph_balance= self.canvas_owq_graph_balance.figure.subplots()
        
            # Clear canvas
            self.ax_owq_graph_balance.clear()
            x = np.arange(len(name_variables))
            bars = self.ax_owq_graph_balance.bar(x, value_variables)
            
            #Add values to the top of the bars
            for bar in bars:
                yval = bar.get_height()
                self.ax_owq_graph_balance.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2),
                                           ha='center', va='bottom', fontsize=9, color='black',weight ="bold")

            # Rotar las etiquetas del eje x a 45 grados
            self.ax_owq_graph_balance.set_xticklabels(name_variables, rotation=45, ha='right')

            #Axis
            self.ax_owq_graph_balance.set_ylabel("Amount of pesticide (mg)",size = 10,family="arial",weight = "bold",color = "black")

            #X ticks
            self.ax_owq_graph_balance.set_xticklabels(name_variables)
            self.ax_owq_graph_balance.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            #Red line
            self.ax_owq_graph_balance.axvline(x=9.5, color='red', linestyle='--', linewidth=1.5) 

            #Thousand separator
            def xfunc(x,pos):
                s = '{:0,d}'.format(int(x))
                return s
            x_format = tkr.FuncFormatter(xfunc)
            self.ax_owq_graph_balance.yaxis.set_major_formatter(x_format)
            
            # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
            self.canvas_owq_graph_balance.figure.subplots_adjust(left=0.2, bottom=0.2)

            # Redraw the canvas
            self.canvas_owq_graph_balance.draw()
            
            #Show dialog
            self.dlg_owq_graph_balance.show()
            
            
    def show_owq_graph(self):
        """Method to show the dialog with water quality graph"""
        #Obtain results
        ruta = self.obtain_direction_vfsmod(self.dlg_base.line_quality.text())
        if os.path.exists(ruta):
            #Obtain values
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            valores = []
            for i in range(len(lineas)):
                if lineas[i] == "      Z(m)      C(mg/L)      S(mg/mg)\n":
                    for k in range(i+2,len(lineas)):
                        if len(lineas[k].split())==0 or (float(lineas[k].split()[1])==float(0)) and (float(lineas[k].split()[2])==float(0)):
                            break
                        else:
                            valores.append([float(x) for x in lineas[k].split()])

            df = pd.DataFrame(valores, columns=["z","c","s"])
            
            #Create graph
            #Add layout
            #If canvas exist then clear. If not then create it. 
            if not hasattr(self, 'canvas_owq_graph'):
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_owq_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_owq_graph.frame)
                self.dlg_owq_graph.frame.setLayout(layout)
                
                # Añadir el canvas al layout
                layout.addWidget(self.canvas_owq_graph)
                
            else:
                # Si ya existe, simplemente limpiar el canvas
                self.canvas_owq_graph.figure.clear()
        
            self.ax_owq_graph= self.canvas_owq_graph.figure.subplots(1,2)
        
            # Clear canvas
            self.ax_owq_graph[0].clear()
            self.ax_owq_graph[1].clear()
            
            #Create graph

            # Crear el gráfico de barras
            profundidad = df["z"]
            concentracion = df["c"]
            ratio = df["s"]
            # Invertir el eje y para que 0 esté arriba y aumentar hacia abajo
            self.ax_owq_graph[0].invert_yaxis()
            self.ax_owq_graph[1].invert_yaxis()

            # Graficar concentración vs. profundidad
            self.ax_owq_graph[0].plot(concentracion, profundidad, marker='o', color='b')
            self.ax_owq_graph[1].plot(ratio, profundidad, marker='o', color='b')

            # Etiquetas de los ejes
            self.ax_owq_graph[0].set_xlabel('Pore water concentration (mg/L)', color='black')
            self.ax_owq_graph[1].set_xlabel('Solid phase/liquid phase (mg/mg)', color='black')
            self.ax_owq_graph[0].set_ylabel('Depth (m)', color='black')

            # Colorear el área entre profundidad 0 y 0.06
            self.ax_owq_graph[0].axhspan(0, 0.02, facecolor='gray', alpha=0.3)  # Opacidad del rectángulo
            self.ax_owq_graph[1].axhspan(0, 0.02, facecolor='gray', alpha=0.3)  # Opacidad del rectángulo

            # Añadir texto "mixing layer" dentro del rectángulo con flechas más a la derecha
            self.ax_owq_graph[0].text(max(concentracion)*0.85, 0.01, 'Mixing Layer', fontsize=10, ha='center', va='center')
            self.ax_owq_graph[1].text(max(ratio)*0.85, 0.01, 'Mixing Layer', fontsize=10, ha='center', va='center')

            # Colorear los ejes en negro
            self.ax_owq_graph[0].spines['bottom'].set_color('black')
            self.ax_owq_graph[1].spines['bottom'].set_color('black')
            self.ax_owq_graph[0].spines['top'].set_color('black')
            self.ax_owq_graph[1].spines['top'].set_color('black')
            self.ax_owq_graph[0].spines['left'].set_color('black')
            self.ax_owq_graph[1].spines['left'].set_color('black')
            self.ax_owq_graph[0].spines['right'].set_color('black')
            self.ax_owq_graph[1].spines['right'].set_color('black')
            
            #Add line with value 1 
            self.ax_owq_graph[1].axvline(x=1, color='red', linestyle='--')
            ticks1 = self.ax_owq_graph[1].get_xticks()
            self.ax_owq_graph[1].set_xticklabels([f'{tick}' if tick != 1 else '1' for tick in ticks1])
            for tick in self.ax_owq_graph[1].get_xticklabels():
                if tick.get_text() == '1':
                    tick.set_color('red')

            #Title
            self.ax_owq_graph[0].set_title("Pore water concentration (mg/L)")
            self.ax_owq_graph[1].set_title("Solid phase/liquid phase (mg/mg)")
            
            # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
            self.canvas_owq_graph.figure.subplots_adjust(left=0.2, bottom=0.2)

            # Redraw the canvas
            self.canvas_owq_graph.draw()
            
            #Show dialog
            self.dlg_owq_graph.show()
    
    def show_runoff_results(self):
        """Method to show the dialog with runoff graph"""
        #Obtain results
        ruta = self.obtain_direction_vfsmod(self.dlg_base.line_overall.text())
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        #Function to obtain specific results form .osp file
        def obtain_result(string):
            for i in lineas:
                if i.split("=")[-1]==string:
                    for k in i.split("=")[0].split(" "):
                        try:
                            output = float(k)
                            break
                        except:
                            pass
            return output
        
        #Obtain results
        runoff_in = obtain_result(" Total Runoff from Source\n")
        rainfall = obtain_result(" Total Rainfall on Filter\n")
        infiltration = obtain_result(" Total Infiltration in Filter\n")
        runoff_out = obtain_result(" Total Runoff out from Filter\n")
        
        #Put graph
        #If canvas exist then clear. If not then create it. 
        if not hasattr(self, 'canvas_runoff_result'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_runoff_result = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_runoff_graph.frame)
            self.dlg_runoff_graph.frame.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_runoff_result)
            
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_runoff_result.figure.clear()
        
        self.ax_runoff_result= self.canvas_runoff_result.figure.subplots()
    
    
        # Clear canvas
        self.ax_runoff_result.clear()
        
        #Create plot
        # Datos para el gráfico
        names = ['Runoff In', 'Rainfall', 'Infiltration', 'Runoff Out']
        valores = [runoff_in, rainfall, infiltration, runoff_out]

        # Crear el gráfico de barras
        bars = self.ax_runoff_result.bar(names, valores)
        
        #Add values to the top of the bars
        for bar in bars:
            yval = bar.get_height()
            self.ax_runoff_result.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2),
                                       ha='center', va='bottom', fontsize=9, color='black',weight ="bold")

        
        #Axis
        self.ax_runoff_result.set_xlabel("Component",size = 10,family="arial",weight = "bold",color = "black")
        self.ax_runoff_result.set_ylabel("Amount (m$^{3}$)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        self.ax_runoff_result.tick_params(axis = "both",colors = "black",labelsize = 9)
        
        #Change y limit
        self.ax_runoff_result.set_ylim(0, max(valores)*1.1)

        #Thousand separator
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        self.ax_runoff_result.yaxis.set_major_formatter(x_format)
        
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        self.canvas_runoff_result.figure.subplots_adjust(left=0.2, bottom=0.2)

        # Redraw the canvas
        self.canvas_runoff_result.draw()
        
        #Show dialog
        self.dlg_runoff_graph.show()
    
    def show_sediment_results(self):
        """Method to show the dialog with runoff graph"""
        #Obtain results
        ruta = self.obtain_direction_vfsmod(self.dlg_base.line_overall.text())
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        #Function to obtain specific results form .osp file
        def obtain_result(string):
            for i in lineas:
                if i.split("=")[-1]==string:
                    for k in i.split("=")[0].split(" "):
                        try:
                            output = float(k)
                            break
                        except:
                            pass
            return output
        
        #Obtain results
        sediment_in = obtain_result(" Mass Sediment Input to Filter\n")
        retained = obtain_result(" Mass Sediment retained in Filter\n")
        infiltration = obtain_result(" Mass Sediment Output from Filter\n")
        
        #Put graph
        #If canvas exist then clear. If not then create it. 
        if not hasattr(self, 'canvas_sediment_result'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_sediment_result = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_sediment_graph.frame)
            self.dlg_sediment_graph.frame.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_sediment_result)
            
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_sediment_result.figure.clear()
        
        self.ax_sediment_result= self.canvas_sediment_result.figure.subplots()
    
    
        # Clear canvas
        self.ax_sediment_result.clear()
        
        #Create plot
        # Datos para el gráfico
        names = ['Sediment In', 'Sediment Retained', 'Sediment Out']
        valores = [sediment_in, retained, infiltration]

        # Crear el gráfico de barras
        bars = self.ax_sediment_result.bar(names, valores,color ="red")
        
        #Add values to the top of the bars
        for bar in bars:
            yval = bar.get_height()
            self.ax_sediment_result.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2),
                                       ha='center', va='bottom', fontsize=9, color='black',weight ="bold")

        
        #Axis
        self.ax_sediment_result.set_xlabel("Component",size = 10,family="arial",weight = "bold",color = "black")
        self.ax_sediment_result.set_ylabel("Amount (kg)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        self.ax_sediment_result.tick_params(axis = "both",colors = "black",labelsize = 9)
        
        #Change y limit
        self.ax_sediment_result.set_ylim(0, max(valores)*1.1)

        #Thousand separator
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        self.ax_sediment_result.yaxis.set_major_formatter(x_format)
        
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        self.canvas_sediment_result.figure.subplots_adjust(left=0.2, bottom=0.2)

        # Redraw the canvas
        self.canvas_sediment_result.draw()
        
        #Show dialog
        self.dlg_sediment_graph.show()
    
    def show_osp_results(self):
        """Method to show the osp results after the VFS execution"""
        #Obtain data
        filepath = self.obtain_direction_vfsmod(self.dlg_base.line_overall.text())
        with open(filepath, 'r') as file:
            lineas = file.readlines()
        
        condition=0
        parameters = []
        values = []
        for linea in lineas:
            parameter = '\n'.join(line.lstrip() for line in linea.split("=")[-1].splitlines())
            value =  '\n'.join(line.lstrip() for line in linea.split("=")[0].splitlines())
            if linea == "       Summary of Buffer Performance Indicators:\n":
                condition = 1
            if len(linea.split("="))==2 and condition ==1:
                parameters.append(parameter)
                values.append(value)
        
        #Add it to the table
        df = pd.DataFrame(data = {"parameters":parameters,"values":values})
        self.dlg_osp_results.tableWidget.setRowCount(len(parameters))
        for fila in range(len(parameters)):
            for columna in range(2):
                item = QTableWidgetItem(str(df.iloc[fila,columna]))
                self.dlg_osp_results.tableWidget.setItem(fila, columna, item)
                item.setTextAlignment(Qt.AlignCenter)
        #Modify the width of column
        self.dlg_osp_results.tableWidget.setColumnWidth(0, 300)
        #Show dialog
        self.dlg_osp_results.show()
    
    
    def show_hydrograph_vfsmod_graph(self):
        """Method to show hydrograph graph in vfsmod"""
        #If canvas exist then clear. If not then create it. 
        if not hasattr(self, 'canvas_vfsmod_hydrograph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_vfsmod_hydrograph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_vfsmod_hydrograph.frame_2)
            self.dlg_vfsmod_hydrograph.frame_2.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_vfsmod_hydrograph)
            
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_vfsmod_hydrograph.figure.clear()
        
        self.ax_vfsmod_hydrograph = self.canvas_vfsmod_hydrograph.figure.subplots()
        self.update_vfsmod_hydrograph_graph()
    
    
    def update_vfsmod_hydrograph_graph(self):
        """Method to update the hydrograph graph"""
        # Clear canvas
        self.ax_vfsmod_hydrograph.clear()
        # We obtain the data and create the graph
        row_count = self.dlg_vfsmod_hydrograph.tableWidget.rowCount()
        time = []
        discharge = []
        for row in range(row_count):
            time_item = self.dlg_vfsmod_hydrograph.tableWidget.item(row, 0)
            discharge_item = self.dlg_vfsmod_hydrograph.tableWidget.item(row, 1)
            
            if time_item and discharge_item:
                try: # if data is not added correctly
                    time.append(float(time_item.text()))
                    discharge.append(float(discharge_item.text()))
                except:
                    return
        
        #Creation of graph        
        self.ax_vfsmod_hydrograph.plot(time,discharge,color='blue', linewidth=2, marker='o', markersize=4)

        #Axis
        self.ax_vfsmod_hydrograph.set_xlabel("Time (s)",size = 10,family="arial",weight = "bold",color = "black")
        self.ax_vfsmod_hydrograph.set_ylabel("Discharge (m$^{3}$/s)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        self.ax_vfsmod_hydrograph.tick_params(axis = "both",colors = "black",labelsize = 9)

        #Thousand separator
        #Separador de miles
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        self.ax_vfsmod_hydrograph.xaxis.set_major_formatter(x_format)
        
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        self.canvas_vfsmod_hydrograph.figure.subplots_adjust(left=0.2, bottom=0.2)

        # Redraw the canvas
        self.canvas_vfsmod_hydrograph.draw()
    
    
    def show_hietograph_vfsmod_graph(self):
        """Method to show hyetograph graph in vfsmod"""
        #If canvas exist then clear. If not then create it. 
        if not hasattr(self, 'canvas_vfsmod_hyetograph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_vfsmod_hyetograph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_vfsmod_hyetograph.frame_3)
            self.dlg_vfsmod_hyetograph.frame_3.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_vfsmod_hyetograph)
            
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_vfsmod_hyetograph.figure.clear()
        
        self.ax_vfsmod_hyetograph = self.canvas_vfsmod_hyetograph.figure.subplots()
        self.update_vfsmod_hyetograph_graph()
    
    def update_vfsmod_hyetograph_graph(self):
        """Method to update the hyetograph graph"""
        # Clear canvas
        self.ax_vfsmod_hyetograph.clear()
        # We obtain the data and create the graph
        row_count = self.dlg_vfsmod_hyetograph.tableWidget.rowCount()
        time = []
        precipitation = []
        for row in range(row_count):
            time_item = self.dlg_vfsmod_hyetograph.tableWidget.item(row, 0)
            precipitation_item = self.dlg_vfsmod_hyetograph.tableWidget.item(row, 1)
            
            if time_item and precipitation_item:
                try: # if data is not added correctly
                    time.append(float(time_item.text()))
                    precipitation.append(float(precipitation_item.text()))
                except:
                    return
        
        #Creation of graph        
        widths = [time[i+1] - time[i] for i in range(len(time)-1)]
        self.ax_vfsmod_hyetograph.bar(time[:-1],precipitation[:-1],width=widths,color='blue', align='edge', edgecolor='black', linewidth=0.5)
        #Axis
        self.ax_vfsmod_hyetograph.set_xlabel("Time (s)",size = 10,family="arial",weight = "bold",color = "black")
        self.ax_vfsmod_hyetograph.set_ylabel("Precipitation (m/s)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        self.ax_vfsmod_hyetograph.tick_params(axis = "both",colors = "black",labelsize = 9)

        #Thousand separator
        #Separador de miles
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        self.ax_vfsmod_hyetograph.xaxis.set_major_formatter(x_format)
        
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        self.canvas_vfsmod_hyetograph.figure.subplots_adjust(left=0.2, bottom=0.2)

        # Redraw the canvas
        self.canvas_vfsmod_hyetograph.draw()
        
        
    def dlg_buffer_segment_show(self):
        """Method to show buffer segment dialog and update graph"""
        #If canvas exist then clear. If not then create it. 
        if not hasattr(self, 'canvas_buffer_segment'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_buffer_segment = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_buffer_segment.frame_2)
            self.dlg_buffer_segment.frame_2.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_buffer_segment)
            
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_buffer_segment.figure.clear()
        
        self.ax_buffer_segment = self.canvas_buffer_segment.figure.subplots()
        
        self.dlg_buffer_segment.show()
        self.update_buffer_segment_graph()
    
    
    def update_buffer_segment_graph(self):
        """Method to update the buffer segment graph"""
        # Clear canvas
        self.ax_buffer_segment.clear()

        # We obtain the data and create the graph
        row_count = self.dlg_buffer_segment.tableWidget.rowCount()
        distances = []
        roughnesses = []
        slopes = []
        for row in range(row_count):
            distance_item = self.dlg_buffer_segment.tableWidget.item(row, 0)
            roughness_item = self.dlg_buffer_segment.tableWidget.item(row, 1)
            slope_item = self.dlg_buffer_segment.tableWidget.item(row, 2)
            
            if distance_item and roughness_item and slope_item:
                try: # if data is not added correctly
                    distances.append(float(distance_item.text()))
                    roughnesses.append(float(roughness_item.text()))
                    slopes.append(float(slope_item.text()))
                except:
                    return

        # Convert to numpy arrays for easier manipulation
        distances = np.array(distances)
        roughnesses = np.array(roughnesses)
        slopes = np.array(slopes)
        slopes = -slopes  # Convert slopes to negative

        # Ensure distances start from 0
        distances = np.insert(distances, 0, 0)
        heights = np.zeros_like(distances)

        # Calculate heights based on slopes (assuming starting height is 0)
        for i in range(1, len(distances)):
            height_change = slopes[i-1] * (distances[i] - distances[i-1])
            heights[i] = heights[i-1] + height_change

        # Normalize roughnesses for coloring
        norm = plt.Normalize(roughnesses.min(), roughnesses.max())
        colors = plt.cm.viridis(norm(roughnesses))

        # Plot
        self.ax_buffer_segment.scatter(distances, heights, c='black', s=10)

        # Plot lines connecting the points
        # Colors of the lines based on roughness
        for i in range(len(distances) - 1):
            x_values = [distances[i], distances[i + 1]]
            y_values = [heights[i], heights[i + 1]]
            
            # Line color based on roughness of the segment
            segment_color = plt.cm.viridis(norm(roughnesses[i]))
            
            self.ax_buffer_segment.plot(x_values, y_values, color=segment_color, linestyle='-', alpha=0.7)

        # Legend
        if hasattr(self, 'cbar'):
            self.cbar.remove()

        # Get unique values and sort them
        unique_roughnesses = sorted(set(roughnesses))
        dummy_lines = [plt.Line2D([0], [0], color=plt.cm.viridis(norm(val)), linestyle='-', alpha=0.7) for val in unique_roughnesses]

        # Add the legend to the right of the plot
        self.ax_buffer_segment.legend(
            dummy_lines,
            [f'{val:.2e}' for val in unique_roughnesses],
            loc='center left',
            bbox_to_anchor=(0.55, 0.8),
            title='Roughness'
        )

        self.ax_buffer_segment.set_xlabel("Distance (m)", size=10, family="arial", weight="bold", color="black")
        self.ax_buffer_segment.set_ylabel("Elevation (m)", size=10, family="arial", weight="bold", color="black")

        # Adjust margins for more space
        self.canvas_buffer_segment.figure.subplots_adjust(wspace=0.4) # Spacing between two graphs
        self.canvas_buffer_segment.figure.subplots_adjust(left=0.2, bottom=0.2)

        # Redraw the canvas
        self.canvas_buffer_segment.draw()
        
        #Update buffer length in dialog
        try:
            if float(distances[-1]) != float(self.dlg_overland_flow.length.text()):
                self.dlg_overland_flow.length.setText(str(distances[-1]))
        except:
            pass

            
    def show_sedimentograph_results(self):
        """Method to show sedimentograph results after UH execution"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_sedimentograph.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_sedimentograph_output.textEdit.setPlainText(contenido)
        #Show dialog
        self.dlg_sedimentograph_output.show()
    
    def dlg_iro_results_show(self):
        """Method to show iro results after UH execution"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_hydrograph.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_iro_results.textEdit.setPlainText(contenido)
        #Show dialog
        self.dlg_iro_results.show()
    
    def dlg_irn_results_show(self):
        """Method to show irn results after UH execution"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_hyetograph.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_irn_results.textEdit.setPlainText(contenido)
        #Show dialog
        self.dlg_irn_results.show()
        
    def show_output_1_results(self):
        """Method to show sedimentograph results after UH execution"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_output_1.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_user_output_1.textEdit.setPlainText(contenido)
        #Show dialog
        self.dlg_user_output_1.show()
    
    def show_output_2_results(self):
        """Method to show sedimentograph results after UH execution"""
        #Add text
        path = self.obtain_direction_vfsmod(self.dlg_base.line_output_2.text())
        with open(path, 'r') as file:
            lineas = file.readlines()
        contenido = ""
        for i in lineas:
            contenido+=i
        self.dlg_user_output_2.textEdit.setPlainText(contenido)
        #Show dialog
        self.dlg_user_output_2.show()
        
        
    def set_timestep_non_editable(self):
        """Method to disable the ability to modify the timestep of the user defined storm and center items"""
        row_count = self.dlg_user_storm.tableWidget.rowCount()
        
        # Iterar sobre todas las filas y hacer la columna 0 (timestep) no editable
        for row in range(row_count):
            # Columna 0: Timestep (no editable)
            item = self.dlg_user_storm.tableWidget.item(row, 0)
            if item is None:
                item = QTableWidgetItem()
                self.dlg_user_storm.tableWidget.setItem(row, 0, item)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignCenter)

            # Columna 1: Precipitación (editable pero centrado)
            item_precip = self.dlg_user_storm.tableWidget.item(row, 1)
            if item_precip is None:
                item_precip = QTableWidgetItem()
                self.dlg_user_storm.tableWidget.setItem(row, 1, item_precip)
            item_precip.setTextAlignment(Qt.AlignCenter)
        
        # Deshabilitar el encabezado vertical (números de fila)
        self.dlg_user_storm.tableWidget.verticalHeader().setVisible(False)

    
    
    def browse_design_results_csv(self):
        """Method tho browse csv with results of design"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_design_results, "Select Design Results File",working_directory , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_design_results.design_file.setText(text)
    
    def browse_files_sensitivity_results_sobol(self):
        """Method to select the file for sensitivity analysis graph between the local files for Sobol"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Sobol Sensitivity Analysis Results File",working_directory+"\\sensitivity\\output" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_base.csv_results_2.setText(text)
    
    def browse_files_sensitivity_results_fast(self):
        """Method to select the file for sensitivity analysis graph between the local files for FAST"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select FAST Sensitivity Analysis Results File",working_directory+"\\sensitivity\\output" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_base.csv_results_fast.setText(text)
    
    def browse_files_calibration_hydrograph(self):
        """Method to select the file for calibration results"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_calibration_results_hydrograph, "Select Calibration Results File",working_directory+"\\inverse" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_calibration_results_hydrograph.results.setText(text)
    
    def browse_files_calibration_sedimentograph(self):
        """Method to select the file for calibration results"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_calibration_results_sedimentograph, "Select Calibration Results File",working_directory+"\\inverse" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_calibration_results_sedimentograph.results.setText(text)
    
    def browse_csv_oat(self):
        """Method to add csv of oat results"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select OAT Sensitivity Analysis Results File",working_directory+"\\sensitivity\\output" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_base.csv_results_oat.setText(text)
    
    def browse_csv_uncertainity(self):
        """Method to add csv of uncertainity results"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Uncertainity Analysis Results File",working_directory+"\\uncertainity\\output" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_base.csv_results_uncertainity.setText(text)
            #Update graph
            self.update_graph_uncertainity()
        
    def browse_files_sensitivity_results(self):
        """Method to select the file for sensitivity analysis graph between the local files for Morris"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Morris Sensitivity Analysis Results File",working_directory+"\\sensitivity\\output" , "CSV files (*.csv)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
            self.dlg_base.csv_results_morris.setText(text)
    
    def show_graph_sensitivity_global(self):
        """Method to add the graph of global sensitivity analysis"""
        if not hasattr(self, 'canvas_sensitivity_graph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_sensitivity_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_base.frame_64)
            self.dlg_base.frame_64.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_sensitivity_graph)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_sensitivity_graph.figure.clear()
        
        
    def update_sensitivity_graph_global(self):
        """Method to update the graph of the sensitivity for Sobol"""
        #MORRIS
        if self.dlg_base.radio_morris.isChecked():
            ruta = self.obtain_direction_vfsmod(self.dlg_base.csv_results_morris.text())
            if os.path.exists(ruta):
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                #If the csv is not of a Morris sensitivity analysis then give error
                if lineas[0]!="Morris sensitivity indexes" + '\n':
                    self.warning_message("Please select a csv file that contains Morris sensitivity analysis results")
                    return
                
                #Create and clear axis before drawing
                self.canvas_sensitivity_graph.figure.clear()
                self.ax = self.canvas_sensitivity_graph.figure.subplots()
                #Obtain data
                #Obtain ouputs parameter
                if self.dlg_base.runoff_source_mm_2.isChecked():output_column = "Total Runoff from source (mm)"
                if self.dlg_base.runoff_source_m3_2.isChecked():output_column = "Total Runoff from Source (m3)"
                if self.dlg_base.runoff_filter_mm_2.isChecked():output_column = "Total Runoff out from Filter (mm)"
                if self.dlg_base.runoff_filter_m3_2.isChecked():output_column = "Total Runoff out from Filter (m3)"
                if self.dlg_base.infiltration_filter_m3_2.isChecked():output_column = "Total Infiltration in Filter (m3)"
                if self.dlg_base.sediment_input_2.isChecked():output_column = "Mass Sediment Input to Filter (kg)"
                if self.dlg_base.concentration_sediment_2.isChecked():output_column = "Concentration Sediment in Runoff from source Area (g/L)"
                if self.dlg_base.sediment_output_2.isChecked():output_column = "Mass Sediment Output from Filter (kg)"
                if self.dlg_base.sediment_runoff_exit_2.isChecked():output_column = "Concentration Sediment in Runoff exiting the Filter (g/L)"
                if self.dlg_base.sediment_delivery_2.isChecked():output_column = "Sediment Delivery Ratio"
                if self.dlg_base.runoff_delivery_2.isChecked():output_column = "Runoff Delivery Ratio"
                
                names_inputs = []
                mu_star = []
                sigma = []
                for i in range(len(lineas)):
                    if lineas[i] == output_column+ '\n':
                        for k in lineas[i+1:]:
                            if k == "----------------------------------------------------------------------" + '\n':
                                    break
                            names_inputs.append(k.split(":")[0])
                            mu_star.append(float(k.split(":")[1].split("_")[0]))
                            sigma.append(float(k.split(":")[1].split("_")[1]))
                            
                # Graficar los puntos con color granate y agregar etiquetas
                for i, (x, y) in enumerate(zip(mu_star, sigma)):
                    if np.isnan(x):x = 0
                    if np.isnan(y):y = 0
                    self.ax.scatter(x, y, marker="o", color="maroon")
                    self.ax.annotate(f'{names_inputs[i]}', (x, y), textcoords="offset points", xytext=(10,10), ha='center', 
                        fontweight='bold',fontsize = 8)
                #Linea 1:1
                line_plot = list(range(-1,int(max(list(mu_star)+list(sigma))*1.05)+2))
                self.ax.plot(line_plot, line_plot, color="red",linestyle="--")

                self.ax.set_xlim(0,max(list(mu_star)+list(sigma))*1.05)
                self.ax.set_ylim(0,max(list(mu_star)+list(sigma))*1.05)
                #Separador de miles
                def formato_con_separador(valor, pos):
                    if max(list(mu_star))>10:
                        return "{:,.0f}".format(valor)
                    else:
                        return "{:,.2f}".format(valor)
                self.ax.xaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                self.ax.yaxis.set_major_formatter(FuncFormatter(formato_con_separador))
                #Labels
                self.ax.set_xlabel("Mean of Elementary Effects ($\mu_{i}^{*}$)",size = 14,family="arial",weight = "bold",color = "black")
                self.ax.set_ylabel("Standard Deviation of Elementary Effects ($\sigma_{i}$)",size = 14,family="arial",weight = "bold",color = "black")
                        
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph.draw()
        
        #FAST
        if self.dlg_base.radio_fast.isChecked():
            ruta = self.obtain_direction_vfsmod(self.dlg_base.csv_results_fast.text())
            if os.path.exists(ruta):
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                #If the csv is not of a FAST sensitivity analysis then give error
                if lineas[0]!="FAST sensitivity indexes" + '\n':
                    self.warning_message("Please select a csv file that contains FAST sensitivity analysis results")
                    return
                
                #Create and clear axis before drawing
                self.canvas_sensitivity_graph.figure.clear()
                self.ax_fast = self.canvas_sensitivity_graph.figure.subplots(1,2)
                
                #Obtain data
                #Obtain ouputs parameter
                if self.dlg_base.runoff_source_mm_2.isChecked():output_column = "Total Runoff from source (mm)"
                if self.dlg_base.runoff_source_m3_2.isChecked():output_column = "Total Runoff from Source (m3)"
                if self.dlg_base.runoff_filter_mm_2.isChecked():output_column = "Total Runoff out from Filter (mm)"
                if self.dlg_base.runoff_filter_m3_2.isChecked():output_column = "Total Runoff out from Filter (m3)"
                if self.dlg_base.infiltration_filter_m3_2.isChecked():output_column = "Total Infiltration in Filter (m3)"
                if self.dlg_base.sediment_input_2.isChecked():output_column = "Mass Sediment Input to Filter (kg)"
                if self.dlg_base.concentration_sediment_2.isChecked():output_column = "Concentration Sediment in Runoff from source Area (g/L)"
                if self.dlg_base.sediment_output_2.isChecked():output_column = "Mass Sediment Output from Filter (kg)"
                if self.dlg_base.sediment_runoff_exit_2.isChecked():output_column = "Concentration Sediment in Runoff exiting the Filter (g/L)"
                if self.dlg_base.sediment_delivery_2.isChecked():output_column = "Sediment Delivery Ratio"
                if self.dlg_base.runoff_delivery_2.isChecked():output_column = "Runoff Delivery Ratio"
                
                names_inputs = []
                s1 = []
                s1_conf = []
                st = []
                st_conf = []
                for i in range(len(lineas)):
                    if lineas[i] == output_column+ '\n':
                        for k in lineas[i+1:]:
                            if k == "----------------------------------------------------------------------" + '\n':
                                    break
                            names_inputs.append(k.split(":")[0])
                            s1.append(float(k.split(":")[1].split("_")[0]))
                            s1_conf.append(float(k.split(":")[1].split("_")[1]))
                            st.append(float(k.split(":")[1].split("_")[2]))
                            st_conf.append(float(k.split(":")[1].split("_")[3]))
                
                #Total order 
                self.ax_fast[0].bar(names_inputs, st, yerr=st_conf, capsize=5, color='b')
                self.ax_fast[0].set_title('Total order index (ST)', fontsize=10)
                self.ax_fast[0].set_ylabel('FAST index')
                self.ax_fast[0].tick_params(axis='x', rotation=20,labelsize = 8)
                
                #First order 
                self.ax_fast[1].bar(names_inputs, s1, yerr=s1_conf, capsize=5, color='b')
                self.ax_fast[1].set_title('First order index (S1)', fontsize=10)
                self.ax_fast[1].tick_params(axis='x', rotation=20,labelsize = 8)
                
                
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph.draw()
        
        #Sobol
        elif self.dlg_base.radio_sobol.isChecked():
            ruta = self.obtain_direction_vfsmod(self.dlg_base.csv_results_2.text())
            if os.path.exists(ruta):
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                #If the csv is not of a Sobol sensitivity analysis then give error
                if lineas[0]!="Sobol sensitivity indexes" + '\n':
                    self.warning_message("Please select a csv file that contains Sobol sensitivity analysis results")
                    return
                
                #Create and clear axis before drawing
                self.canvas_sensitivity_graph.figure.clear()
                self.ax_sobol = self.canvas_sensitivity_graph.figure.subplots(1, 2)
                
                #Obtain data
                #Obtain ouputs parameter
                if self.dlg_base.runoff_source_mm_2.isChecked():output_column = "Total Runoff from source (mm)"
                if self.dlg_base.runoff_source_m3_2.isChecked():output_column = "Total Runoff from Source (m3)"
                if self.dlg_base.runoff_filter_mm_2.isChecked():output_column = "Total Runoff out from Filter (mm)"
                if self.dlg_base.runoff_filter_m3_2.isChecked():output_column = "Total Runoff out from Filter (m3)"
                if self.dlg_base.infiltration_filter_m3_2.isChecked():output_column = "Total Infiltration in Filter (m3)"
                if self.dlg_base.sediment_input_2.isChecked():output_column = "Mass Sediment Input to Filter (kg)"
                if self.dlg_base.concentration_sediment_2.isChecked():output_column = "Concentration Sediment in Runoff from source Area (g/L)"
                if self.dlg_base.sediment_output_2.isChecked():output_column = "Mass Sediment Output from Filter (kg)"
                if self.dlg_base.sediment_runoff_exit_2.isChecked():output_column = "Concentration Sediment in Runoff exiting the Filter (g/L)"
                if self.dlg_base.sediment_delivery_2.isChecked():output_column = "Sediment Delivery Ratio"
                if self.dlg_base.runoff_delivery_2.isChecked():output_column = "Runoff Delivery Ratio"
                
                names_inputs = []
                s1 = []
                s1_conf = []
                st = []
                st_conf = []
                for i in range(len(lineas)):
                    if lineas[i] == output_column+ '\n':
                        for k in lineas[i+1:]:
                            if k == "----------------------------------------------------------------------" + '\n':
                                    break
                            names_inputs.append(k.split(":")[0])
                            s1.append(float(k.split(":")[1].split("_")[0]))
                            s1_conf.append(float(k.split(":")[1].split("_")[1]))
                            st.append(float(k.split(":")[1].split("_")[2]))
                            st_conf.append(float(k.split(":")[1].split("_")[3]))
                
                #Total order 
                self.ax_sobol[0].bar(names_inputs, st, yerr=st_conf, capsize=5, color='b')
                self.ax_sobol[0].set_title('Total order index (ST)', fontsize=10)
                self.ax_sobol[0].set_ylabel('Sobol index')
                self.ax_sobol[0].tick_params(axis='x', rotation=20,labelsize = 8)
                
                #First order 
                self.ax_sobol[1].bar(names_inputs, s1, yerr=s1_conf, capsize=5, color='b')
                self.ax_sobol[1].set_title('First order index (S1)', fontsize=10)
                self.ax_sobol[1].tick_params(axis='x', rotation=20,labelsize = 8)
                
                
                # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                self.canvas_sensitivity_graph.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
                #Draw canvas
                self.canvas_sensitivity_graph.draw()
    

    def browse_files_uncertainity(self,information):
        """Method to select the file for uncertainity analysis between the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        if information=="prj": 
            select = "Select VFS Project File"
            types = "PRJ files (*.prj)"
        elif information == "lis": 
            select = "Select UH Project File"
            types = "LIS files (*.lis)"
        else:
            select = "Select CSV File"
            types = "CSV files (*.csv)"
        fname = QFileDialog.getOpenFileName(self.dlg_base, select,working_directory , types)
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
        if information == "prj":
            self.dlg_base.vfs_file_uncertainity.setText(text)
        elif information == "lis":
            self.dlg_base.uh_file_uncertainity.setText(text)
        else:
            self.dlg_base.file_save_uncertainity.setText(text)
    
    
    def browse_files_sensitivity(self,information):
        """Method to select the file for sensitivity analysis between the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        if information=="prj": 
            select = "Select VFS Project File"
            types = "PRJ files (*.prj)"
        elif information == "lis": 
            select = "Select UH Project File"
            types = "LIS files (*.lis)"
        else:
            select = "Select CSV File"
            types = "CSV files (*.csv)"
        fname = QFileDialog.getOpenFileName(self.dlg_base, select,working_directory , types)
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                text = os.path.relpath(fname[0], working_directory)
            else: #absolute path
                text = fname[0]
        if information == "prj":
            self.dlg_base.vfs_file_sensitivity.setText(text)
        elif information == "lis":
            self.dlg_base.uh_file_sensitivity.setText(text)
        else:
            self.dlg_base.file_save.setText(text)
    
    def start_analysis_design(self):
        """Method to execute the class to paralelization of design analysis. A class like that 
        has to be used because we need QTrhead to add progress bar"""
        self.number_execution = 0
        self.results = []
        args_list = [(i, i % (self.number_cores*2), 
          self.combinations_design,self.working_directory,
          self.dlg_base.design_length.isChecked(),self.dlg_base.design_spacing.isChecked(),
          self.obtain_direction_vfsmod(self.dlg_base.design_vfs_file.text())) for i in range(len(self.combinations_design))]
        self.progress_dialog = QProgressDialog("Starting design...", "Cancel", 0, len(args_list))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Progress")
        self.progress_dialog.show()
        
        self.sensitivity_thread = DesignAnalysisThread(args_list)
        self.sensitivity_thread.update_progress.connect(self.update_progress_dialog_design)
        self.sensitivity_thread.start()

    def update_progress_dialog_design(self,data):
        """Method to update progress bar in design paralelization"""
        self.number_execution +=1
        self.results.append(data[1])
        text = f"Execution {self.number_execution}/{len(self.combinations_design)}\n"
        self.progress_dialog.setLabelText(text)
        self.progress_dialog.setValue(int(self.progress_dialog.maximum()*((self.number_execution / len(self.combinations_design)))))
        QCoreApplication.processEvents()  # Permitir que la interfaz gráfica responda
        
        if self.number_execution == len(self.combinations_design):
            self.run_design_part_two()
    
    def start_analysis_sensitivity(self):
        """Method to execute the class to paralelization of sensitivity analysis. A class like that 
        has to be used because we need QTrhead to add progress bar"""
        self.number_execution = 0
        self.results = []
        args_list = [(i, i % (self.number_cores*2), 
          self.param_values, self.dic_data, 
          self.sensitivity_parameters, self.working_directory, 
          self.obtain_direction_vfsmod(self.vfs_sensitivity_file),self.water_quality) for i in range(len(self.param_values))]
        self.progress_dialog = QProgressDialog("Starting sensitivity analysis...", "Cancel", 0, len(args_list))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Progress")
        self.progress_dialog.show()
        
        self.sensitivity_thread = SensitivityAnalysisThread(args_list)
        self.sensitivity_thread.update_progress.connect(self.update_progress_dialog_sensitivity)
        self.sensitivity_thread.start()

    def update_progress_dialog_sensitivity(self,data):
        """Method to update progress bar in sensitivity paralelization"""
        self.number_execution +=1
        self.results.append(data[1])
        text = f"Execution {self.number_execution}/{len(self.param_values)}\n"
        self.progress_dialog.setLabelText(text)
        self.progress_dialog.setValue(int(self.progress_dialog.maximum()*((self.number_execution / len(self.param_values)))))
        QCoreApplication.processEvents()  # Permitir que la interfaz gráfica responda
        
        if self.number_execution == len(self.param_values):
            self.run_sensitivity_analysis_part_two()
    
    def start_analysis_uncertainity(self):
        """Method to execute the class to paralelization of uncertainity analysis. A class like that 
        has to be used because we need QTrhead to add progress bar"""
        self.number_execution = 0
        self.results = []
        args_list = [(i, i % (self.number_cores*2), 
          self.param_values, self.dic_data, 
          self.sensitivity_parameters, self.working_directory, 
          self.obtain_direction_vfsmod(self.vfs_uncertainity_file),self.water_quality) for i in range(len(self.combinations_design))]
        self.progress_dialog = QProgressDialog("Starting uncertainity analysis...", "Cancel", 0, len(args_list))
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Progress")
        self.progress_dialog.show()
        
        self.sensitivity_thread = UncertainityAnalysisThread(args_list)
        self.sensitivity_thread.update_progress.connect(self.update_progress_dialog_uncertainity)
        self.sensitivity_thread.start()

    def update_progress_dialog_uncertainity(self,data):
        """Method to update progress bar in uncertainity paralelization"""
        self.number_execution +=1
        self.results.append(data[1])
        text = f"Execution {self.number_execution}/{len(self.param_values)}\n"
        self.progress_dialog.setLabelText(text)
        self.progress_dialog.setValue(int(self.progress_dialog.maximum()*((self.number_execution / len(self.param_values)))))
        QCoreApplication.processEvents()  # Permitir que la interfaz gráfica responda
        
        if self.number_execution == len(self.param_values):
            self.run_uncertainity_analysis_part_two()
    
    
    def run_sensitivity_analysis_part_one(self):
        """Method to run whole sensitivity analysis"""
        #Create the dictionary for the sensitivity analysis
        self.dic_data = self.create_dictionary_sensitivity_analysis()
        
        self.vfs_sensitivity_file = self.dlg_base.vfs_file_sensitivity.text()
        
        #Create problem variable
        if not self.dlg_base.oat.isChecked():
            self.problem = {'num_vars': len(self.dic_data),'names': list(self.dic_data.keys()),'bounds': [x[1] for x in self.dic_data.values()],"dists":[x[0] for x in self.dic_data.values()]}
        #Create samples
        if self.dlg_base.sobol.isChecked():
            if int(self.dlg_base.trajectories.text())<256:
                self.warning_message("Number of samples must be 256 or higher when executing Sobol")
                return
            self.param_values = saltelli.sample(self.problem, int(self.dlg_base.trajectories.text()))
        elif self.dlg_base.morris.isChecked():
            #Warnings
            if int(self.dlg_base.trajectories.text())<8:
                self.warning_message("N value must be 8 or higher when executing Morris")
                return
            if self.dlg_base.table.rowCount()<2:
                self.warning_message("Select at least 2 parameters for Morris sensitivity analysis")
                return
                
            self.param_values = sample_morris(self.problem, int(self.dlg_base.trajectories.text()))
        elif self.dlg_base.fast.isChecked():
            if int(self.dlg_base.trajectories.text())<256:
                self.warning_message("N value must be 256 or higher when executing FAST")
                return
            self.param_values = sample_fast(self.problem, int(self.dlg_base.trajectories.text()), M = 1)
        elif self.dlg_base.oat.isChecked():
            #Put OAT input values as the format for the other sensitivity analysis
            lista_de_listas = []
            for k,i in enumerate(self.dic_data.values()):
                lista_de_listas.append([i,k])
            lista_general = []
            for k, lista in enumerate(lista_de_listas):
                for m in lista[0]:
                    sub = []
                    for h in range(len(lista_de_listas)):
                        if lista_de_listas[h][1]==k:
                            sub.append(m)
                        else:
                            sub.append(lista_de_listas[h][0][0])
                    lista_general.append(sub)

            self.param_values = np.array(lista_general)
        
        #We start obtaining the results
        #Create folders of sensitivity analysis
        self.create_folder_sensitivity_analysis()
        
        #Move files to sensitivity analysis folder
        self.move_files_sensitivity_analysis()
        
        
        #Create dataframe to save the results
        self.results_sensitivity = pd.DataFrame(columns=["Error","Total Runoff from source (mm)","Total Runoff from Source (m3)",
            "Total Runoff out from Filter (mm)","Total Runoff out from Filter (m3)","Total Infiltration in Filter (m3)",
            "Mass Sediment Input to Filter (kg)","Concentration Sediment in Runoff from source Area (g/L)",
            "Mass Sediment Output from Filter (kg)","Concentration Sediment in Runoff exiting the Filter (g/L)",
            "Sediment Delivery Ratio","Runoff Delivery Ratio","Water Front Depth (m)"])
        #Add water quality parameters if present
        if self.water_quality:
            self.results_sensitivity.insert(len(self.results_sensitivity.columns),"Leachate depth (m)",None)
        
        self.number_outputs = len(self.results_sensitivity.columns)-1
        #Add the parameters names 
        for i in self.dic_data.keys():
            self.results_sensitivity.insert(0,i,None)
        
        #Method were the paralelization is achieved
        self.start_analysis_sensitivity()

        
        
    def run_sensitivity_analysis_part_two(self):
        """Second part of sensitivity analysis to analyze the results. I have splitted sensitivity running
        in two because we use Thread method and we need to stop till the thread finishes, if not we get an error"""
        
        #Create DataFrame or results
        self.results_sensitivity = self.create_df_sensitivity(self.results)
        
        #Delete all files created for paralelization of sensitivity analysis
        self.delete_files_sensitivity()
        
        
        #Save results in CSV
        path = self.obtain_direction_vfsmod(self.dlg_base.file_save.text())
        try:
            if self.dlg_base.sobol.isChecked():
                with open(path, 'w') as f:
                    #Add first row
                    f.write("Sobol sensitivity indexes" + '\n')
                    #Add sensitivity indexes for each output
                    for i in self.results_sensitivity.columns[-self.number_outputs:]:
                        f.write("----------------------------------------------------------------------" + '\n')
                        f.write(f"{i}" + '\n')
                        si = sobol.analyze(self.problem, np.array(self.results_sensitivity[i]))
                        for input_parameter_k,input_parameter in enumerate(self.dic_data.keys()): 
                            f.write(f"{input_parameter}:{si['S1'][input_parameter_k]}_{si['S1_conf'][input_parameter_k]}_{si['ST'][input_parameter_k]}_{si['ST_conf'][input_parameter_k]}_{si['S2'][input_parameter_k]}_{si['S2_conf'][input_parameter_k]}" + '\n')
                    f.write("----------------------------------------------------------------------" + '\n')
                    
            elif self.dlg_base.morris.isChecked():
                with open(path, 'w') as f:
                    #Add first row
                    f.write("Morris sensitivity indexes" + '\n')
                    #Add sensitivity indexes for each output
                    for i in self.results_sensitivity.columns[-self.number_outputs:]:
                        f.write("----------------------------------------------------------------------" + '\n')
                        f.write(f"{i}" + '\n')
                        si = analyze_morris(self.problem,np.array(self.param_values),np.array(self.results_sensitivity[i]))
                        for input_parameter_k,input_parameter in enumerate(self.dic_data.keys()):    
                            f.write(f"{input_parameter}:{si['mu_star'][input_parameter_k]}_{si['sigma'][input_parameter_k]}" + '\n')
                    f.write("----------------------------------------------------------------------" + '\n')
            
            elif self.dlg_base.fast.isChecked():
                with open(path, 'w') as f:
                    #Add first row
                    f.write("FAST sensitivity indexes" + '\n')
                    #Add sensitivity indexes for each output
                    for i in self.results_sensitivity.columns[-self.number_outputs:]:
                        f.write("----------------------------------------------------------------------" + '\n')
                        f.write(f"{i}" + '\n')
                        si = analyze_fast(self.problem,np.array(self.results_sensitivity[i]))
                        for input_parameter_k,input_parameter in enumerate(self.dic_data.keys()):    
                            f.write(f"{input_parameter}:{si['S1'][input_parameter_k]}_{si['S1_conf'][input_parameter_k]}_{si['ST'][input_parameter_k]}_{si['ST_conf'][input_parameter_k]}" + '\n')
                    f.write("----------------------------------------------------------------------" + '\n')
            
            elif self.dlg_base.oat.isChecked():
                with open(path, 'w') as f:
                    f.write("OAT sensitivity results" + '\n')
                    string = f"Studied parameters:"
                    for i in range(len(self.dic_data)):
                        string += list(self.dic_data.keys())[i]
                        if i!= len(self.dic_data)-1:
                            string +=","
                        else:
                            string += "\n"
                    f.write(string)
                    start = [0,0]
                    f.write("----------------------------------------------------------------------" + '\n')
                    for i in self.dic_data.keys():
                        f.write(i + " results" + '\n')
                        a = len(self.dic_data[i])
                        start[1] += start[0]+a
                        data = self.results_sensitivity.iloc[start[0]:start[1],:]
                        #Put dataframe
                        f.write(','.join(data.columns) + '\n')
                        for index, row in data.iterrows():
                            f.write(','.join(map(str, row.values)) + '\n')
                        start[0]=start[0]+a
                        f.write("----------------------------------------------------------------------" + '\n')
        except PermissionError:
            self.warning_message(f"{path} file is opened and Sensitivity Analysis data could not be saved")
            return
        
        #Append results
        if not self.dlg_base.oat.isChecked():
            self.results_sensitivity.to_csv(path, mode='a',index=False, float_format='%.5f')
        
        #Close progress bar and warning message of ending
        self.progress_metod(close = True)
        self.warning_message("Sensitivity analysis completed succesfully!")
    
    def create_df_design(self,results):
        """Method to create the dataframe of design after parallelization"""
        #First create dataframe
        df = pd.DataFrame(columns=list(results[0].columns))
        for i in results:
            df = pd.concat([df,i], ignore_index=True)
        #Put in the same order as the input values
        new_df = pd.DataFrame(columns=list(results[0].columns))
        input_parameters = ["Rainfall (mm)"]
        combinations_design = [x[0] for x in self.combinations_design]
        if self.dlg_base.design_length.isChecked():
            input_parameters += ["VFS Length (m)"]
            combinations_design = [[combinations_design[x],self.combinations_design[x][1]] for x in range(len(combinations_design))]
        if self.dlg_base.design_spacing.isChecked():
            input_parameters += ["Vegetation Spacing (cm)"]
            combinations_design = [[combinations_design[x],self.combinations_design[x][2]] for x in range(len(combinations_design))]
        for i in combinations_design:
            df_concat = df.copy()
            for k in range(len(i)): 
                df_concat = df_concat[df_concat[input_parameters[k]]==i[k]]
            df_concat = df_concat.iloc[[0]]
            new_df = pd.concat([new_df,df_concat], ignore_index=True)
        return new_df
    
    def create_df_sensitivity(self,results):
        """Method to create the dataframe of sensitivity after parallelization"""
        #First create dataframe
        df = pd.DataFrame(columns=list(results[0].columns))
        for i in results:
            df = pd.concat([df,i], ignore_index=True)
        #Put in the same order as the input values
        new_df = pd.DataFrame(columns=list(results[0].columns))
        input_parameters = list(self.dic_data.keys())
        for i in self.param_values:
            df_concat = df.copy()
            for k in range(len(i)): 
                df_concat = df_concat[df_concat[input_parameters[k]]==i[k]]
            df_concat = df_concat.iloc[[0]]
            new_df = pd.concat([new_df,df_concat], ignore_index=True)
        return new_df
    
    def create_df_uncertainity(self,results):
        """Method to create the dataframe of uncertainity after parallelization"""
        #First create dataframe
        df = pd.DataFrame(columns=list(results[0].columns))
        for i in results:
            df = pd.concat([df,i], ignore_index=True)
        return df     
            
    
    def run_uncertainity_analysis_part_one(self):
        """Method to run parallel processing of uncertainity analysis"""
        #Create the dictionary for the sensitivity analysis
        self.dic_data = self.create_dictionary_uncertainity_analysis()
        self.vfs_uncertainity_file = self.dlg_base.vfs_file_uncertainity.text()
        
        #Warning
        if int(self.dlg_base.samples_uncertainity.text())<2:
            self.warning_message("N value must be higher than 256 when executing Uncertainity Analysis")
            return
        
        #We will use the fast sample to obtain randomized samples for each input
        values = []
        for parameter in self.dic_data.keys():
            #Create problem variable
            self.problem = {'num_vars': 1,'names': [parameter],'bounds': [self.dic_data[parameter][1]],"dists":[self.dic_data[parameter][0]]}
            #Create samples
            samples = sample_fast(self.problem, int(self.dlg_base.samples_uncertainity.text()), M = 1)
            values.append(samples)
        
        self.param_values = np.column_stack(values)

        #We start obtaining the results
        #Create folders of uncertainity analysis
        self.create_folder_uncertainity_analysis()
        
        #Move files to uncertainity analysis folder
        self.move_files_uncertainity_analysis()
        
        #Create dataframe to save the results
        self.results_sensitivity = pd.DataFrame(columns=["Error","Total Runoff from source (mm)","Total Runoff from Source (m3)",
            "Total Runoff out from Filter (mm)","Total Runoff out from Filter (m3)","Total Infiltration in Filter (m3)",
            "Mass Sediment Input to Filter (kg)","Concentration Sediment in Runoff from source Area (g/L)",
            "Mass Sediment Output from Filter (kg)","Concentration Sediment in Runoff exiting the Filter (g/L)",
            "Sediment Delivery Ratio","Runoff Delivery Ratio","Water Front Depth (m)"])
        
        #Add water quality parameters if present
        if self.water_quality:
            self.results_sensitivity.insert(len(self.results_sensitivity.columns),"Leachate depth (m)",None)
        
        number_outputs = len(self.results_sensitivity.columns)-1
        #Add the parameters names 
        for i in self.dic_data.keys():
            self.results_sensitivity.insert(0,i,None)
        #Method were the paralelization is achieved
        self.start_analysis_uncertainity()
        
        
    def run_uncertainity_analysis_part_two(self):
        """Second part of uncertainity analysis to analyze the results. I have splitted uncertainity running
        in two because we use Thread method and we need to stop till the thread finishes, if not we get an error"""

        #Create DataFrame or results
        self.results_sensitivity = self.create_df_uncertainity(self.results)
        
        #Delete all files created for paralelization of sensitivity analysis
        self.delete_files_uncertainity()
            
        #Save results in CSV
        path = self.obtain_direction_vfsmod(self.dlg_base.file_save_uncertainity.text())
        try:
            with open(path, 'w') as f:
                f.write("Uncertainity analysis results" + '\n')
                string = f"Studied parameters:"
                for i in range(len(self.dic_data)):
                    string += list(self.dic_data.keys())[i]
                    if i!= len(self.dic_data)-1:
                        string +=","
                    else:
                        string += "\n"
                f.write(string)
        except PermissionError:
            self.warning_message(f"{path} file is opened and Uncertainity Analysis data could not be saved")
            return
        self.results_sensitivity.to_csv(path, mode='a',index=False, float_format='%.5f')
        
        #Close progress bar and warning message of ending
        self.progress_metod(close = True)
        self.warning_message("Uncertainity analysis completed succesfully!")
    
    
    def move_files_design_analysis(self):
        """Method to move files to the corresponding folders for sensitiviy analysis"""
        #FIRST WE MOVE THE FILES TO THE FOLDER OF DESIGN ANALYSIS
        #Prj
        prj_file = self.dlg_base.working_directory_vfsmod.text()+"\\design\\design.prj"
        #Check if water quality is simulated
        with open(self.obtain_direction_vfsmod(self.dlg_base.design_vfs_file.text()), "r") as archivo:
            lineas = archivo.readlines()
        self.water_quality = False
        for i in lineas:
            if i[:3]=="iwq":
                self.water_quality = True
            
        #Create file
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw=inputs\\design.ikw  \n")
            archivo.write(f"iso=inputs\\design.iso  \n")
            archivo.write(f"igr=inputs\\design.igr  \n")
            archivo.write(f"isd=inputs\\design.isd  \n")
            archivo.write(f"irn=inputs\\design.irn  \n")
            archivo.write(f"iro=inputs\\design.iro  \n")
            if self.water_quality:
                archivo.write(f"iwq=inputs\\design.iwq  \n")
            archivo.write(f"og1=output\\design.og1  \n")
            archivo.write(f"og2=output\\design.og2  \n")
            archivo.write(f"ohy=output\\design.ohy  \n")
            archivo.write(f"osm=output\\design.osm  \n")
            archivo.write(f"osp=output\\design.osp  \n")
            if self.water_quality:
                archivo.write(f"owq=output\\design.owq  \n")
        
        #UH
        lis_file = self.dlg_base.working_directory_vfsmod.text()+"\\design\\design.lis"
        #Create file
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp=inputs\\design.inp  \n")
            archivo.write(f"iro=inputs\\design.iro  \n")
            archivo.write(f"irn=inputs\\design.irn  \n")
            archivo.write(f"isd=inputs\\design.isd  \n")
            archivo.write(f"out=inputs\\design.out  \n")
            archivo.write(f"hyt=inputs\\design.hyt  \n")
        
        #REST OF THE FILES
        #Function to copy and paste the inputs to create the files to use in the design analysis
        def copy_paste(process,type_input):
            ruta_pegar = self.dlg_base.working_directory_vfsmod.text()+f"\\design\\inputs\\design.{type_input}" 
            if process == "UH":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.design_uh_file.text())
            elif process == "VFS":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.design_vfs_file.text())
            if os.path.exists(ruta) and os.path.isfile(ruta):
                #First we open .prj and obtain the direction of the copying file
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==type_input:
                        ikw = i.split("=")[-1]
                if not os.path.isabs(ikw): #relative path
                    ikw = os.path.join(os.path.dirname(ruta), ikw)
                ikw = ikw.replace("\n", "") #take out the line jumps
                shutil.copyfile(ikw, ruta_pegar)
        #INP
        copy_paste("UH","inp")
        #OUT
        copy_paste("UH","out")
        #HYT
        copy_paste("UH","hyt")
        
        #IKW
        copy_paste("VFS","ikw")
        #ISO
        copy_paste("VFS","iso")
        #IGR
        copy_paste("VFS","igr")
        #ISD
        copy_paste("VFS","isd")
        #IRN
        copy_paste("VFS","irn")
        #IRO
        copy_paste("VFS","iro")
        #IWQ
        if self.water_quality:
            copy_paste("VFS","iwq")
        
        
        #Put base values
        self.modify_inp_file_design(duration = self.dlg_base.design_storm_duration.text())
        if not self.dlg_base.design_length.isChecked():
            self.modify_ikw_file_design()
        if not self.dlg_base.design_spacing.isChecked():
            self.modify_igr_file_design()
        
        #NOW WE REPLICATE THE FILES AS MUCH AS CORES ARE IN THE COMPUTER
        self.number_cores = psutil.cpu_count(logical=False)
        
        #Replicate prj as much as cores are
        for core in range(self.number_cores*2):#we do *2 because if not there can be problems of overlapping:processes executing files that are already executing
            with open(prj_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("design",f"design_{core}") for linea in lineas]
            new_filepath = prj_file.replace("design.prj",f"design_{core}.prj")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Replicate lis as much as cores are
        for core in range(self.number_cores*2):
            with open(lis_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("design",f"design_{core}") for linea in lineas]
            new_filepath = lis_file.replace("design.lis",f"design_{core}.lis")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Move replicated input files 
        carpeta = self.dlg_base.working_directory_vfsmod.text()+"\\design"
        folder_path = Path(carpeta+"\\inputs")
        files = [f.name for f in folder_path.iterdir() if f.is_file() and "_" not in f.name]
        for i in range(self.number_cores*2):
            for k in files:
                shutil.copyfile(carpeta+"\\inputs\\"+k, carpeta+"\\inputs\\"+k.replace("design",f"design_{i}"))
        #Replicate executables
        carpeta_bat = self.plugin_directory+"\\executables"
        for core in range(self.number_cores*2):
            #Execution UH
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_uh_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_uh_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\design\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\uh" design_{core}.lis'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
            #Execution VFS
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_vfs_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_vfs_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\design\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" design_{core}.prj'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
    
    def move_files_sensitivity_analysis(self):
        """Method to move files to the corresponding folders for sensitiviy analysis"""
        #FIRST WE MOVE THE FILES TO THE FOLDER OF SENSITIVITY ANALYSIS
        #Prj
        prj_file = self.dlg_base.working_directory_vfsmod.text()+"\\sensitivity\\sensitivity.prj"
        #Check if water quality is simulated
        with open(self.obtain_direction_vfsmod(self.dlg_base.vfs_file_sensitivity.text()), "r") as archivo:
            lineas = archivo.readlines()
        self.water_quality = False
        for i in lineas:
            if i[:3]=="iwq":
                self.water_quality = True
            
        #Create file
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw=inputs\\sensitivity.ikw  \n")
            archivo.write(f"iso=inputs\\sensitivity.iso  \n")
            archivo.write(f"igr=inputs\\sensitivity.igr  \n")
            archivo.write(f"isd=inputs\\sensitivity.isd  \n")
            archivo.write(f"irn=inputs\\sensitivity.irn  \n")
            archivo.write(f"iro=inputs\\sensitivity.iro  \n")
            if self.water_quality:
                archivo.write(f"iwq=inputs\\sensitivity.iwq  \n")
            archivo.write(f"og1=output\\sensitivity.og1  \n")
            archivo.write(f"og2=output\\sensitivity.og2  \n")
            archivo.write(f"ohy=output\\sensitivity.ohy  \n")
            archivo.write(f"osm=output\\sensitivity.osm  \n")
            archivo.write(f"osp=output\\sensitivity.osp  \n")
            if self.water_quality:
                archivo.write(f"owq=output\\sensitivity.owq  \n")
        
        #UH
        lis_file = self.dlg_base.working_directory_vfsmod.text()+"\\sensitivity\\sensitivity.lis"
        #Create file
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp=inputs\\sensitivity.inp  \n")
            archivo.write(f"iro=inputs\\sensitivity.iro  \n")
            archivo.write(f"irn=inputs\\sensitivity.irn  \n")
            archivo.write(f"isd=inputs\\sensitivity.isd  \n")
            archivo.write(f"out=inputs\\sensitivity.out  \n")
            archivo.write(f"hyt=inputs\\sensitivity.hyt  \n")
        
        #REST OF THE FILES
        #Function to copy and paste the inputs to create the files to use in the sensitivity analysis
        def copy_paste(process,type_input):
            ruta_pegar = self.dlg_base.working_directory_vfsmod.text()+f"\\sensitivity\\inputs\\sensitivity.{type_input}" 
            if process == "UH":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.uh_file_sensitivity.text())
            elif process == "VFS":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.vfs_file_sensitivity.text())
            if os.path.exists(ruta) and os.path.isfile(ruta):
                #First we open .prj and obtain the direction of the copying file
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==type_input:
                        ikw = i.split("=")[-1]
                if not os.path.isabs(ikw): #relative path
                    ikw = os.path.join(os.path.dirname(ruta), ikw)
                ikw = ikw.replace("\n", "") #take out the line jumps
                shutil.copyfile(ikw, ruta_pegar)
        #INP
        copy_paste("UH","inp")
        #OUT
        copy_paste("UH","out")
        #HYT
        copy_paste("UH","hyt")
        
        #IKW
        copy_paste("VFS","ikw")
        #ISO
        copy_paste("VFS","iso")
        #IGR
        copy_paste("VFS","igr")
        #ISD
        copy_paste("VFS","isd")
        #IRN
        copy_paste("VFS","irn")
        #IRO
        copy_paste("VFS","iro")
        #IWQ
        if self.water_quality:
            copy_paste("VFS","iwq")
        
        #NOW WE REPLICATE THE FILES AS MUCH AS CORES ARE IN THE COMPUTER
        self.number_cores = psutil.cpu_count(logical=False)
        
        #Replicate prj as much as cores are
        for core in range(self.number_cores*2):#we do *2 because if not there can be problems of overlapping:processes executing files that are already executing
            with open(prj_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("sensitivity",f"sensitivity_{core}") for linea in lineas]
            new_filepath = prj_file.replace("sensitivity.prj",f"sensitivity_{core}.prj")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Replicate lis as much as cores are
        for core in range(self.number_cores*2):
            with open(lis_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("sensitivity",f"sensitivity_{core}") for linea in lineas]
            new_filepath = lis_file.replace("sensitivity.lis",f"sensitivity_{core}.lis")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Move replicated input files 
        carpeta = self.dlg_base.working_directory_vfsmod.text()+"\\sensitivity"
        folder_path = Path(carpeta+"\\inputs")
        files = [f.name for f in folder_path.iterdir() if f.is_file() and "_" not in f.name]
        for i in range(self.number_cores*2):
            for k in files:
                shutil.copyfile(carpeta+"\\inputs\\"+k, carpeta+"\\inputs\\"+k.replace("sensitivity",f"sensitivity_{i}"))
        #Replicate executables
        carpeta_bat = self.plugin_directory+"\\executables"
        for core in range(self.number_cores*2):
            #Execution UH
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_uh_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_uh_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\sensitivity\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\uh" sensitivity_{core}.lis'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
            #Execution VFS
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_vfs_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_vfs_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\sensitivity\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" sensitivity_{core}.prj'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
    
    def delete_files_design(self):
        """Method to delete files of design analysis after parallelization"""
        files_delete = [self.working_directory+"\\design\\"+x for x in os.listdir(self.working_directory+"\\design") if "design" in x and "_" in x]
        files_delete += [self.working_directory+"\\design\\inputs\\"+x for x in os.listdir(self.working_directory+"\\design"+"\\inputs") if "design" in x and "_" in x]
        files_delete += [self.working_directory+"\\design\\output\\"+x for x in os.listdir(self.working_directory+"\\design"+"\\output") if "design" in x and "_" in x and x[-3:]!="csv"]
        files_delete += [self.plugin_directory+"\\executables\\"+x for x in os.listdir(self.plugin_directory+"\\executables") if "execution" in x and "_" in x]
        for i in files_delete:
            os.remove(i)
    
    def delete_files_sensitivity(self):
        """Method to delete files of sensitivity analysis after parallelization"""
        files_delete = [self.working_directory+"\\sensitivity\\"+x for x in os.listdir(self.working_directory+"\\sensitivity") if "sensitivity" in x and "_" in x]
        files_delete += [self.working_directory+"\\sensitivity\\inputs\\"+x for x in os.listdir(self.working_directory+"\\sensitivity"+"\\inputs") if "sensitivity" in x and "_" in x]
        files_delete += [self.working_directory+"\\sensitivity\\output\\"+x for x in os.listdir(self.working_directory+"\\sensitivity"+"\\output") if "sensitivity" in x and "_" in x and x[-3:]!="csv"]
        files_delete += [self.plugin_directory+"\\executables\\"+x for x in os.listdir(self.plugin_directory+"\\executables") if "execution" in x and "_" in x]
        for i in files_delete:
            os.remove(i)
    
    def delete_files_uncertainity(self):
        """Method to delete files of uncertainity analysis after parallelization"""
        files_delete = [self.working_directory+"\\uncertainity\\"+x for x in os.listdir(self.working_directory+"\\uncertainity") if "uncertainity" in x and "_" in x]
        files_delete += [self.working_directory+"\\uncertainity\\inputs\\"+x for x in os.listdir(self.working_directory+"\\uncertainity"+"\\inputs") if "uncertainity" in x and "_" in x]
        files_delete += [self.working_directory+"\\uncertainity\\output\\"+x for x in os.listdir(self.working_directory+"\\uncertainity"+"\\output") if "uncertainity" in x and "_" in x and x[-3:]!="csv"]
        files_delete += [self.plugin_directory+"\\executables\\"+x for x in os.listdir(self.plugin_directory+"\\executables") if "execution" in x and "_" in x]
        for i in files_delete:
            os.remove(i)
    
    def move_files_uncertainity_analysis(self):
        """Method to move files to the corresponding folders for uncertainity analysis"""
        #Prj
        prj_file = self.dlg_base.working_directory_vfsmod.text()+"\\uncertainity\\uncertainity.prj"
        #Check if water quality is simulated
        with open(self.obtain_direction_vfsmod(self.dlg_base.vfs_file_uncertainity.text()), "r") as archivo:
            lineas = archivo.readlines()
        self.water_quality = False
        for i in lineas:
            if i[:3]=="iwq":
                self.water_quality = True
            
        #Create file
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw=inputs\\uncertainity.ikw  \n")
            archivo.write(f"iso=inputs\\uncertainity.iso  \n")
            archivo.write(f"igr=inputs\\uncertainity.igr  \n")
            archivo.write(f"isd=inputs\\uncertainity.isd  \n")
            archivo.write(f"irn=inputs\\uncertainity.irn  \n")
            archivo.write(f"iro=inputs\\uncertainity.iro  \n")
            if self.water_quality:
                archivo.write(f"iwq=inputs\\uncertainity.iwq  \n")
            archivo.write(f"og1=output\\uncertainity.og1  \n")
            archivo.write(f"og2=output\\uncertainity.og2  \n")
            archivo.write(f"ohy=output\\uncertainity.ohy  \n")
            archivo.write(f"osm=output\\uncertainity.osm  \n")
            archivo.write(f"osp=output\\uncertainity.osp  \n")
            if self.water_quality:
                archivo.write(f"owq=output\\uncertainity.owq  \n")
        
        #UH
        lis_file = self.dlg_base.working_directory_vfsmod.text()+"\\uncertainity\\uncertainity.lis"
        #Create file
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp=inputs\\uncertainity.inp  \n")
            archivo.write(f"iro=inputs\\uncertainity.iro  \n")
            archivo.write(f"irn=inputs\\uncertainity.irn  \n")
            archivo.write(f"isd=inputs\\uncertainity.isd  \n")
            archivo.write(f"out=inputs\\uncertainity.out  \n")
            archivo.write(f"hyt=inputs\\uncertainity.hyt  \n")
        
        #REST OF THE FILES
        #Function to copy and paste the inputs to create the files to use in the uncertainity analysis
        def copy_paste(process,type_input):
            ruta_pegar = self.dlg_base.working_directory_vfsmod.text()+f"\\uncertainity\\inputs\\uncertainity.{type_input}" 
            if process == "UH":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.uh_file_uncertainity.text())
            elif process == "VFS":
                ruta = self.obtain_direction_vfsmod(self.dlg_base.vfs_file_uncertainity.text())
            if os.path.exists(ruta) and os.path.isfile(ruta):
                #First we open .prj and obtain the direction of the copying file
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==type_input:
                        ikw = i.split("=")[-1]
                if not os.path.isabs(ikw): #relative path
                    ikw = os.path.join(os.path.dirname(ruta), ikw)
                ikw = ikw.replace("\n", "") #take out the line jumps
                shutil.copyfile(ikw, ruta_pegar)
        #INP
        copy_paste("UH","inp")
        #OUT
        copy_paste("UH","out")
        #HYT
        copy_paste("UH","hyt")
        
        #IKW
        copy_paste("VFS","ikw")
        #ISO
        copy_paste("VFS","iso")
        #IGR
        copy_paste("VFS","igr")
        #ISD
        copy_paste("VFS","isd")
        #IRN
        copy_paste("VFS","irn")
        #IRO
        copy_paste("VFS","iro")
        #IWQ
        if self.water_quality:
            copy_paste("VFS","iwq")
        
        #NOW WE REPLICATE THE FILES AS MUCH AS CORES ARE IN THE COMPUTER
        self.number_cores = psutil.cpu_count(logical=False)
        
        #Replicate prj as much as cores are
        for core in range(self.number_cores*2):#we do *2 because if not there can be problems of overlapping:processes executing files that are already executing
            with open(prj_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("uncertainity",f"uncertainity_{core}") for linea in lineas]
            new_filepath = prj_file.replace("uncertainity.prj",f"uncertainity_{core}.prj")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Replicate lis as much as cores are
        for core in range(self.number_cores*2):
            with open(lis_file, 'r') as file:
                lineas = file.readlines()
            lineas = [linea.replace("uncertainity",f"uncertainity_{core}") for linea in lineas]
            new_filepath = lis_file.replace("uncertainity.lis",f"uncertainity_{core}.lis")
            with open(new_filepath, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
        #Move replicated input files 
        carpeta = self.dlg_base.working_directory_vfsmod.text()+"\\uncertainity"
        folder_path = Path(carpeta+"\\inputs")
        files = [f.name for f in folder_path.iterdir() if f.is_file() and "_" not in f.name]
        for i in range(self.number_cores*2):
            for k in files:
                shutil.copyfile(carpeta+"\\inputs\\"+k, carpeta+"\\inputs\\"+k.replace("uncertainity",f"uncertainity_{i}"))
        #Replicate executables
        carpeta_bat = self.plugin_directory+"\\executables"
        for core in range(self.number_cores*2):
            #Execution UH
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_uh_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_uh_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\uncertainity\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\uh" uncertainity_{core}.lis'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
            #Execution VFS
            shutil.copyfile(carpeta_bat+"\\execution.bat", carpeta_bat+"\\"+f"execution_vfs_{core}.bat")
            f = open(carpeta_bat+"\\"+f"execution_vfs_{core}.bat","w+")
            linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\uncertainity\\"')
            linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" uncertainity_{core}.prj'
            linea_tres = "Pause"
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.write("{} \n".format(linea_tres))
            f.close()
            
    
    def create_folder_sensitivity_analysis(self):
        """Method to create the folder needed to sensitivity analysis"""
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.dlg_base.working_directory_vfsmod.text()
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
            
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\sensitivity"):
            create_folder("sensitivity")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\sensitivity\inputs"):
            create_folder("sensitivity\inputs")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\sensitivity\output"):
            create_folder("sensitivity\output")
    
    def create_folder_uncertainity_analysis(self):
        """Method to create the folder needed to uncertainity analysis"""
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.dlg_base.working_directory_vfsmod.text()
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
            
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+r"\uncertainity"):
            create_folder("uncertainity")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+r"\uncertainity\inputs"):
            create_folder("uncertainity\inputs")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+r"\uncertainity\output"):
            create_folder("uncertainity\output")
    
    
    def update_bat_uh_sensitivity(self):
        """Method to update the bat for execution of UH for sensitivity analysis"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\sensitivity\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\uh" sensitivity.lis'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    def update_bat_uh_uncertainity(self):
        """Method to update the bat for execution of UH for uncertainity analysis"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\uncertainity\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\uh" uncertainity.lis'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    def update_bat_vfs_sensitivity(self):
        """Method to update the bat for execution of VFS for sensitivity analysis"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\sensitivity\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" sensitivity.prj'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
        
    def update_bat_vfs_uncertainity(self):
        """Method to update the bat for execution of VFS for uncertainity analysis"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\uncertainity\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" uncertainity.prj'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    
    def create_dictionary_uncertainity_analysis(self):
        """Method to create the dictionary that will contain the parameters of the uncertainity analysis"""
        #Functions to convert user specified inputs into inputs that SALib can read
        def distribution_parameters_fun(row):
            if str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Uniform":
                distribution = "unif"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Logaritmic uniform":
                distribution = "logunif"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Triangular":
                distribution = "triang"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Normal":
                distribution = "norm"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Normal truncated":
                distribution = "truncnorm"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.dlg_base.table_uncertainity.item(row, 1).text()) == "Lognormal":
                distribution = "lognorm"
                texto = str(self.dlg_base.table_uncertainity.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            return distribution, parameters
            
        #Diccionario nombre en el diálogo - [parametros del análisis de sensibilidad]
        dic_data = {}
        for i in range(self.dlg_base.table_uncertainity.rowCount()):
            #Diccionario [Parametro] = (Distribucion, Parametros)
            name = self.dlg_base.table_uncertainity.item(i, 0).text()
            #Obtain name of distribution and parameters
            dis,param = distribution_parameters_fun(i)
            dic_data[name] = [dis,param]
        return dic_data
        
    def create_dictionary_sensitivity_analysis(self):
        """Method to create the dictionary that will contain the parameters of the sensitivity analysis"""
        #Functions to convert user specified inputs into inputs that SALib can read
        if self.dlg_base.oat.isChecked():
            dic_data = {}
            for i in range(self.dlg_base.table_oat.rowCount()):
                name = self.dlg_base.table_oat.item(i, 0).text()
                base = float(self.dlg_base.table_oat.item(i, 1).text().split(",")[0].split(":")[-1])
                minimum = float(self.dlg_base.table_oat.item(i, 1).text().split(",")[1].split(":")[-1])
                maximum = float(self.dlg_base.table_oat.item(i, 1).text().split(",")[2].split(":")[-1])
                increment = float(self.dlg_base.table_oat.item(i, 1).text().split(",")[3].split(":")[-1])
                values = [base]
                value = minimum
                while True:
                    values.append(value)
                    value += increment
                    if value>maximum:
                        break
                dic_data[name] = values
            return dic_data
        else:
            def distribution_parameters_fun(row):
                if str(self.dlg_base.table.item(row, 1).text()) == "Uniform":
                    distribution = "unif"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                elif str(self.dlg_base.table.item(row, 1).text()) == "Logaritmic uniform":
                    distribution = "logunif"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                elif str(self.dlg_base.table.item(row, 1).text()) == "Triangular":
                    distribution = "triang"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                elif str(self.dlg_base.table.item(row, 1).text()) == "Normal":
                    distribution = "norm"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                elif str(self.dlg_base.table.item(row, 1).text()) == "Normal truncated":
                    distribution = "truncnorm"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                elif str(self.dlg_base.table.item(row, 1).text()) == "Lognormal":
                    distribution = "lognorm"
                    texto = str(self.dlg_base.table.item(row, 2).text())
                    parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
                return distribution, parameters
            
            #Diccionario nombre en el diálogo - [parametros del análisis de sensibilidad]
            dic_data = {}
            for i in range(self.dlg_base.table.rowCount()):
                #Diccionario [Parametro] = (Distribucion, Parametros)
                name = self.dlg_base.table.item(i, 0).text()
                #Obtain name of distribution and parameters
                dis,param = distribution_parameters_fun(i)
                dic_data[name] = [dis,param]
            
            return dic_data
    
    def distribution_parameters(self):
        """Method to add/delete new labels depending on choosed distribution"""
        distribution = [self.dlg_base.distributions.itemText(i) for i in range(self.dlg_base.distributions.count())][self.dlg_base.distributions.currentIndex()]
        
        # Obtén el número de filas actual en el GridLayout
        numRows = self.dlg_base.gridLayout_81.rowCount()
        
        def delete_elements():
            try:
                widget = self.dlg_base.third
                self.dlg_base.gridLayout_81.removeWidget(widget)
                widget.deleteLater()
                widget = self.dlg_base.third_label
                self.dlg_base.gridLayout_81.removeWidget(widget)
                widget.deleteLater()
            except:
                pass
            try:
                widget = self.dlg_base.fourth
                self.dlg_base.gridLayout_81.removeWidget(widget)
                widget.deleteLater()
                widget = self.dlg_base.fourth_label
                self.dlg_base.gridLayout_81.removeWidget(widget)
                widget.deleteLater()
            except:
                pass
        if self.dlg_base.oat.isChecked():
            #Primero se borra
            delete_elements()
            #Luego se añade
            # Crea un nuevo QLabel y QLineEdit
            self.dlg_base.third_label = QLabel("Maximum value")
            self.dlg_base.third = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third_label, 4, 0)
            self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third, 4, 1)
            
            # Crea un nuevo QLabel y QLineEdit
            self.dlg_base.fourth_label = QLabel("Increment")
            self.dlg_base.fourth = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.dlg_base.gridLayout_81.addWidget(self.dlg_base.fourth_label, 5, 0)
            self.dlg_base.gridLayout_81.addWidget(self.dlg_base.fourth, 5, 1)
        else:
            if distribution=="Uniform":
                #Primero se borra
                delete_elements()
                
            elif distribution=="Logaritmic uniform":
                #Primero se borra
                delete_elements()
     
            elif distribution=="Triangular":
                #Primero se borra
                delete_elements()

                #Luego se añade
                # Crea un nuevo QLabel y QLineEdit
                self.dlg_base.third_label = QLabel("Peak")
                self.dlg_base.third = QLineEdit()
                # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third_label, 4, 0)
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third, 4, 1)

            elif distribution=="Normal":
                #Primero se borra
                delete_elements()
            
            if distribution=="Lognormal":
                #Primero se borra
                delete_elements()
            
            if distribution=="Normal truncated":
                #Primero se borra
                delete_elements()
                
                #Luego se añade
                # Crea un nuevo QLabel y QLineEdit
                self.dlg_base.third_label = QLabel("Mean")
                self.dlg_base.third = QLineEdit()
                # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third_label, 4, 0)
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.third, 4, 1)
                
                # Crea un nuevo QLabel y QLineEdit
                self.dlg_base.fourth_label = QLabel("Standard deviation")
                self.dlg_base.fourth = QLineEdit()
                # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.fourth_label, 5, 0)
                self.dlg_base.gridLayout_81.addWidget(self.dlg_base.fourth, 5, 1)
    
    def distribution_parameters_uncertainity(self):
        """Method to add/delete new labels depending on choosed distribution"""
        distribution = [self.dlg_base.distributions_uncertainity.itemText(i) for i in range(self.dlg_base.distributions_uncertainity.count())][self.dlg_base.distributions_uncertainity.currentIndex()]
        
        # Obtén el número de filas actual en el GridLayout
        numRows = self.dlg_base.gridLayout_84.rowCount()
        
        def delete_elements():
            try:
                widget = self.dlg_base.third_2
                self.dlg_base.gridLayout_84.removeWidget(widget)
                widget.deleteLater()
                widget = self.dlg_base.third_label_2
                self.dlg_base.gridLayout_84.removeWidget(widget)
                widget.deleteLater()
            except:
                pass
            try:
                widget = self.dlg_base.fourth_2
                self.dlg_base.gridLayout_84.removeWidget(widget)
                widget.deleteLater()
                widget = self.dlg_base.fourth_label_2
                self.dlg_base.gridLayout_84.removeWidget(widget)
                widget.deleteLater()
            except:
                pass

        if distribution=="Uniform":
            #Primero se borra
            delete_elements()
            
        elif distribution=="Logaritmic uniform":
            #Primero se borra
            delete_elements()
 
        elif distribution=="Triangular":
            #Primero se borra
            delete_elements()

            #Luego se añade
            # Crea un nuevo QLabel y QLineEdit
            self.dlg_base.third_label_2 = QLabel("Peak")
            self.dlg_base.third_2 = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.third_label_2, 5, 0)
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.third_2, 5, 1)

        elif distribution=="Normal":
            #Primero se borra
            delete_elements()
        
        if distribution=="Lognormal":
            #Primero se borra
            delete_elements()
        
        if distribution=="Normal truncated":
            #Primero se borra
            delete_elements()
            
            #Luego se añade
            # Crea un nuevo QLabel y QLineEdit
            self.dlg_base.third_label_2 = QLabel("Mean")
            self.dlg_base.third_2 = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.third_label_2, 5, 0)
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.third_2, 5, 1)
            
            # Crea un nuevo QLabel y QLineEdit
            self.dlg_base.fourth_label_2 = QLabel("Standard deviation")
            self.dlg_base.fourth_2 = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.fourth_label_2, 6, 0)
            self.dlg_base.gridLayout_84.addWidget(self.dlg_base.fourth_2, 6, 1)
            
    def change_bounds_sensitivity(self):
        """Metod to change bounds labels if distribution changed"""
        def change_lines(bound1,bound2,bound3=None,bound4=None):
            self.dlg_base.label_123.setText(bound1)
            self.dlg_base.label_121.setText(bound2)
        distribution = [self.dlg_base.distributions.itemText(i) for i in range(self.dlg_base.distributions.count())][self.dlg_base.distributions.currentIndex()]
        if self.dlg_base.oat.isChecked():
            change_lines("Base value","Minimum value","Maximum value","Increment")
        else:
            if distribution=="Uniform":
                change_lines("Minimum","Maximum")
            if distribution=="Logaritmic uniform":
                change_lines("Minimum","Maximum")
            if distribution=="Triangular":
                change_lines("Minimum","Maximum","Peak")
            if distribution=="Normal":
                change_lines("Mean","Standard deviation")
            if distribution=="Lognormal":
                change_lines("Mean","Standard deviation")
            if distribution=="Normal truncated":
                change_lines("Minimum","Maximum","Mean","Standard deviation")
    
    def change_bounds_uncertainity(self):
        """Metod to change bounds labels if distribution changed"""
        def change_lines(bound1,bound2,bound3=None,bound4 = None):
            self.dlg_base.label_141.setText(bound1)
            self.dlg_base.label_139.setText(bound2)

        distribution = [self.dlg_base.distributions_uncertainity.itemText(i) for i in range(self.dlg_base.distributions_uncertainity.count())][self.dlg_base.distributions_uncertainity.currentIndex()]
        if distribution=="Uniform":
            change_lines("Minimum","Maximum")
        if distribution=="Logaritmic uniform":
            change_lines("Minimum","Maximum")
        if distribution=="Triangular":
            change_lines("Minimum","Maximum","Peak")
        if distribution=="Normal":
            change_lines("Mean","Standard deviation")
        if distribution=="Lognormal":
            change_lines("Mean","Standard deviation")
        if distribution=="Normal truncated":
            change_lines("Minimum","Maximum","Mean","Standard deviation")
    
    def delete_sensitivity_table(self):
        """Method to delete sensitivity analysis parameters to table"""
        if self.dlg_base.oat.isChecked(): table = self.dlg_base.table_oat
        elif not self.dlg_base.oat.isChecked(): table = self.dlg_base.table
        numero_filas = table.rowCount()
        if numero_filas > 0:
            table.removeRow(numero_filas - 1)
        if numero_filas == 1:
            table.setColumnCount(0)
        
        #Update number of samples
        self.change_sensitivity_method()
    
    def delete_uncertainity_table(self):
        """Method to delete uncertainity analysis parameters to table"""
        table = self.dlg_base.table_uncertainity
        numero_filas = table.rowCount()
        if numero_filas > 0:
            table.removeRow(numero_filas - 1)
        if numero_filas == 1:
            table.setColumnCount(0)
    
    def add_sensitivity_table(self):
        """Method to add information to the sensitivity analysis table"""
        #Method to add sensitivity analysis parameters to table
        if self.dlg_base.oat.isChecked(): table = self.dlg_base.table_oat
        elif not self.dlg_base.oat.isChecked(): table = self.dlg_base.table
        
        
        if table.columnCount() == 0:
            #Añadir columnas
            if self.dlg_base.oat.isChecked(): nombres_columnas = ["Parameter","Values"]
            elif not self.dlg_base.oat.isChecked(): nombres_columnas = ["Parameter","Distribution","Distribution parameters"]
            
            table.setColumnCount(len(nombres_columnas))
            table.setHorizontalHeaderLabels(nombres_columnas)
            #Cambiar el ancho de las columnas
            if self.dlg_base.oat.isChecked():
                table.setColumnWidth(nombres_columnas.index("Parameter"), 180)
                table.setColumnWidth(nombres_columnas.index("Values"), 300)
            elif not self.dlg_base.oat.isChecked():
                table.setColumnWidth(nombres_columnas.index("Parameter"), 180)
                table.setColumnWidth(nombres_columnas.index("Distribution parameters"), 200)
            
        #Añadir filas
        def add_element(columna,texto):
            item = QTableWidgetItem(texto)
            table.setItem(numero_filas, columna, item)
            item.setTextAlignment(Qt.AlignCenter)
        
        #Primero la información de los lineEdits
        numero_filas = table.rowCount()
        table.setRowCount(numero_filas + 1)
        #Add parameter
        add_element(0,self.dlg_base.parameter_name.text())
        #Add distribution
        distribution = [self.dlg_base.distributions.itemText(i) for i in range(self.dlg_base.distributions.count())][self.dlg_base.distributions.currentIndex()]
        if not self.dlg_base.oat.isChecked():
            add_element(1,distribution)
        #Add distribution parameters
        if self.dlg_base.oat.isChecked():
            add_element(1,f"base:{self.dlg_base.first.text()},min:{self.dlg_base.second.text()},max:{self.dlg_base.third.text()},increment:{self.dlg_base.fourth.text()}")
        elif not self.dlg_base.oat.isChecked():
            if distribution=="Uniform" or distribution=="Logaritmic uniform":
                add_element(2,f"min:{self.dlg_base.first.text()},max:{self.dlg_base.second.text()}")
            elif distribution == "Triangular":
                add_element(2,f"min:{self.dlg_base.first.text()},max:{self.dlg_base.second.text()},peak:{self.dlg_base.third.text()}")
            elif distribution == "Normal" or distribution == "Lognormal":
                add_element(2,f"mean:{self.dlg_base.first.text()},stdv:{self.dlg_base.second.text()}")
            elif distribution == "Normal truncated":
                add_element(2,f"min:{self.dlg_base.first.text()},max:{self.dlg_base.second.text()},mean:{self.dlg_base.third.text()},stdv:{self.dlg_base.fourth.text()}")
            
            #Update number of samples
            self.change_sensitivity_method()
    
    def add_uncertainity_table(self):
        """Method to add information to the sensitivity analysis table"""
        #Method to add uncertainity analysis parameters to table

        table = self.dlg_base.table_uncertainity
        
        if table.columnCount() == 0:
            #Añadir columnas
            nombres_columnas = ["Parameter","Distribution","Distribution parameters"]
            
            table.setColumnCount(len(nombres_columnas))
            table.setHorizontalHeaderLabels(nombres_columnas)
            #Cambiar el ancho de las columnas
            table.setColumnWidth(nombres_columnas.index("Parameter"), 180)
            table.setColumnWidth(nombres_columnas.index("Distribution parameters"), 200)
            
        #Añadir filas
        def add_element(columna,texto):
            item = QTableWidgetItem(texto)
            table.setItem(numero_filas, columna, item)
            item.setTextAlignment(Qt.AlignCenter)
        
        #Primero la información de los lineEdits
        numero_filas = table.rowCount()
        table.setRowCount(numero_filas + 1)
        #Add parameter
        add_element(0,self.dlg_base.parameter_name_uncertainity.text())
        #Add distribution
        distribution = [self.dlg_base.distributions_uncertainity.itemText(i) for i in range(self.dlg_base.distributions_uncertainity.count())][self.dlg_base.distributions_uncertainity.currentIndex()]
        add_element(1,distribution)
        if distribution=="Uniform" or distribution=="Logaritmic uniform":
            add_element(2,f"min:{self.dlg_base.first_2.text()},max:{self.dlg_base.second_2.text()}")
        elif distribution == "Triangular":
            add_element(2,f"min:{self.dlg_base.first_2.text()},max:{self.dlg_base.second_2.text()},peak:{self.dlg_base.third_2.text()}")
        elif distribution == "Normal" or distribution == "Lognormal":
            add_element(2,f"mean:{self.dlg_base.first_2.text()},stdv:{self.dlg_base.second_2.text()}")
        elif distribution == "Normal truncated":
            add_element(2,f"min:{self.dlg_base.first_2.text()},max:{self.dlg_base.second_2.text()},mean:{self.dlg_base.third_2.text()},stdv:{self.dlg_base.fourth_2.text()}")
            
    
    def change_sensitivity_method(self):
        """Method to change sensitivity inputs depending on selected senstitivity metod"""
        if self.dlg_base.sobol.isChecked():
            self.dlg_base.label_125.setText("M")
            try:
                if self.dlg_base.trajectories.text()=="" or self.dlg_base.table.rowCount()==0:
                    self.dlg_base.samples.setText("")
                else:
                    self.dlg_base.samples.setText(str(int(self.dlg_base.trajectories.text())*(2*self.dlg_base.table.rowCount()+2)))
            except:
                pass
        elif self.dlg_base.morris.isChecked():
            self.dlg_base.label_125.setText("Trajectories")
            try:
                if self.dlg_base.trajectories.text()=="" or self.dlg_base.table.rowCount()==0:
                    self.dlg_base.samples.setText("")
                else:
                    self.dlg_base.samples.setText(str(int(self.dlg_base.trajectories.text())*(self.dlg_base.table.rowCount()+1)))
            except:
                pass
        elif self.dlg_base.fast.isChecked():
            self.dlg_base.label_125.setText("N")
            try:
                if self.dlg_base.trajectories.text()=="" or self.dlg_base.table.rowCount()==0:
                    self.dlg_base.samples.setText("")
                else:
                    self.dlg_base.samples.setText(str(int(self.dlg_base.trajectories.text())*(self.dlg_base.table.rowCount())))
            except:
                pass
    
    def search_sensitivity_parameter(self):
        """Method to search sensitivity parameter in the dialog"""
        #Metod to search a sensitiviy input
        texto = str(self.dlg_base.search.text())
        #If text == "" then delete every button
        if texto =="":
            while self.dlg_base.verticalLayout_19.count():
                child = self.dlg_base.verticalLayout_19.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            elementos = []
            for i in self.sensitivity_parameters.keys():
                if texto.lower() in i.lower():
                    elementos.append(i)
            try: #if it doesnt find a name
                #Delete all elements of vertical layout of scroll area
                while self.dlg_base.verticalLayout_19.count():
                    child = self.dlg_base.verticalLayout_19.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                #Add new button to the scroll area
                for nombre in elementos:
                    boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                    boton.setObjectName(nombre)
                    self.dlg_base.verticalLayout_19.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
            except:
                pass
    
    
    def search_uncertainity_parameter(self):
        """Method to search sensitivity parameter in the dialog"""
        #Metod to search a sensitiviy input
        texto = str(self.dlg_base.search_uncertainity.text())
        #If text == "" then delete every button
        if texto =="":
            while self.dlg_base.verticalLayout_21.count():
                child = self.dlg_base.verticalLayout_21.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            elementos = []
            for i in self.sensitivity_parameters.keys():
                if texto.lower() in i.lower():
                    elementos.append(i)
            try: #if it doesnt find a name
                #Delete all elements of vertical layout of scroll area
                while self.dlg_base.verticalLayout_21.count():
                    child = self.dlg_base.verticalLayout_21.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                #Add new button to the scroll area
                for nombre in elementos:
                    boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                    boton.setObjectName(nombre)
                    self.dlg_base.verticalLayout_21.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
            except:
                pass
    
    def show_buttons_sensitivity_dialog(self,button):
        """Method to add buttons to sensitivity dialog"""
        #Delete all elements of vertical layout of scroll area
        while self.dlg_base.verticalLayout_19.count():
            child = self.dlg_base.verticalLayout_19.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        #Add element
        if button == self.dlg_base.all_parameters:
            for nombre in self.sensitivity_parameters.keys():
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
        if button == self.dlg_base.rainfall_event:
            parameters = ["Rainfall (mm)","Storm duration (h)","Curve number"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.source_area:
            parameters = ["Source Area Length along the slope (m)", "Source Area Slope as a fraction","Source Area (ha)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.erosion_parameters:
            parameters = ["Soil erodibility (K)","Percent organic matter","Crop factor","Particle Class Diameter","Practice Factor"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.buffer_dimensions:
            parameters = ["Buffer length (m)","Width of the Strip (m)","Filter Manning n (RNA s/m^1/3)","Average Filter Slope"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.kinematic_wave:
            parameters = ["Number of Nodes","Time Weight Factor","Number of Elemental Nodal Points","Courant Number","Maximum Iterations"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.infiltration:
            parameters = ["Vertical Saturated K","Average Suction at the Wetting Front","Initial Water Content","Saturated Water Content","Maximum Surface Storage","Fraction of the filter where ponding is checked"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.buffer_vegetation:
            parameters = ["Spacing for grass stems (cm)","Roughness-Grass Mannings n VN","Height of grass (cm)","Roughness-Bare surface Mannings n (Vn2)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
                
        if button == self.dlg_base.incoming_sediment:
            parameters = ["Incoming flow sediment concentration (g/cm^3)","Sediment particle size diameter d50 (cm)","Porosity of deposited sediment as a fraction","Portion of Particles from incoming sediment \nwith diameter >0.0037 cm","Sediment particle density (g/cm^3)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
        
        if button == self.dlg_base.water_quality_button:
            parameters = ["Linear sorption coefficient (L/Kg)","Adsorption coefficient (L/Kg)","Organic Carbon (%)","Clay in incoming sediment (%)","Pesticide half-life (days)","Topsoil field capacity (m3/m3)","Total pesticide mass per unit area source field (mg/m2)","Surface mixing layer thickness (cm)","Dispersion length of chemical (m)","Runoff remobilized VFS residue \nfrom last event (mg/m2)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_12)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_19.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))
    
    def show_buttons_uncertainity_dialog(self,button):
        """Method to add buttons to uncertainity dialog"""
        #Delete all elements of vertical layout of scroll area
        while self.dlg_base.verticalLayout_21.count():
            child = self.dlg_base.verticalLayout_21.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        #Add element
        if button == self.dlg_base.all_parameters_2:
            for nombre in self.sensitivity_parameters.keys():
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
        if button == self.dlg_base.rainfall_event_2:
            parameters = ["Rainfall (mm)","Storm duration (h)","Curve number"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.source_area_2:
            parameters = ["Source Area Length along the slope (m)", "Source Area Slope as a fraction","Source Area (ha)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.erosion_parameters_2:
            parameters = ["Soil erodibility (K)","Percent organic matter","Crop factor","Particle Class Diameter","Practice Factor"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.buffer_dimensions_2:
            parameters = ["Buffer length (m)","Width of the Strip (m)","Filter Manning n (RNA s/m^1/3)","Average Filter Slope"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.kinematic_wave_2:
            parameters = ["Number of Nodes","Time Weight Factor","Number of Elemental Nodal Points","Courant Number","Maximum Iterations"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.infiltration_2:
            parameters = ["Vertical Saturated K","Average Suction at the Wetting Front","Initial Water Content","Saturated Water Content","Maximum Surface Storage","Fraction of the filter where ponding is checked"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.buffer_vegetation_2:
            parameters = ["Spacing for grass stems (cm)","Roughness-Grass Mannings n VN","Height of grass (cm)","Roughness-Bare surface Mannings n (Vn2)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
                
        if button == self.dlg_base.incoming_sediment_2:
            parameters = ["Incoming flow sediment concentration (g/cm^3)","Sediment particle size diameter d50 (cm)","Porosity of deposited sediment as a fraction","Portion of Particles from incoming sediment \nwith diameter >0.0037 cm","Sediment particle density (g/cm^3)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_uncertainity(b))
        
        if button == self.dlg_base.water_quality_button_2:
            parameters = ["Linear sorption coefficient (L/Kg)","Adsorption coefficient (L/Kg)","Organic Carbon (%)","Clay in incoming sediment (%)","Pesticide half-life (days)","Topsoil field capacity (m3/m3)","Total pesticide mass per unit area source field (mg/m2)","Surface mixing layer thickness (cm)","Dispersion length of chemical (m)","Runoff remobilized VFS residue \nfrom last event (mg/m2)"]
            for nombre in parameters:
                boton = QtWidgets.QPushButton(nombre, self.dlg_base.scrollAreaWidgetContents_15)
                boton.setObjectName(nombre)
                self.dlg_base.verticalLayout_21.addWidget(boton)
                politica_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(politica_tamaño)
                boton.clicked.connect(lambda _, b = nombre: self.add_parameter_name_sensitivity(b))

    def add_parameter_name_sensitivity(self,name):
        """Method to add the parameter name to the lineEdit in sensitivity analysis dialog"""
        self.dlg_base.parameter_name.setText(name)
    
    def add_parameter_name_uncertainity(self,name):
        """Method to add the parameter name to the lineEdit in sensitivity analysis dialog"""
        self.dlg_base.parameter_name_uncertainity.setText(name)
    
    def browse_files_calibration(self,information):
        """Method to select the file between the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        if information[0]=="prj": 
            select = "Select VFS Project File"
            types = "PRJ files (*.prj)"
        elif information[2]==self.dlg_base.hydrograph_file: select = "Select Hydrograph Measured Data File"
        else: select = "Select Sedimentograph Measured Data File"
        if information[0]=="txt": 
            types = "TXT files (*.txt)"
        fname = QFileDialog.getOpenFileName(information[1], select,working_directory , types)
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                information[2].setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                information[2].setText(fname[0])
    
    def run_calibration_sedimentograph(self):
        """Method to run the calibration for sedimentograph"""
        self.calibration_sedimentograph = True
        #Obtain dataframe of sedimentograph
        self.sedimentograph_calibration_df = self.obtain_df_sedimentograph_calibration()
        
        #First, put the progress
        self.calibration_execution_progress_sedimentograph([0,])
        
        #If "inverse" folder does not exist, then create it
        self.create_folder_calibration()
        
        #Move prj to the inverse folder and in inverse/inputs put the inputs
        self.move_files_calibration_sedimentograph()
        
        #Create the dictionary to know the bounds of the input parameters
        self.calibration_dictionary = self.create_dictionary_calibration_sedimentograph()
        
        #first we create the thread class to be able to use the dialog when executing
        class ejecutor(QThread):
            resultado_progress = pyqtSignal(list)
            def __init__(self, plugin_directory, method_execution,dictionary,max_iterations,tolerance,save_results_calibration):
                super().__init__()
                self.plugin_directory = plugin_directory
                self.execution_calibration_sedimentograph = method_execution
                self.dictionary = dictionary
                self.best_result = {"x":None,"result":None} #save results of calibration iteration
                self.list_of_inputs = []
                self.list_of_results = []
                self.max_iterations = int(max_iterations)
                self.tolerance = float(tolerance)
                self.save_results_calibration = save_results_calibration
                
            def run(self):
                #Method to update progress in the optimization
                self.ejecuciones = 0 
                def objetivo(x):
                    result = self.execution_calibration_sedimentograph(x)
                    # Emitir la señal con el número de ejecuciones y el resultado
                    self.ejecuciones += 1
                    self.resultado_progress.emit([self.ejecuciones, float(result)])
                    #Save the best result if it is the first run or if it improves on the current best result
                    if self.best_result["result"] is None or result < self.best_result["result"]:
                        self.best_result["x"] = x
                        self.best_result["result"] = result
                        
                    if self.ejecuciones == self.max_iterations or result == "error": #condition of maximum number of iterations to stop the code
                        1/0
                    #Save inputs and results
                    self.list_of_inputs.append(x)
                    self.list_of_results.append(result)
                    
                    
                    return result   
                    
                #Limits to the calibration
                limites = list(self.dictionary.values())
                #Global calibration
                try:
                    resultado_global = differential_evolution(objetivo, bounds=limites, strategy='best1bin',tol=self.tolerance)
                except ZeroDivisionError: #maximum iterations achieved
                    self.resultado_progress.emit(["Warning","Maximum iterations achieved \n Adding best result...\n"])
                    objetivo(self.best_result["x"]) #execute best just so that users can see it
                    self.list_of_inputs[:-1] #eilminate last one
                    self.list_of_results[:-1]
                    
                #Message end global calibration
                self.resultado_progress.emit(["Warning","Calibration ended"])
                
                #Save results
                self.save_results_calibration(self.list_of_inputs,self.list_of_results)
                
        self.worker = ejecutor(self.plugin_directory, self.execution_calibration_sedimentograph,self.calibration_dictionary,
            self.dlg_calibration_advanced_settings.max_iterations.text(),self.dlg_calibration_advanced_settings.tolerance.text(),
            self.save_results_calibration)
        self.worker.start()
        self.worker.resultado_progress.connect(self.calibration_execution_progress_sedimentograph)
    
    
    def change_base_inputs_calibration_sedimentograph(self,inputs):
        """Method to change the inputs in the calibration of sedimentograph if change is selected"""
        #spacing
        if inputs[0]=="change":
            self.modify_inputs_calibration("igr",0,0,self.dlg_base.new_spacing.text())
        #roughness grass
        if inputs[1]=="change":
            self.modify_inputs_calibration("igr",0,1,self.dlg_base.new_roughness.text())
        #height
        if inputs[2]=="change":
            self.modify_inputs_calibration("igr",0,2,self.dlg_base.new_height.text())
        #roughness bare
        if inputs[3]=="change":
            self.modify_inputs_calibration("igr",0,3,self.dlg_base.new_bare.text())
        #coarse
        if inputs[4]=="change":
            self.modify_inputs_calibration("isd",0,1,self.dlg_base.new_coarse.text())
        #incoming
        if inputs[5]=="change":
            self.modify_inputs_calibration("isd",0,2,self.dlg_base.new_incoming.text())
        #porosity
        if inputs[6]=="change":
            self.modify_inputs_calibration("isd",0,3,self.dlg_base.new_porosity.text())
        #sediment_class
        if inputs[7]=="change":
            self.modify_inputs_calibration("isd",1,0,self.dlg_base.new_class.text())
        #sediment_density
        if inputs[8]=="change":
            self.modify_inputs_calibration("isd",1,1,self.dlg_base.new_density.text())
        
    
    def move_files_calibration_sedimentograph(self):
        """Method to move files to the corresponding folders for calibration"""
        #Move sedimentograph
        try:
            shutil.copyfile(self.obtain_direction_vfsmod(self.dlg_base.sedimentograph_file.text()),self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\{os.path.basename(self.dlg_base.sedimentograph_file.text())}")
        except SameFileError:
            pass
            
        #Prj
        prj_file = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inverse.prj"
        #Check if water quality is simulated
        with open(self.obtain_direction_vfsmod(self.dlg_base.vfs_file.text()), "r") as archivo:
            lineas = archivo.readlines()
        self.water_quality = False
        for i in lineas:
            if i[:3]=="iwq":
                self.water_quality = True
            
        #Create file
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw=inputs\\inverse.ikw  \n")
            archivo.write(f"iso=inputs\\inverse.iso  \n")
            archivo.write(f"igr=inputs\\inverse.igr  \n")
            archivo.write(f"isd=inputs\\inverse.isd  \n")
            archivo.write(f"irn=inputs\\inverse.irn  \n")
            archivo.write(f"iro=inputs\\inverse.iro  \n")
            if self.water_quality:
                archivo.write(f"iwq=inputs\\inverse.iwq  \n")
            archivo.write(f"og1=output\\inverse.og1  \n")
            archivo.write(f"og2=output\\inverse.og2  \n")
            archivo.write(f"ohy=output\\inverse.ohy  \n")
            archivo.write(f"osm=output\\inverse.osm  \n")
            archivo.write(f"osp=output\\inverse.osp  \n")
            if self.water_quality:
                archivo.write(f"owq=output\\inverse.owq  \n")
        
        #UH
        lis_file = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inverse.lis"
        #Create file
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp=inputs\\inverse.inp  \n")
            archivo.write(f"iro=inputs\\inverse.iro  \n")
            archivo.write(f"irn=inputs\\inverse.irn  \n")
            archivo.write(f"isd=inputs\\inverse.isd  \n")
            archivo.write(f"out=inputs\\inverse.out  \n")
            archivo.write(f"hyt=inputs\\inverse.hyt  \n")
        
        #REST OF THE FILES
        #Function to copy and paste the inputs to create the files to use in the design analysis
        def copy_paste(type_input):
            ruta_pegar = self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\inputs\\inverse.{type_input}" 
            ruta = self.obtain_direction_vfsmod(self.dlg_base.vfs_file.text())
            if os.path.exists(ruta) and os.path.isfile(ruta):
                #First we open .prj and obtain the direction of the copying file
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==type_input:
                        ikw = i.split("=")[-1]
                if not os.path.isabs(ikw): #relative path
                    ikw = os.path.join(os.path.dirname(ruta), ikw)
                ikw = ikw.replace("\n", "") #take out the line jumps
                shutil.copyfile(ikw, ruta_pegar)
        
        #IKW
        copy_paste("ikw")
        #ISO
        copy_paste("iso")
        #IGR
        copy_paste("igr")
        #ISD
        copy_paste("isd")
        #IRN
        copy_paste("irn")
        #IRO
        copy_paste("iro")
        #IWQ
        if self.water_quality:
            copy_paste("iwq")
    
    def run_calibration_hydrograph(self):
        """Method to run the calibration for hydrograph"""
        self.calibration_hydrograph = True
        #Obtain dataframe of hydrograph
        self.hydrograph_calibration_df = self.obtain_df_hydrograph_calibration()
        #First, put the progress
        self.calibration_execution_progress_hydrograph([0,])
        
        #If "inverse" folder does not exist, then create it
        self.create_folder_calibration()
        
        #Move prj to the inverse folder and in inverse/inputs put the inputs
        self.move_files_calibration_hydrograph()
        
        #Create the dictionary to know the bounds of the input parameters
        self.calibration_dictionary = self.create_dictionary_calibration_hydrograph()
        
            
        #first we create the thread class to be able to use the dialog when executing
        class ejecutor(QThread):
            resultado_progress = pyqtSignal(list)
            def __init__(self, plugin_directory, method_execution,dictionary,max_iterations,tolerance,save_results_calibration):
                super().__init__()
                self.plugin_directory = plugin_directory
                self.execution_calibration_hydrograph = method_execution
                self.dictionary = dictionary
                self.best_result = {"x":None,"result":None} #save results of calibration iteration
                self.list_of_inputs = []
                self.list_of_results = []
                self.max_iterations = int(max_iterations)
                self.tolerance = float(tolerance)
                self.save_results_calibration = save_results_calibration
                
            def run(self):
                #Method to update progress in the optimization
                self.ejecuciones = 0 
                def objetivo(x):
                    result = self.execution_calibration_hydrograph(x)
                    # Emitir la señal con el número de ejecuciones y el resultado
                    self.ejecuciones += 1
                    self.resultado_progress.emit([self.ejecuciones, float(result)])
                    #Save the best result if it is the first run or if it improves on the current best result
                    if self.best_result["result"] is None or result < self.best_result["result"]:
                        self.best_result["x"] = x
                        self.best_result["result"] = result
                        
                    if self.ejecuciones == self.max_iterations or results == "error": #condition of maximum number of iterations to stop the code
                        1/0
                    #Save inputs and results
                    self.list_of_inputs.append(x)
                    self.list_of_results.append(result)
                    
                    
                    return result   
                    
                #Limits to the calibration
                limites = list(self.dictionary.values())
                #Global calibration
                try:
                    resultado_global = differential_evolution(objetivo, bounds=limites, strategy='best1bin',tol=self.tolerance)
                except ZeroDivisionError: #maximum iterations achieved
                    self.resultado_progress.emit(["Warning","Maximum iterations achieved \n Adding best result...\n"])
                    objetivo(self.best_result["x"]) #execute best just so that users can see it
                    self.list_of_inputs[:-1] #eilminate last one
                    self.list_of_results[:-1]
                    
                #Message end global calibration
                self.resultado_progress.emit(["Warning","Calibration ended"])
                
                #Save results
                self.save_results_calibration(self.list_of_inputs,self.list_of_results)
                
        self.worker = ejecutor(self.plugin_directory, self.execution_calibration_hydrograph,self.calibration_dictionary,
            self.dlg_calibration_advanced_settings.max_iterations.text(),self.dlg_calibration_advanced_settings.tolerance.text(),
            self.save_results_calibration)
        self.worker.start()
        self.worker.resultado_progress.connect(self.calibration_execution_progress_hydrograph)
    
    
    def obtain_df_hydrograph_calibration(self):
        """Method to obtain the dataframe of the hydrograph to be used in the calibration"""
        ruta = self.obtain_direction_vfsmod(self.dlg_base.hydrograph_file.text())
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        discharge = []
        times = []
        for i in lineas:
            discharge.append(float(i.split()[1]))
            times.append(float(i.split()[0]))
        df = pd.DataFrame(data = {"Time":times,"Discharge":discharge})
        return df
    
    def obtain_df_sedimentograph_calibration(self):
        """Method to obtain the dataframe of the sedimentograph to be used in the calibration"""
        ruta = self.obtain_direction_vfsmod(self.dlg_base.sedimentograph_file.text())
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        sediment = []
        times = []
        for i in lineas:
            sediment.append(float(i.split()[1]))
            times.append(float(i.split()[0]))
        df = pd.DataFrame(data = {"Time":times,"Sediment":sediment})
        return df

    
    def execution_calibration_hydrograph(self, input_parameters):
        """Method to change inputs of calibration and execute"""
        #First we translate the inputs of that method to a way so can it can be used
        dic_inputs = {}
        for k,i in enumerate(self.calibration_dictionary.keys()):
            dic_inputs[i]= input_parameters[k]
        #Modify inputs
        for i in dic_inputs.keys():
            #vertical
            if i=="vertical":
                self.modify_inputs_calibration("iso",0,0,dic_inputs[i])
            #average
            elif i=="average":
                self.modify_inputs_calibration("iso",0,1,dic_inputs[i])
            #saturated
            elif i=="saturated":
                self.modify_inputs_calibration("iso",0,2,dic_inputs[i])
            #initial
            elif i=="initial":
                self.modify_inputs_calibration("iso",0,3,dic_inputs[i])
            #maximum
            elif i=="maximum":
                self.modify_inputs_calibration("iso",0,4,dic_inputs[i])
            #fraction
            elif i=="fraction":
                self.modify_inputs_calibration("iso",0,5,dic_inputs[i])
            #width
            elif i=="width":
                self.modify_inputs_calibration("ikw",1,0,dic_inputs[i])
            #length
            elif i=="length":
                self.modify_ikw_file_calibration(dic_inputs[i])
            #manning
            elif i=="manning":
                self.modify_mannign_slope_hydrograph_calibration(1,dic_inputs[i])
            #slope
            elif i=="slope":
                self.modify_mannign_slope_hydrograph_calibration(2,dic_inputs[i])
        #Update bat for calibration
        self.update_bat_calibration()
        #Execute
        resultado = subprocess.run([self.plugin_directory+"\\executables\\execution.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        #Put warning
        if not "...FINISHED..." in resultado.stdout:
            self.warning_message(str(resultado.stdout))
            return "error"
        #Read output
        ruta = self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\output\\inverse.ohy"
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        discharge = []
        times = []
        for i in range(len(lineas)):
            if lineas[i]=="     TIME     OUTFLOW    CUM.FLOW     ie =r-f     INFLOW    CUM.INFLOW       f          z        ITER\n":
                for k in range(i+3,len(lineas)):
                    times.append(float(lineas[k].split()[0]))
                    discharge.append(float(lineas[k].split()[1]))
        self.calibration_df_progress = pd.DataFrame(data = {"Time":times,"Discharge":discharge})
        
        
        #Obtain interpolated dataframe
        calibration_df_progress = self.calibration_df_progress.copy()
        calibration_df_progress.set_index('Time', inplace=True)
        hydrograph_calibration_df = self.hydrograph_calibration_df.copy()
        hydrograph_calibration_df.set_index('Time', inplace=True)
        
        #Do the interpolation
        # Crear un nuevo DataFrame para los resultados
        data_aligned = pd.DataFrame(index=calibration_df_progress.index)
        
        
        # Rellenar b_aligned con los valores de b o interpolados
        for idx in calibration_df_progress.index:
            if idx in hydrograph_calibration_df.index:
                data_aligned.loc[idx, 'Discharge'] = hydrograph_calibration_df.loc[idx, 'Discharge']
            else:
                lower_index = hydrograph_calibration_df.index[hydrograph_calibration_df.index < idx]
                upper_index = hydrograph_calibration_df.index[hydrograph_calibration_df.index > idx]
                
                if len(lower_index) > 0 and len(upper_index) > 0:
                    # Hay índices válidos para interpolar
                    lower_idx = lower_index[-1]  # Último índice inferior
                    upper_idx = upper_index[0]    # Primer índice superior
                    
                    # Interpolación lineal
                    lower_value = hydrograph_calibration_df.loc[lower_idx, 'Discharge']
                    upper_value = hydrograph_calibration_df.loc[upper_idx, 'Discharge']
                    # Calcular el valor interpolado
                    interpolated_value = lower_value + (upper_value - lower_value) * ((idx - lower_idx) / (upper_idx - lower_idx))
                    data_aligned.loc[idx, 'Discharge'] = interpolated_value
                else:
                    # Si no hay índices cercanos, dejar como NaN
                    data_aligned.loc[idx, 'Discharge'] = float('nan')
        
        
        #Save dataframe for the results
        self.data_aligned = data_aligned
        
        #Calculate objective function
        self.objective_function = [self.dlg_calibration_advanced_settings.objective_function.itemText(i) for i in range(self.dlg_calibration_advanced_settings.objective_function.count())][self.dlg_calibration_advanced_settings.objective_function.currentIndex()]
        if  self.objective_function== "RMSE":
            #Calculate RMSE
            diferencias = calibration_df_progress['Discharge'] - data_aligned['Discharge']
            #Calculate squared differenes
            cuadrados_diferencias = diferencias ** 2
            resultado_total = cuadrados_diferencias.sum()
            return resultado_total
        
        elif self.objective_function == "NSE":
            diferencias = calibration_df_progress['Discharge'] - data_aligned['Discharge']
            cuadrados_diferencias = diferencias ** 2
            suma_cuadrados_diferencias = cuadrados_diferencias.sum()
            media_observados = data_aligned['Discharge'].mean()
            diferencias_media_observados = data_aligned['Discharge'] - media_observados
            cuadrados_diferencias_observados = diferencias_media_observados ** 2
            suma_cuadrados_diferencias_observados = cuadrados_diferencias_observados.sum()
            nash_sutcliffe_efficiency = 1 - (suma_cuadrados_diferencias / suma_cuadrados_diferencias_observados)
            return -nash_sutcliffe_efficiency #the calibration function minimizes values, thats why -

        elif self.objective_function == "NNSE":
            diferencias = calibration_df_progress['Discharge'] - data_aligned['Discharge']
            cuadrados_diferencias = diferencias ** 2
            suma_cuadrados_diferencias = cuadrados_diferencias.sum()
            media_observados = data_aligned['Discharge'].mean()
            diferencias_media_observados = data_aligned['Discharge'] - media_observados
            cuadrados_diferencias_observados = diferencias_media_observados ** 2
            suma_cuadrados_diferencias_observados = cuadrados_diferencias_observados.sum()
            nash_sutcliffe_efficiency = 1 - (suma_cuadrados_diferencias / suma_cuadrados_diferencias_observados)
            nnse = 1/(2-nash_sutcliffe_efficiency)
            return -nnse #the calibration function minimizes values, thats why -
    
    def execution_calibration_sedimentograph(self, input_parameters):
        """Method to change inputs of calibration and execute"""
        #First we translate the inputs of that method to a way so can it can be used
        dic_inputs = {}
        for k,i in enumerate(self.calibration_dictionary.keys()):
            dic_inputs[i]= input_parameters[k]
        #Modify inputs
        for i in dic_inputs.keys():
            #spacing
            if i=="spacing":
                self.modify_inputs_calibration("igr",0,0,dic_inputs[i])
            #roughness grass
            elif i=="rougheness_grass":
                self.modify_inputs_calibration("igr",0,1,dic_inputs[i])
            #height
            elif i=="height":
                self.modify_inputs_calibration("igr",0,2,dic_inputs[i])
            #roughness bare
            elif i=="roughness_bare":
                self.modify_inputs_calibration("igr",0,3,dic_inputs[i])
            #coarse
            elif i=="coarse_sediment":
                self.modify_inputs_calibration("isd",0,1,dic_inputs[i])
            #incoming
            elif i=="incoming_flow":
                self.modify_inputs_calibration("isd",0,2,dic_inputs[i])
            #porosity
            elif i=="porosity":
                self.modify_inputs_calibration("isd",0,3,dic_inputs[i])
            #sediment_class
            elif i=="particle_class":
                self.modify_inputs_calibration("isd",1,0,dic_inputs[i])
            #sediment_density
            elif i=="particle_densitiy":
                self.modify_inputs_calibration("isd",1,1,dic_inputs[i]) 

        #Update bat for calibration
        self.update_bat_calibration()
        #Execute
        resultado = subprocess.run([self.plugin_directory+"\\executables\\execution.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        #Put warning
        if not "...FINISHED..." in resultado.stdout:
            self.warning_message(str(resultado.stdout))
            return "error"
        
        #Read output
        #First obtain the gso data in (g/cm.s)
        ruta = self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\output\\inverse.og1"
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        sediment = []
        times = []
        for i in range(len(lineas)):
            if lineas[i]=="  Time      Y(t)     X1(t)     X2(t)      L(t)      Se       gsi       gsI       gs2       gso     Cum.gsi Wedge_mass Lower_mass  Cum.gso     f        frac      DEP      CDEP       Tt\n":
                for k in range(i+3,len(lineas)):
                    times.append(float(lineas[k].split()[0]))
                    sediment.append(float(lineas[k].split()[9]))
        self.calibration_df_progress = pd.DataFrame(data = {"Time":times,"Sediment":sediment})
        #Then obtain the width of the filter
        with open(self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\output\\inverse.osp", "r") as archivo:
            lineas = archivo.readlines()
        try:
            for i in lineas:
                if i.split("=")[-1]==" Filter Strip Width (input)\n":
                    for k in i.split("=")[0].split(" "):
                        try:
                            width = float(k)
                            break
                        except:
                            pass
            self.calibration_df_progress["Sediment"] = self.calibration_df_progress["Sediment"]*width*100
        except UnboundLocalError:
            self.warning_message("Error in execution")
            return "error"
                
        
        #Obtain interpolated dataframe
        calibration_df_progress = self.calibration_df_progress.copy()
        calibration_df_progress.set_index('Time', inplace=True)
        sedimentograph_calibration_df = self.sedimentograph_calibration_df.copy()
        sedimentograph_calibration_df.set_index('Time', inplace=True)
        
        #Do the interpolation
        # Crear un nuevo DataFrame para los resultados
        data_aligned = pd.DataFrame(index=calibration_df_progress.index)
        
        
        # Rellenar b_aligned con los valores de b o interpolados
        for idx in calibration_df_progress.index:
            if idx in sedimentograph_calibration_df.index:
                data_aligned.loc[idx, 'Sediment'] = sedimentograph_calibration_df.loc[idx, 'Sediment']
            else:
                lower_index = sedimentograph_calibration_df.index[sedimentograph_calibration_df.index < idx]
                upper_index = sedimentograph_calibration_df.index[sedimentograph_calibration_df.index > idx]
                
                if len(lower_index) > 0 and len(upper_index) > 0:
                    # Hay índices válidos para interpolar
                    lower_idx = lower_index[-1]  # Último índice inferior
                    upper_idx = upper_index[0]    # Primer índice superior
                    
                    # Interpolación lineal
                    lower_value = sedimentograph_calibration_df.loc[lower_idx, 'Sediment']
                    upper_value = sedimentograph_calibration_df.loc[upper_idx, 'Sediment']
                    # Calcular el valor interpolado
                    interpolated_value = lower_value + (upper_value - lower_value) * ((idx - lower_idx) / (upper_idx - lower_idx))
                    data_aligned.loc[idx, 'Sediment'] = interpolated_value
                else:
                    # Si no hay índices cercanos, dejar como NaN
                    data_aligned.loc[idx, 'Sediment'] = float('nan')
        
        
        #Save dataframe for the results
        self.data_aligned = data_aligned
        
        #Calculate objective function
        self.objective_function = [self.dlg_calibration_advanced_settings.objective_function.itemText(i) for i in range(self.dlg_calibration_advanced_settings.objective_function.count())][self.dlg_calibration_advanced_settings.objective_function.currentIndex()]
        if  self.objective_function== "RMSE":
            #Calculate RMSE
            diferencias = calibration_df_progress['Sediment'] - data_aligned['Sediment']
            #Calculate squared differenes
            cuadrados_diferencias = diferencias ** 2
            resultado_total = cuadrados_diferencias.sum()
            return resultado_total
        
        elif self.objective_function == "NSE":
            diferencias = calibration_df_progress['Sediment'] - data_aligned['Sediment']
            cuadrados_diferencias = diferencias ** 2
            suma_cuadrados_diferencias = cuadrados_diferencias.sum()
            media_observados = data_aligned['Sediment'].mean()
            diferencias_media_observados = data_aligned['Sediment'] - media_observados
            cuadrados_diferencias_observados = diferencias_media_observados ** 2
            suma_cuadrados_diferencias_observados = cuadrados_diferencias_observados.sum()
            nash_sutcliffe_efficiency = 1 - (suma_cuadrados_diferencias / suma_cuadrados_diferencias_observados)
            return -nash_sutcliffe_efficiency #the calibration function minimizes values, thats why -

        elif self.objective_function == "NNSE":
            diferencias = calibration_df_progress['Sediment'] - data_aligned['Sediment']
            cuadrados_diferencias = diferencias ** 2
            suma_cuadrados_diferencias = cuadrados_diferencias.sum()
            media_observados = data_aligned['Sediment'].mean()
            diferencias_media_observados = data_aligned['Sediment'] - media_observados
            cuadrados_diferencias_observados = diferencias_media_observados ** 2
            suma_cuadrados_diferencias_observados = cuadrados_diferencias_observados.sum()
            nash_sutcliffe_efficiency = 1 - (suma_cuadrados_diferencias / suma_cuadrados_diferencias_observados)
            nnse = 1/(2-nash_sutcliffe_efficiency)
            return -nnse #the calibration function minimizes values, thats why -
        
        
    def calibration_execution_progress_hydrograph(self,information):
        """Method to show the progress of calibration"""
        #Progress befores we start with the executions
        if information[0]=="Warning":
            #Put the text
            self.calibration_progress_text+=information[1]
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
        elif information[0] == 0:
            #Show dialog
            self.dlg_calibration_progress.show()
            #Put the text
            self.calibration_progress_text = ""
            self.calibration_progress_text+="Starting calibration...\n"
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
            
            if not hasattr(self, 'canvas_calibration_graph'):
                #Create the canvas of the graph
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_calibration_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_calibration_progress.frame)
                self.dlg_calibration_progress.frame.setLayout(layout)
                
                #Add canvas to layout
                layout.addWidget(self.canvas_calibration_graph)
            
            #Add graph
            self.canvas_calibration_graph.figure.clear()
            self.ax_calibration_progress = self.canvas_calibration_graph.figure.subplots()
            
            
            self.ax_calibration_progress.plot(self.hydrograph_calibration_df.Time, self.hydrograph_calibration_df.Discharge,marker='o')
            #Labels
            self.ax_calibration_progress.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
            self.ax_calibration_progress.set_ylabel("Discharge (m3/s)",size = 12,family="arial",weight = "bold",color = "black")
            #X ticks
            self.ax_calibration_progress.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.3, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph.draw()
            
        else:
            #First, put the text
            if self.objective_function == "RMSE":
                self.calibration_progress_text+=f"{information[0]}:OF = "+"{:.2e}".format(information[1])+"\n"
            else: #in NSE and NNSE we put negative in the execution function because its a minimization calibration method
                self.calibration_progress_text+=f"{information[0]}:OF = "+"{:.2e}".format(-information[1])+"\n"
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
            #Then add the graph
            self.canvas_calibration_graph.figure.clear()
            self.ax_calibration_progress = self.canvas_calibration_graph.figure.subplots()
            
            #Add lines
            self.ax_calibration_progress.plot(self.hydrograph_calibration_df.Time,self.hydrograph_calibration_df.Discharge,label = "Measured",marker='o')
            self.ax_calibration_progress.plot(self.calibration_df_progress.Time,self.calibration_df_progress.Discharge,label = "Simulated",marker='o')
            
            #Limits
            #Labels
            self.ax_calibration_progress.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
            self.ax_calibration_progress.set_ylabel("Discharge (m3/s)",size = 12,family="arial",weight = "bold",color = "black")
            #X ticks
            self.ax_calibration_progress.tick_params(axis = "both",colors = "black",labelsize = 9)
            # Add legend
            self.ax_calibration_progress.legend()
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.25, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph.draw()
    
    def calibration_execution_progress_sedimentograph(self,information):
        """Method to show the progress of calibration"""
        #Progress befores we start with the executions
        if information[0]=="Warning":
            #Put the text
            self.calibration_progress_text+=information[1]
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
        elif information[0] == 0:
            #Show dialog
            self.dlg_calibration_progress.show()
            #Put the text
            self.calibration_progress_text = ""
            self.calibration_progress_text+="Starting calibration...\n"
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
            
            if not hasattr(self, 'canvas_calibration_graph'):
                #Create the canvas of the graph
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_calibration_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_calibration_progress.frame)
                self.dlg_calibration_progress.frame.setLayout(layout)
                
                #Add canvas to layout
                layout.addWidget(self.canvas_calibration_graph)
            
            #Add graph
            self.canvas_calibration_graph.figure.clear()
            self.ax_calibration_progress = self.canvas_calibration_graph.figure.subplots()
            
            
            self.ax_calibration_progress.plot(self.sedimentograph_calibration_df.Time, self.sedimentograph_calibration_df.Sediment,marker='o')
            #Labels
            self.ax_calibration_progress.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
            self.ax_calibration_progress.set_ylabel("Sediment (g/s)",size = 12,family="arial",weight = "bold",color = "black")
            #X ticks
            self.ax_calibration_progress.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.3, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph.draw()
            
        else:
            #First, put the text
            if self.objective_function == "RMSE":
                self.calibration_progress_text+=f"{information[0]}:OF = "+"{:.2e}".format(information[1])+"\n"
            else: #in NSE and NNSE we put negative in the execution function because its a minimization calibration method
                self.calibration_progress_text+=f"{information[0]}:OF = "+"{:.2e}".format(-information[1])+"\n"
            self.dlg_calibration_progress.textEdit.setPlainText(self.calibration_progress_text)
            self.dlg_calibration_progress.textEdit.moveCursor(QtGui.QTextCursor.End) #move to end the text to see it
            
            #Then add the graph
            self.canvas_calibration_graph.figure.clear()
            self.ax_calibration_progress = self.canvas_calibration_graph.figure.subplots()
            
            #Add lines
            self.ax_calibration_progress.plot(self.sedimentograph_calibration_df.Time,self.sedimentograph_calibration_df.Sediment,label = "Measured",marker='o')
            self.ax_calibration_progress.plot(self.calibration_df_progress.Time,self.calibration_df_progress.Sediment,label = "Simulated",marker='o')
            
            #Limits
            #Labels
            self.ax_calibration_progress.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
            self.ax_calibration_progress.set_ylabel("Sediment (g/s)",size = 12,family="arial",weight = "bold",color = "black")
            #X ticks
            self.ax_calibration_progress.tick_params(axis = "both",colors = "black",labelsize = 9)
            # Add legend
            self.ax_calibration_progress.legend()
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.25, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph.draw()
    
    
    
    def save_results_calibration(self,inputs, results):
        """Method to save results in calibration execution"""
        #Calculate goodness of fit values
        #Ceff (Nash Sutcliffe)
        calibration_df_progress = self.calibration_df_progress.copy()
        calibration_df_progress.set_index('Time', inplace=True)
        diferencias = calibration_df_progress.iloc[:,0] - self.data_aligned.iloc[:,0]
        cuadrados_diferencias = diferencias ** 2
        suma_cuadrados_diferencias = cuadrados_diferencias.sum()
        media_observados = self.data_aligned.iloc[:,0].mean()
        diferencias_media_observados = self.data_aligned.iloc[:,0] - media_observados
        cuadrados_diferencias_observados = diferencias_media_observados ** 2
        suma_cuadrados_diferencias_observados = cuadrados_diferencias_observados.sum()
        nash_sutcliffe_efficiency = 1 - (suma_cuadrados_diferencias / suma_cuadrados_diferencias_observados)
        #RMSE
        diferencias = calibration_df_progress.iloc[:,0] - self.data_aligned.iloc[:,0]
        cuadrados_diferencias = diferencias ** 2
        rmse = cuadrados_diferencias.sum()
        #IOA
        observed = self.data_aligned.iloc[:,0]
        simulated = calibration_df_progress.iloc[:,0]
        mean_observed = observed.mean()
        squared_differences = (simulated - observed) ** 2
        numerator = squared_differences.sum()
        denominator = ((abs(simulated - mean_observed) + abs(observed - mean_observed)) ** 2).sum()
        ioa = 1 - (numerator / denominator)
        #IOA_m
        observed = self.data_aligned.iloc[:,0]
        simulated = calibration_df_progress.iloc[:,0]
        mean_observed = observed.mean()
        squared_differences = (simulated - observed) ** 2
        numerator = squared_differences.sum()
        denominator = ((abs(simulated - mean_observed) + abs(observed - mean_observed)) ** 2).sum()
        ioa_m = 1 - (numerator / denominator)
        #IOA_r
        numerator_r = ((simulated - observed) ** 2).sum()
        denominator_r = (observed ** 2).sum()
        ioa_r = 1 - (numerator_r / denominator_r)
        #MAE
        mae = (abs(simulated - observed)).mean()
        #Ceff_m 
        mean_observed = observed.mean()
        Ceff_m = 1 - (cuadrados_diferencias.sum() / ((observed - mean_observed) ** 2).sum())
        #Ceff_r
        Ceff_r = 1 - (cuadrados_diferencias.sum() / (calibration_df_progress.iloc[:,0] ** 2).sum())
        
        #Create csv with results
        path = self.obtain_direction_vfsmod(self.dlg_calibration_advanced_settings.exit_file.text())
        try:
            with open(path, 'w') as f:
                #Add results of calibration
                if self.calibration_sedimentograph:
                    f.write(f"Sedimentograph calibration" + '\n')
                elif self.calibration_hydrograph:
                    f.write(f"Hydrograph calibration" + '\n')
                f.write(f"Number of iterations: {len(inputs)}" + '\n')
                if self.objective_function == "RMSE":
                    final_of = min(results)
                else:
                    final_of = max(results)
                f.write(f"Final OF: {final_of}" + '\n')
                f.write(f"Estimated parameter values: ")
                for i in range(len(self.calibration_dictionary.keys())):
                    if i != len(self.calibration_dictionary.keys())-1:
                        f.write(f"{list(self.calibration_dictionary.keys())[i]}: {inputs[results.index(final_of)][i]},")
                    else:
                        f.write(f"{list(self.calibration_dictionary.keys())[i]}: {inputs[results.index(final_of)][i]}\n")
                f.write(f"--------Goodness of fit--------\n")
                f.write(f"Ceff = {nash_sutcliffe_efficiency}"+"\n")
                f.write(f"Ceff_m = {Ceff_m}"+"\n")
                f.write(f"Ceff_r = {Ceff_r}"+"\n")
                f.write(f"RMSE = {rmse}"+"\n")
                f.write(f"IoA = {ioa}"+"\n")
                f.write(f"IoA_m = {ioa_m}"+"\n")
                f.write(f"IoA_r = {ioa_r}"+"\n")
                f.write(f"MAE = {mae}"+"\n")
        except PermissionError:
            self.warning_message(f"{path} file is opened. Please close it to save results")
        
        #Then add the observed and simulated data
        df = pd.DataFrame(data = {"Time":self.data_aligned.index,"Observed":self.data_aligned.iloc[:,0],"Simulated":calibration_df_progress.iloc[:,0]})
        df.to_csv(path, mode='a',index=False, float_format='%.5f')
        
        #Put filepath in the results dialog
        if self.calibration_sedimentograph:
            self.dlg_calibration_results_sedimentograph.results.setText(self.dlg_calibration_advanced_settings.exit_file.text())
        elif elf.calibration_hydrograph:
            self.dlg_calibration_results_hydrograph.results.setText(self.dlg_calibration_advanced_settings.exit_file.text())
        
        #Set to false calibrations
        self.calibration_sedimentograph = False
        self.calibration_hydrograph = False
    
    
    def update_graph_calibration_hydrograph(self):
        """Method to update the graph of calibration"""
        path = self.obtain_direction_vfsmod(self.dlg_calibration_results_hydrograph.results.text())
        if os.path.exists(path):    
            #First add the text
            with open(path, "r") as archivo:
                lineas = archivo.readlines()
            contenido = ""
            times = []
            observed = []
            simulated = []
            for k,i in enumerate(lineas):
                if i[:4]=="Time":
                    for m in range(k+1,len(lineas)):
                        try:
                            times.append(float(lineas[m].split(",")[0]))
                        except:
                            times.append(0)
                        try:
                            observed.append(float(lineas[m].split(",")[1]))
                        except:
                            observed.append(0)
                        try:
                            simulated.append(float(lineas[m].split(",")[2]))
                        except:
                            simulated.append(0)
                    break
                contenido += i
            self.dlg_calibration_results_hydrograph.textEdit.setPlainText(contenido)
            
            #Add the graph
            if not hasattr(self, 'canvas_calibration_graph_hydrograph'):
                #Create the canvas of the graph
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_calibration_graph_hydrograph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_calibration_results_hydrograph.frame)
                self.dlg_calibration_results_hydrograph.frame.setLayout(layout)
                #Add canvas to layout
                layout.addWidget(self.canvas_calibration_graph_hydrograph)
            
            #Add graph
            self.canvas_calibration_graph_hydrograph.figure.clear()
            self.ax_calibration_graph_hydrograph = self.canvas_calibration_graph_hydrograph.figure.subplots()
            
            if self.dlg_calibration_results_hydrograph.one_one.isChecked():
                self.ax_calibration_graph_hydrograph.scatter(simulated, observed,color = "blue")
                #1:1 line
                max_val = max(simulated + observed)
                self.ax_calibration_graph_hydrograph.plot([0, max_val], [0, max_val], linestyle='--', color='black')
                self.ax_calibration_graph_hydrograph.set_xlabel("Simulated",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_hydrograph.set_ylabel("Observed",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_hydrograph.tick_params(axis = "both",colors = "black",labelsize = 9)

                
            elif self.dlg_calibration_results_hydrograph.graph_fit.isChecked():
                self.ax_calibration_graph_hydrograph.plot(times, observed,
                    color = "blue", label = "Observed",marker = "o")
                self.ax_calibration_graph_hydrograph.plot(times, simulated,color = "red", 
                    label = "Simulated",marker = "o")
                self.ax_calibration_graph_hydrograph.legend()
                self.ax_calibration_graph_hydrograph.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_hydrograph.set_ylabel("Discharge (m3/s)",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_hydrograph.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph_hydrograph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph_hydrograph.figure.subplots_adjust(left=0.2, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph_hydrograph.draw()
    
    def update_graph_calibration_sedimentograph(self):
        """Method to update the graph of calibration"""
        path = self.obtain_direction_vfsmod(self.dlg_calibration_results_sedimentograph.results.text())
        if os.path.exists(path):    
            #First add the text
            with open(path, "r") as archivo:
                lineas = archivo.readlines()
            contenido = ""
            times = []
            observed = []
            simulated = []
            for k,i in enumerate(lineas):
                if i[:4]=="Time":
                    for m in range(k+1,len(lineas)):
                        try:
                            times.append(float(lineas[m].split(",")[0]))
                        except:
                            times.append(0)
                        try:
                            observed.append(float(lineas[m].split(",")[1]))
                        except:
                            observed.append(0)
                        try:
                            simulated.append(float(lineas[m].split(",")[2]))
                        except:
                            simulated.append(0)
                    break
                contenido += i
            self.dlg_calibration_results_sedimentograph.textEdit.setPlainText(contenido)
            
            #Add the graph
            if not hasattr(self, 'canvas_calibration_graph_sedimentograph'):
                #Create the canvas of the graph
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_calibration_graph_sedimentograph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_calibration_results_sedimentograph.frame)
                self.dlg_calibration_results_sedimentograph.frame.setLayout(layout)
                #Add canvas to layout
                layout.addWidget(self.canvas_calibration_graph_sedimentograph)
            
            #Add graph
            self.canvas_calibration_graph_sedimentograph.figure.clear()
            self.ax_calibration_graph_sedimentograph = self.canvas_calibration_graph_sedimentograph.figure.subplots()
            
            if self.dlg_calibration_results_sedimentograph.one_one.isChecked():
                self.ax_calibration_graph_sedimentograph.scatter(simulated, observed,color = "blue")
                #1:1 line
                max_val = max(simulated + observed)
                self.ax_calibration_graph_sedimentograph.plot([0, max_val], [0, max_val], linestyle='--', color='black')
                self.ax_calibration_graph_sedimentograph.set_xlabel("Simulated",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_sedimentograph.set_ylabel("Observed",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_sedimentograph.tick_params(axis = "both",colors = "black",labelsize = 9)

                
            elif self.dlg_calibration_results_sedimentograph.graph_fit.isChecked():
                self.ax_calibration_graph_sedimentograph.plot(times, observed,
                    color = "blue", label = "Observed",marker = "o")
                self.ax_calibration_graph_sedimentograph.plot(times, simulated,color = "red", 
                    label = "Simulated",marker = "o")
                self.ax_calibration_graph_sedimentograph.legend()
                self.ax_calibration_graph_sedimentograph.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_sedimentograph.set_ylabel("Sediment (g/s)",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph_sedimentograph.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph_sedimentograph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph_sedimentograph.figure.subplots_adjust(left=0.2, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph_sedimentograph.draw()
            
            
            
    def update_bat_calibration(self):
        """Method to update the bat of the hydrograph"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\inverse\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" inverse.prj'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    def move_files_calibration_hydrograph(self):
        """Method to move files to the corresponding folders for calibration"""
        #Move hydrograph
        try:
            shutil.copyfile(self.obtain_direction_vfsmod(self.dlg_base.hydrograph_file.text()),self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\{os.path.basename(self.dlg_base.hydrograph_file.text())}")
        except SameFileError:
            pass
            
        #Prj
        prj_file = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inverse.prj"
        #Check if water quality is simulated
        with open(self.obtain_direction_vfsmod(self.dlg_base.vfs_project.text()), "r") as archivo:
            lineas = archivo.readlines()
        self.water_quality = False
        for i in lineas:
            if i[:3]=="iwq":
                self.water_quality = True
            
        #Create file
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw=inputs\\inverse.ikw  \n")
            archivo.write(f"iso=inputs\\inverse.iso  \n")
            archivo.write(f"igr=inputs\\inverse.igr  \n")
            archivo.write(f"isd=inputs\\inverse.isd  \n")
            archivo.write(f"irn=inputs\\inverse.irn  \n")
            archivo.write(f"iro=inputs\\inverse.iro  \n")
            if self.water_quality:
                archivo.write(f"iwq=inputs\\inverse.iwq  \n")
            archivo.write(f"og1=output\\inverse.og1  \n")
            archivo.write(f"og2=output\\inverse.og2  \n")
            archivo.write(f"ohy=output\\inverse.ohy  \n")
            archivo.write(f"osm=output\\inverse.osm  \n")
            archivo.write(f"osp=output\\inverse.osp  \n")
            if self.water_quality:
                archivo.write(f"owq=output\\inverse.owq  \n")
        
        #UH
        lis_file = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inverse.lis"
        #Create file
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp=inputs\\inverse.inp  \n")
            archivo.write(f"iro=inputs\\inverse.iro  \n")
            archivo.write(f"irn=inputs\\inverse.irn  \n")
            archivo.write(f"isd=inputs\\inverse.isd  \n")
            archivo.write(f"out=inputs\\inverse.out  \n")
            archivo.write(f"hyt=inputs\\inverse.hyt  \n")
        
        #REST OF THE FILES
        #Function to copy and paste the inputs to create the files to use in the design analysis
        def copy_paste(type_input):
            ruta_pegar = self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\inputs\\inverse.{type_input}" 
            ruta = self.obtain_direction_vfsmod(self.dlg_base.vfs_project.text())
            if os.path.exists(ruta) and os.path.isfile(ruta):
                #First we open .prj and obtain the direction of the copying file
                with open(ruta, "r") as archivo:
                    lineas = archivo.readlines()
                for i in lineas:
                    if i[:3]==type_input:
                        ikw = i.split("=")[-1]
                if not os.path.isabs(ikw): #relative path
                    ikw = os.path.join(os.path.dirname(ruta), ikw)
                ikw = ikw.replace("\n", "") #take out the line jumps
                shutil.copyfile(ikw, ruta_pegar)
        
        #IKW
        copy_paste("ikw")
        #ISO
        copy_paste("iso")
        #IGR
        copy_paste("igr")
        #ISD
        copy_paste("isd")
        #IRN
        copy_paste("irn")
        #IRO
        copy_paste("iro")
        #IWQ
        if self.water_quality:
            copy_paste("iwq")
        
        
    def create_dictionary_calibration_hydrograph(self):
        """Method to create the dictionary of bounds of the input parameters for the calibration of hydrograph"""
        #Inputs
        dictionary = {}
        #Function to return the value needed for the inverse calibration file
        def calibration(radio_button_one,radio_button_two):
            if radio_button_one.isChecked():
                return "change"
            elif radio_button_two.isChecked():
                return "calibrate"
            else:
                return -1
        
        
        vertical = calibration(self.dlg_base.change_vertical,self.dlg_base.calibrate_vertical)
        average = calibration(self.dlg_base.change_average,self.dlg_base.calibrate_average)
        saturated = calibration(self.dlg_base.change_saturated,self.dlg_base.calibrate_saturated)
        initial = calibration(self.dlg_base.change_initial,self.dlg_base.calibrate_initial)
        maximum = calibration(self.dlg_base.change_maximum,self.dlg_base.calibrate_maximum)
        fraction = calibration(self.dlg_base.change_fraction,self.dlg_base.calibrate_fraction)
        width = calibration(self.dlg_base.change_width,self.dlg_base.calibrate_width)
        length = calibration(self.dlg_base.change_length,self.dlg_base.calibrate_length)
        manning = calibration(self.dlg_base.change_manning,self.dlg_base.calibrate_manning)
        slope = calibration(self.dlg_base.change_slope,self.dlg_base.calibrate_slope)
        
        #Change inputs if "Change" has selected
        self.change_base_inputs_calibration_hydrograph([vertical,average,saturated,initial,maximum,fraction,width,length,manning,slope])
        
        #Create dictionary
        if vertical == "calibrate":
            dictionary["vertical"] = [float(self.dlg_base.min_vertical.text()),float(self.dlg_base.max_vertical.text())]
            
        if average == "calibrate":
            dictionary["average"] = [float(self.dlg_base.min_average.text()),float(self.dlg_base.max_average.text())]
        
        if saturated == "calibrate":
            dictionary["saturated"] = [float(self.dlg_base.min_saturated.text()),float(self.dlg_base.max_saturated.text())]
        
        if initial == "calibrate":
            dictionary["initial"] = [float(self.dlg_base.min_initial.text()),float(self.dlg_base.max_initial.text())]
        
        if maximum == "calibrate":
            dictionary["maximum"] = [float(self.dlg_base.min_maximum.text()),float(self.dlg_base.max_maximum.text())]
        
        if fraction == "calibrate":
            dictionary["fraction"] = [float(self.dlg_base.min_fraction.text()),float(self.dlg_base.max_fraction.text())]
        
        if width == "calibrate":
            dictionary["width"] = [float(self.dlg_base.min_width.text()),float(self.dlg_base.max_width.text())]
        
        if length == "calibrate":
            dictionary["length"] = [float(self.dlg_base.min_length.text()),float(self.dlg_base.max_length.text())]
        
        if manning == "calibrate":
            dictionary["manning"] = [float(self.dlg_base.min_manning.text()),float(self.dlg_base.max_manning.text())]
        
        if slope == "calibrate":
            dictionary["slope"] = [float(self.dlg_base.min_slope.text()),float(self.dlg_base.max_slope.text())]
        
        return dictionary
    
    def create_dictionary_calibration_sedimentograph(self):
        """Method to create the dictionary of bounds of the input parameters for the calibration of sedimentograph"""
        #Inputs
        dictionary = {}
        #Function to return the value needed for the inverse calibration file
        def calibration(radio_button_one,radio_button_two):
            if radio_button_one.isChecked():
                return "change"
            elif radio_button_two.isChecked():
                return "calibrate"
            else:
                return -1
        
        
        spacing = calibration(self.dlg_base.change_spacing,self.dlg_base.calibrate_spacing)
        rougheness_grass = calibration(self.dlg_base.change_roughness,self.dlg_base.calibrate_roughness)
        height = calibration(self.dlg_base.change_height,self.dlg_base.calibrate_height)
        roughness_bare = calibration(self.dlg_base.change_bare,self.dlg_base.calibrate_bare)
        coarse_sediment = calibration(self.dlg_base.change_coarse,self.dlg_base.calibrate_coarse)
        incoming_flow = calibration(self.dlg_base.change_incoming,self.dlg_base.calibrate_incoming)
        porosity = calibration(self.dlg_base.change_porosity,self.dlg_base.calibrate_porosity)
        particle_class = calibration(self.dlg_base.change_class,self.dlg_base.calibrate_class)
        particle_densitiy = calibration(self.dlg_base.change_density,self.dlg_base.calibrate_density)
        

        #Change inputs if "Change" has selected
        self.change_base_inputs_calibration_sedimentograph([spacing,rougheness_grass,height,roughness_bare,coarse_sediment,incoming_flow,porosity,particle_class,particle_densitiy])
        
        #Create dictionary
        if spacing == "calibrate":
            dictionary["spacing"] = [float(self.dlg_base.min_spacing.text()),float(self.dlg_base.max_spacing.text())]
            
        if rougheness_grass == "calibrate":
            dictionary["rougheness_grass"] = [float(self.dlg_base.min_roughness.text()),float(self.dlg_base.max_roughness.text())]
        
        if height == "calibrate":
            dictionary["height"] = [float(self.dlg_base.min_height.text()),float(self.dlg_base.max_height.text())]
        
        if roughness_bare == "calibrate":
            dictionary["roughness_bare"] = [float(self.dlg_base.min_bare.text()),float(self.dlg_base.max_bare.text())]
        
        if coarse_sediment == "calibrate":
            dictionary["coarse_sediment"] = [float(self.dlg_base.min_coarse.text()),float(self.dlg_base.max_coarse.text())]
        
        if incoming_flow == "calibrate":
            dictionary["incoming_flow"] = [float(self.dlg_base.min_incoming.text()),float(self.dlg_base.max_incoming.text())]
        
        if porosity == "calibrate":
            dictionary["porosity"] = [float(self.dlg_base.min_porosity.text()),float(self.dlg_base.max_porosity.text())]
        
        if particle_class == "calibrate":
            dictionary["particle_class"] = [float(self.dlg_base.min_class.text()),float(self.dlg_base.max_class.text())]
        
        if particle_densitiy == "calibrate":
            dictionary["particle_densitiy"] = [float(self.dlg_base.min_density.text()),float(self.dlg_base.max_density.text())]
        
        return dictionary
        
    
    def modify_inputs_calibration(self,extension, row, column, new_value):
        """Method to modify inputs in calibration"""
        filepath = self.dlg_base.working_directory_vfsmod.text()+f"\\inverse\\inputs\\inverse.{extension}"
        with open(filepath, 'r') as file:
            lineas = file.readlines()
        numbers_str = lineas[row]
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        matches[column] = str(new_value)
        # Rebuild the string by replacing only the specific number
        lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        with open(filepath, 'w') as archivo:
            for i in lineas:
                archivo.write(i)
    
    def change_base_inputs_calibration_hydrograph(self,inputs):
        """Method to change the inputs in the calibration of hydrograph if change is selected"""
        #vertical
        if inputs[0]=="change":
            self.modify_inputs_calibration("iso",0,0,self.dlg_base.new_vertical.text())
        #average
        if inputs[1]=="change":
            self.modify_inputs_calibration("iso",0,1,self.dlg_base.new_average.text())
        #saturated
        if inputs[2]=="change":
            self.modify_inputs_calibration("iso",0,2,self.dlg_base.new_saturated.text())
        #initial
        if inputs[3]=="change":
            self.modify_inputs_calibration("iso",0,3,self.dlg_base.new_initial.text())
        #maximum
        if inputs[4]=="change":
            self.modify_inputs_calibration("iso",0,4,self.dlg_base.new_maximum.text())
        #fraction
        if inputs[5]=="change":
            self.modify_inputs_calibration("iso",0,5,self.dlg_base.new_fraction.text())
        #width
        if inputs[6]=="change":
            self.modify_inputs_calibration("ikw",1,0,self.dlg_base.new_width.text())
        #length
        if inputs[7]=="change":
            self.modify_ikw_file_calibration(self.dlg_base.new_length.text())
        #manning
        if inputs[8]=="change":
            self.modify_mannign_slope_hydrograph_calibration(1,self.dlg_base.new_manning.text())
        #slope
        if inputs[9]=="change":
            self.modify_mannign_slope_hydrograph_calibration(2,self.dlg_base.new_slope.text())
        
    
    def modify_mannign_slope_hydrograph_calibration(self,column,new_value):
        """Method to modify the manning and slope for hydrograph calibration"""
        #We obtain information of ikw file
        ikw = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inputs\\inverse.ikw"
        
        with open(ikw, "r") as archivo:
            lineas = archivo.readlines()
        
        for row in range(4,len(lineas)):
            numbers_str = lineas[row]
            # Use regex to find all numbers in the string
            matches = re.findall(r'\S+', numbers_str)
            # Replace the specific number at the given index
            if len(matches)==1:
                break
            matches[column] = str(new_value)
            # Rebuild the string by replacing only the specific number
            lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
            
            with open(ikw, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
            
    def modify_ikw_file_calibration(self,value_change):
        """Metod to modify the ikw file for the hydrograph calibration"""
        #We obtain information of ikw file
        ikw = self.dlg_base.working_directory_vfsmod.text()+"\\inverse\\inputs\\inverse.ikw"
        #We substitute value of length
        with open(ikw, "r") as archivo:
            lineas = archivo.readlines()

        def modify_number_in_string(numbers_str, index, new_value):
            # Use regex to find all numbers in the string
            matches = re.findall(r'\S+', numbers_str)
            # Replace the specific number at the given index
            matches[index] = str(new_value)
            # Rebuild the string by replacing only the specific number
            return re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        lineas[2] = modify_number_in_string(lineas[2],0,value_change)
        
        #Then we update the segments
        number_segments = int(lineas[3])
        length = list(map(float, lineas[2].split()))[0]
        new_interval = length/number_segments
        
        #Data frame, but we take it from the original, not from the last execution
        #We import dataframe of segments from the original file
        ruta = self.obtain_direction_vfsmod(self.dlg_base.vfs_project.text())
        with open(ruta, "r") as archivo:
            lineas_prj = archivo.readlines()
        ikw_original = lineas_prj[0].split("=")[-1]
        if not os.path.isabs(ikw_original): #relative path
            ikw_original = os.path.join(os.path.dirname(ruta), ikw_original)
        ikw_original = ikw_original.replace("\n", "")
        with open(ikw_original, "r") as archivo:
            lineas_ikw_original = archivo.readlines()
        
        #Data frame    
        df = pd.DataFrame(data = {"Distance":[list(map(float, lineas_ikw_original[x].split()))[0] for x in range(4,4+number_segments)],
                             "Manning":[list(map(float, lineas_ikw_original[x].split()))[1] for x in range(4,4+number_segments)],
                             "Slope":[list(map(float, lineas_ikw_original[x].split()))[2] for x in range(4,4+number_segments)]})
        
        
        actual_length = max(df["Distance"])
        length_to_change = float(value_change)
        print(length_to_change)
        if length_to_change <= actual_length:
            df = df[df["Distance"]<=length_to_change]
            df.loc[df.index[-1], "Distance"] = length_to_change
        else:
            df.loc[df.index[-1], "Distance"] = length_to_change
        
        
        #Add to the file information 
        lineas[3] = modify_number_in_string(lineas[3],0,len(df)) #change number of segments
    
        #Add to the file information
        contenido = ""
        for i in lineas[:4]:    
            contenido+=f"{i}"
        for i in range(len(df)):
            contenido +=f" {df.iloc[i,0]}   {df.iloc[i,1]}   {df.iloc[i,2]}\n"
        for i in lineas[-8:]:    
            contenido+=f"{i}"
        with open(ikw, 'w') as archivo:
            archivo.write(contenido)
    
    def create_folder_calibration(self):
        """Method to create the folder needed to calibration"""
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.dlg_base.working_directory_vfsmod.text()
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
            
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\inverse"):
            create_folder("inverse")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\inverse\inputs"):
            create_folder("inverse\inputs")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\inverse\output"):
            create_folder("inverse\output")
    
    def draw_calibration_hydrology(self):
        """Method to draw the dialog in calibration of hydrology"""
        for i in self.hydrology_checks:
            if i[0][0].isChecked():#no is selected
                i[1][0].setStyleSheet("background-color: #d9d9d9;")
                i[1][0].setEnabled(False)
                i[1][1].setStyleSheet("background-color: #d9d9d9;")
                i[1][1].setEnabled(False)
                i[1][2].setStyleSheet("background-color: #d9d9d9;")
                i[1][2].setEnabled(False)
                
            elif i[0][1].isChecked():#change is selected
                i[1][0].setStyleSheet("background-color: #f0f0f0;")
                i[1][0].setEnabled(True)
                i[1][1].setStyleSheet("background-color: #d9d9d9;")
                i[1][1].setEnabled(False)
                i[1][2].setStyleSheet("background-color: #d9d9d9;")
                i[1][2].setEnabled(False)
                
            elif i[0][2].isChecked():#calibrate is selected
                i[1][0].setStyleSheet("background-color: #d9d9d9;")
                i[1][0].setEnabled(False)
                i[1][1].setStyleSheet("background-color: #f0f0f0;")
                i[1][1].setEnabled(True)
                i[1][2].setStyleSheet("background-color: #f0f0f0;")
                i[1][2].setEnabled(True)
            
    def draw_calibration_sedimentograph(self):
        """Method to draw the dialog in calibration of sedimentograph"""
        for i in self.sedimentograph_checks:
            if i[0][0].isChecked():#no is selected
                i[1][0].setStyleSheet("background-color: #d9d9d9;")
                i[1][0].setEnabled(False)
                i[1][1].setStyleSheet("background-color: #d9d9d9;")
                i[1][1].setEnabled(False)
                i[1][2].setStyleSheet("background-color: #d9d9d9;")
                i[1][2].setEnabled(False)
                
            elif i[0][1].isChecked():#change is selected
                i[1][0].setStyleSheet("background-color: #f0f0f0;")
                i[1][0].setEnabled(True)
                i[1][1].setStyleSheet("background-color: #d9d9d9;")
                i[1][1].setEnabled(False)
                i[1][2].setStyleSheet("background-color: #d9d9d9;")
                i[1][2].setEnabled(False)
                
            elif i[0][2].isChecked():#calibrate is selected
                i[1][0].setStyleSheet("background-color: #d9d9d9;")
                i[1][0].setEnabled(False)
                i[1][1].setStyleSheet("background-color: #f0f0f0;")
                i[1][1].setEnabled(True)
                i[1][2].setStyleSheet("background-color: #f0f0f0;")
                i[1][2].setEnabled(True)
                
    def uncheck_length_spacing(self,parameter):
        """Method to check-uncheck the vegetation length or spacing because only one can be selected"""
        if parameter == "length" and self.dlg_base.design_length.isChecked(): 
            self.dlg_base.design_spacing.setChecked(False)
        elif parameter == "spacing" and self.dlg_base.design_spacing.isChecked(): 
            self.dlg_base.design_length.setChecked(False)
        
    def run_vfsmod(self):
        """Method to run VFSMOD"""
        #Variable to end execution
        self.end_execution = False
        
        #Error handling
        self.error_handling_vfsmod()
        
        if self.end_execution:
            return
        
        #Folder creation
        self.folder_creation_vfsmod()
        
        #First we create the .prj file
        self.create_prj_file()
        
        #The hietograph file with this version of the executable creates .irn file with one more rain steps and it gets error
        self.correct_irn_file(self.obtain_direction_vfsmod(self.dlg_base.line_storm.text()))
        
        #We update the bat for the execution fo VFSMOD
        self.update_bat_vfsmod()
        
        #Execute bat
        resultado = subprocess.run([self.plugin_directory+"\\executables\\execution.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        
        #Put warning
        if not "...FINISHED..." in resultado.stdout:
            self.warning_message(str(resultado.stdout))
        else:
            self.warning_message("VFS executed succesfully!")
        
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
        
        #Update value in design
        self.add_vfs_length_spacing()
    
    def correct_irn_file(self,path):
        """Method to correct the .irn file (the number of steps)"""
        #Open file
        with open(path, "r") as archivo:
            lineas = archivo.readlines()
        #Calculate the number of steps in hietograph
        number_steps = 0
        for i in lineas:
            try:
                float(i.strip().split(" ")[0]) #first number of the line
                number_steps += 1
            except:
                pass
        number_steps -=1
        #Add to the text
        splits = lineas[0].split(" ")
        for k,i in enumerate(splits):
            try:
                float(i)
                splits[k] = str(number_steps)
                break
            except:
                pass
        lineas[0] = " ".join(splits)
        #Save the file
        contenido = ""
        for i in lineas:    
            contenido+=f"{i}"
        with open(path, 'w') as archivo:
            archivo.write(contenido)
    
    def warning_message_calibration(self,message):
        """Message for the calibration"""
        #Put text
        self.dlg_warning_message_calibration.warning.setText(message)
        #Put to the front
        self.dlg_warning_message_calibration.raise_()
        self.dlg_warning_message_calibration.activateWindow()
        #Show the dialog
        self.dlg_warning_message_calibration.show()
    
                
    
    def run_design_part_one(self):
        """Method to run the design"""
        #Variable to end the execution in the design
        self.error_design = False
        #We first create all the combinations
        self.combinations_design = self.create_combinations_design()
        
        #Error handling
        if self.error_design:
            return
        
        #We create the required files
        #First we create the folders in case they don't exist
        self.create_folder_for_design()
        
        #Move files to design folder
        self.move_files_design_analysis()
        
        
        #We add the information of the loops to the files and we execute the file
        self.df_results_design = pd.DataFrame(columns=["Total Runoff from source (mm)","Total Runoff from Source (m3)",
            "Total Runoff out from Filter (mm)","Total Runoff out from Filter (m3)","Total Infiltration in Filter",
            "Mass Sediment Input to Filter","Concentration Sediment in Runoff from source Area",
            "Mass Sediment Output from Filter","Concentration Sediment in Runoff exiting the Filter",
            "Sediment Delivery Ratio","Runoff Delivery Ratio"])
        
        #Method were the paralelization is achieved
        self.start_analysis_design()
    
    def run_design_part_two(self):
         """Second part of design analysis to analyze the results. I have splitted sensitivity running in two because we use Thread method and we need to stop till the thread finishes, if not we get an error"""
        
         #Create DataFrame or results
         self.df_results_design = self.create_df_design(self.results)

         #Delete all files created for paralelization of design analysis
         self.delete_files_design()

         #Add results to a csv
         try:
             self.df_results_design.to_csv(self.obtain_direction_vfsmod(self.dlg_base.name_design_csv.text()), index=False, float_format='%.5f')
         except PermissionError:
            self.warning_message(f"{self.obtain_direction_vfsmod(self.dlg_base.name_design_csv.text())} file is opened and Design Analysis data could not be saved")
            return
         #Close progress bar
         self.progress_metod(close = True)
    
         #Add csv vile to the lineedit to finally put the results in the table
         self.dlg_design_results.design_file.setText(self.dlg_base.name_design_csv.text())
    
         #Update resutls
         self.update_design_results()
    
         #Warning message
         self.warning_message("Design completed succesfully!")
    
    def update_design_results(self):
        """Method to show the diaog and add outputs to table after the design execution"""
        #Add results to table
        #Obtain data
        path = self.obtain_direction_vfsmod(self.dlg_design_results.design_file.text())
        if os.path.exists(path):
            df = pd.read_csv(path)
            self.dlg_design_results.tableWidget.setRowCount(len(df))
            self.dlg_design_results.tableWidget.setColumnCount(len(df.columns))
            self.dlg_design_results.tableWidget.setHorizontalHeaderLabels(df.columns)
            for fila in range(len(df)):
                for columna in range(len(df.columns)):
                    item = QTableWidgetItem(str(df.iloc[fila,columna]))
                    self.dlg_design_results.tableWidget.setItem(fila, columna, item)
                    item.setTextAlignment(Qt.AlignCenter)
    
            
            
    def update_bat_uh_design(self):
        """Method to update bat for the execution of UH"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{self.dlg_base.working_directory_vfsmod.text()}\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\uh" design.lis'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
        
        
    def create_folder_for_design(self):
        """Method to create folders for the design if they don't exist"""
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.dlg_base.working_directory_vfsmod.text()
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
            
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\design"):
            create_folder("design")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\design\inputs"):
            create_folder("design\inputs")
        if not os.path.exists(os.path.normpath(self.dlg_base.working_directory_vfsmod.text())+"\design\output"):
            create_folder("design\output")
        
    def create_combinations_design(self):
        """Method to create the combinations for the design"""
        #STORM
        if self.dlg_base.specific.isChecked():
            return_period_lines = [self.dlg_base.lineEdit_4.text(),self.dlg_base.lineEdit_5.text(),self.dlg_base.lineEdit_6.text(),
                self.dlg_base.lineEdit_7.text(),self.dlg_base.lineEdit_8.text(),self.dlg_base.lineEdit_9.text(),self.dlg_base.lineEdit_10.text()]
            rainfall = []
            for i in return_period_lines:
                if i!="0":
                    rainfall.append(i)
                else:
                    break
        else:
            start = float(self.dlg_base.start.text())
            end = float(self.dlg_base.end.text())
            increment = float(self.dlg_base.increment.text())
            rainfall = [start]
            while True:
                if rainfall[-1]+increment>end:
                    break
                else:
                    rainfall.append(rainfall[-1]+increment)
            if len(rainfall)>7:
                self.warning_message(f"Check input data\nMaximum number of return periods is 7 and {len(rainfall)} is added")
                self.error_design = True
                return
        #LENGTH
        if self.dlg_base.design_length.isChecked():
            start = float(self.dlg_base.lower_length.text())
            end = float(self.dlg_base.upper_length.text())
            increment = float(self.dlg_base.increment_length.text())
            length = [start]
            while True:
                if length[-1]+increment>end:
                    break
                else:
                    length.append(length[-1]+increment)
        else:
            length = [""]
        
        #SPACING
        if self.dlg_base.design_spacing.isChecked():
            start = float(self.dlg_base.lower_spacing.text())
            end = float(self.dlg_base.upper_spacing.text())
            increment = float(self.dlg_base.increment_spacing.text())
            spacing = [start]
            while True:
                if spacing[-1]+increment>end:
                    break
                else:
                    spacing.append(spacing[-1]+increment)
        else:
            spacing = [""]
        
        #We create the combinations
        combinations = list(product(rainfall, length, spacing))
        
        return combinations
    
    def modify_ikw_file_design(self,value_change=None):
        """Metod to create the .ikw file for the design execution"""
        #First we save the .ikw file path
        ruta = self.obtain_direction_vfsmod(self.dlg_base.design_vfs_file.text())
        if os.path.exists(ruta) and os.path.isfile(ruta):
            ikw = self.dlg_base.working_directory_vfsmod.text()+"\\design\\inputs\\design.ikw"
            #We substitute value of length
            with open(ikw, "r") as archivo:
                lineas = archivo.readlines()
            if value_change is None:
                value_change = self.dlg_base.base_length.text()
            def modify_number_in_string(numbers_str, index, new_value):
                # Use regex to find all numbers in the string
                matches = re.findall(r'\S+', numbers_str)
                # Replace the specific number at the given index
                matches[index] = str(new_value)
                # Rebuild the string by replacing only the specific number
                return re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
            lineas[2] = modify_number_in_string(lineas[2],0,value_change)
            
            #Then we update the segments
            number_segments = int(lineas[3])
            length = list(map(float, lineas[2].split()))[0]
            new_interval = length/number_segments

            #Data frame, but we take it from the original, not from the last execution
            #We import dataframe of segments from the original file
            with open(ruta, "r") as archivo:
                lineas_prj = archivo.readlines()
            ikw = lineas_prj[0].split("=")[-1]
            if not os.path.isabs(ikw): #relative path
                ikw = os.path.join(os.path.dirname(ruta), ikw)
            ikw = ikw.replace("\n", "")
            with open(ikw, "r") as archivo:
                lineas_ikw_original = archivo.readlines()
                
            df = pd.DataFrame(data = {"Distance":[list(map(float, lineas_ikw_original[x].split()))[0] for x in range(4,4+number_segments)],
                                 "Manning":[list(map(float, lineas_ikw_original[x].split()))[1] for x in range(4,4+number_segments)],
                                 "Slope":[list(map(float, lineas_ikw_original[x].split()))[2] for x in range(4,4+number_segments)]})
            
            actual_length = max(df["Distance"])
            length_to_change = float(value_change)
            if length_to_change <= actual_length:
                df = df[df["Distance"]<=length_to_change]
                df.loc[df.index[-1], "Distance"] = length_to_change
            else:
                df.loc[df.index[-1], "Distance"] = length_to_change
            
            #Add to the file information
            lineas[3] = modify_number_in_string(lineas[3],0,len(df)) #change number of segments
            contenido = ""
            for i in lineas[:4]:    
                contenido+=f"{i}"
            for i in range(len(df)):
                contenido +=f" {df.iloc[i,0]}   {df.iloc[i,1]}   {df.iloc[i,2]}\n"
            for i in lineas[-8:]:    
                contenido+=f"{i}"
            with open(self.dlg_base.working_directory_vfsmod.text()+"\\design\\inputs\\design.ikw", 'w') as archivo:
                archivo.write(contenido)
    
    def modify_inp_file_design(self,duration=None,rainfall = None):
        """Metod to change storm duration"""
        #First we save the .inp file path
        filepath = self.dlg_base.working_directory_vfsmod.text()+fr"\design\inputs\design.inp"
        with open(filepath, 'r') as file:
            lineas = file.readlines()
        numbers_str = lineas[0]
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        matches[4] = str(self.dlg_base.design_storm_duration.text())
        # Rebuild the string by replacing only the specific number
        lineas[0] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        with open(filepath, 'w') as archivo:
            for i in lineas:
                archivo.write(i)
    
    def progress_metod(self,number_combinations = None,start=False,execution=None, close = False):
        #Metod to add and update de progress bar
        if start == True:
            #Start of the progress bar
            self.progress_dialog = QProgressDialog("Starting sensitivity analysis...", "Cancel", 0, 101)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setWindowTitle("Progress")
            self.progress_dialog.show()
            QCoreApplication.processEvents()# Permitir que la interfaz gráfica responda
        elif not close:
            #Updates of progress bar
            #Creation of text
            text = f"Execution {execution}/{number_combinations}\n"
            #Add updates
            self.progress_dialog.setLabelText(text)
            self.progress_dialog.setValue(int(100*(execution/number_combinations)))
            QCoreApplication.processEvents()# Permitir que la interfaz gráfica responda
        #Close progress bar
        if close:
            self.progress_dialog.close()
    
   
    
    def modify_igr_file_design(self,value_change = None):
        """Metod to create the .igr file for the design execution"""
        #First we save the .igr file path
        filepath = self.dlg_base.working_directory_vfsmod.text()+fr"\design\inputs\design.igr"
        with open(filepath, 'r') as file:
            lineas = file.readlines()
        numbers_str = lineas[0]
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        matches[0] = str(self.dlg_base.base_spacing.text())
        # Rebuild the string by replacing only the specific number
        lineas[0] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        with open(filepath, 'w') as archivo:
            for i in lineas:
                archivo.write(i)
        
    def add_storm_duration_to_design(self):
        """Method to add the storm duration to the design"""
        ruta = self.obtain_direction_vfsmod(self.dlg_base.design_uh_file.text())
        if os.path.exists(ruta) and os.path.isfile(ruta):
            #First we open .lis
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            #Then we open .inp
            inp = lineas[0].split("=")[-1]
            if not os.path.isabs(inp): #relative path
                inp = os.path.join(os.path.dirname(ruta), inp)
            inp = inp.replace("\n", "") #take out the line jumps
            if os.path.exists(inp) and os.path.isfile(inp):
                with open(inp, "r") as archivo:
                    lineas = archivo.readlines()
                counter = 0
                for i in lineas[0].split(" "): #the first number is the storm precipitation
                    try:
                        float(i)
                        if counter ==4:
                            self.dlg_base.design_storm_duration.setText(str(float(i)))
                            break
                        counter +=1
                    except:
                        pass
            
    
    def add_vfs_length_spacing(self):
        """Method to add the length and spacing of vfs to the design"""
        ruta = self.obtain_direction_vfsmod(self.dlg_base.design_vfs_file.text())
        if os.path.exists(ruta) and os.path.isfile(ruta):
            #First we open .prj
            with open(ruta, "r") as archivo:
                lineas = archivo.readlines()
            #Then we open .ikw and .igr
            ikw = lineas[0].split("=")[-1]
            igr = lineas[2].split("=")[-1]
            if not os.path.isabs(ikw): #relative path
                ikw = os.path.join(os.path.dirname(ruta), ikw)
            if not os.path.isabs(igr): #relative path
                igr = os.path.join(os.path.dirname(ruta), igr)
            ikw = ikw.replace("\n", "") #take out the line jumps
            igr = igr.replace("\n", "") #take out the line jumps
            with open(ikw, "r") as archivo:
                lineas = archivo.readlines()
            for i in lineas[2].split(" "): #the first number bufer length
                try:
                    self.dlg_base.base_length.setText(str(float(i)))
                    break
                except:
                    pass
            with open(igr, "r") as archivo:
                lineas = archivo.readlines()
            for i in lineas[0].split(" "): #the first number is spacing
                try:
                    self.dlg_base.base_spacing.setText(str(float(i)))
                    break
                except:
                    pass
        

    def update_project_files(self):
        """Method to update the design project files when text changed"""
        #Obtain the absolute paths
        project_name = self.dlg_base.name_files.text()
        
        #Function to add text 
        def add_text(line, process):
            if process == "uh":
                line.setText(project_name+".lis")
            elif process == "vfs":
                line.setText(project_name+".prj")
        #Add paths to design
        add_text(self.dlg_base.design_uh_file,"uh")
        add_text(self.dlg_base.design_vfs_file,"vfs")
        #Add paths to calibration
        add_text(self.dlg_base.vfs_project,"vfs")
        add_text(self.dlg_base.vfs_file,"vfs")
        #Add paths to sensitivity analysis
        add_text(self.dlg_base.uh_file_sensitivity,"uh")
        add_text(self.dlg_base.vfs_file_sensitivity,"vfs")
        #Add paths to uncertainity analysis
        add_text(self.dlg_base.uh_file_uncertainity,"uh")
        add_text(self.dlg_base.vfs_file_uncertainity,"vfs")
    
    def folder_creation_vfsmod(self):
        """Method to create folders if they not exist for the output"""
        #Function to create a folder
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.dlg_base.working_directory_vfsmod.text()
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
        
        #Creation of folders
        lineEdits = [self.dlg_base.line_project_vfsmod,self.dlg_base.line_overland,self.dlg_base.line_infiltration,
            self.dlg_base.line_buffer,self.dlg_base.line_incoming,self.dlg_base.line_storm,self.dlg_base.line_source,
            self.dlg_base.line_water,self.dlg_base.line_sediment,self.dlg_base.line_flow,self.dlg_base.line_hydrograph_2,
            self.dlg_base.line_waterland,self.dlg_base.line_overall,self.dlg_base.line_quality]
                
        for i in lineEdits:
            directory = os.path.dirname(i.text())
            if not os.path.exists(directory):
                create_folder(directory)
        
    
    
    def error_handling_vfsmod(self):
        """Method to handle errors in VFSMOD execution"""
        #Check if input files exist
        lines = [self.dlg_base.line_overland,self.dlg_base.line_infiltration,
                    self.dlg_base.line_buffer,self.dlg_base.line_incoming,self.dlg_base.line_storm,self.dlg_base.line_source]
                    
        if self.dlg_base.water_quality.isChecked():
            lines.append(self.dlg_base.line_water)
            
        for i in lines:
            if not os.path.exists(self.obtain_direction_vfsmod(i.text())):
                self.warning_message(f"Check input data\n{self.obtain_direction_vfsmod(i.text())} does not exist and is required to run VFSMOD.")
                self.end_execution = True
                return 
    
    
    def update_bat_vfsmod(self):
        """Metod to update bat for the execution of VFS"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{os.path.dirname(self.obtain_direction_vfsmod(self.dlg_base.line_project_vfsmod.text()))}\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\vfsm" {os.path.basename(self.dlg_base.line_project_vfsmod.text())}'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    def create_prj_file(self):
        """Method to create .prj file for VFSMOD execution"""
        prj_file = self.obtain_direction_vfsmod(self.dlg_base.line_project_vfsmod.text())
        with open(prj_file, 'w') as archivo:
            archivo.write(f"ikw={self.obtain_direction_vfsmod(self.dlg_base.line_overland.text())}  \n")
            archivo.write(f"iso={self.obtain_direction_vfsmod(self.dlg_base.line_infiltration.text())}  \n")
            archivo.write(f"igr={self.obtain_direction_vfsmod(self.dlg_base.line_buffer.text())}  \n")
            archivo.write(f"isd={self.obtain_direction_vfsmod(self.dlg_base.line_incoming.text())}  \n")
            archivo.write(f"irn={self.obtain_direction_vfsmod(self.dlg_base.line_storm.text())}  \n")
            archivo.write(f"iro={self.obtain_direction_vfsmod(self.dlg_base.line_source.text())}  \n")
            if self.dlg_base.water_quality.isChecked():
                archivo.write(f"iwq={self.obtain_direction_vfsmod(self.dlg_base.line_water.text())}  \n")
            archivo.write(f"og1={self.obtain_direction_vfsmod(self.dlg_base.line_sediment.text())}  \n")
            archivo.write(f"og2={self.obtain_direction_vfsmod(self.dlg_base.line_flow.text())}  \n")
            archivo.write(f"ohy={self.obtain_direction_vfsmod(self.dlg_base.line_hydrograph_2.text())}  \n")
            archivo.write(f"osm={self.obtain_direction_vfsmod(self.dlg_base.line_waterland.text())}  \n")
            archivo.write(f"osp={self.obtain_direction_vfsmod(self.dlg_base.line_overall.text())}  \n")
            if self.dlg_base.water_quality.isChecked():
                archivo.write(f"owq={self.obtain_direction_vfsmod(self.dlg_base.line_quality.text())}  \n")
    
    
    def copy_to_clipboard_hydrograph(self):
        """Method to copy to clipboard the hydrograph produced in UH"""
        # Create list with values
        filas = [f"{c1}\t{c2}" for c1, c2 in zip(self.hydrograph_uh_1, self.hydrograph_uh_2)]

        # Join rows in a single string
        texto = "\n".join(filas)
        # Copying to the clipboard depending on operating system
        if os.name == 'nt':  # Windows
            subprocess.run("clip", universal_newlines=True, input=texto)
        elif os.name == 'posix':  # macOS / Linux
            subprocess.run("pbcopy", universal_newlines=True, input=texto)

    
    def add_hyetograph_to_dialog(self):
        """Method to add the hyetograph information to the dialog"""
        #Disconnect update of graph to avoid all the updates
        self.dlg_vfsmod_hyetograph.tableWidget.itemChanged.disconnect(self.update_vfsmod_hyetograph_graph)
        #Obtain information
        direccion = self.obtain_direction_vfsmod(self.dlg_base.line_storm.text())
        if not os.path.exists(direccion):
            self.warning_message(f"{direccion} does not exist")
            return
        with open(direccion, "r") as archivo:
            lineas = archivo.readlines()
            columna_1 = []
            columna_2 = []
            for linea in lineas:
                columnas = linea.split()
                if len(columnas) >= 2:
                    columna_1.append(float(columnas[0]))
                    columna_2.append(float(columnas[1]))
        #Add rainfall maximum intensity
        self.dlg_vfsmod_hyetograph.maximum_rainfall.setText(str(columna_2[0]))
        #Add the table
        time = columna_1[1:]
        precipitation = columna_2[1:]
        df = pd.DataFrame(data = {"time":time,"precipitation":precipitation})
        self.dlg_vfsmod_hyetograph.tableWidget.setRowCount(len(time))
        for fila in range(len(time)):
            for columna in range(2):
                item = QTableWidgetItem(str(df.iloc[fila,columna]))
                self.dlg_vfsmod_hyetograph.tableWidget.setItem(fila, columna, item)
                item.setTextAlignment(Qt.AlignCenter)
        
        #We show the dialog
        self.dlg_vfsmod_hyetograph.show()
        self.show_hietograph_vfsmod_graph()
        #Connect again update of graph to avoid all the updates
        self.dlg_vfsmod_hyetograph.tableWidget.itemChanged.connect(self.update_vfsmod_hyetograph_graph)
        self.update_vfsmod_hyetograph_graph()
    
    def add_hydrograph_to_dialog(self):
        """Method to add the hyetograph information to the dialog"""
        #Avoid the updating of graph that many times
        self.dlg_vfsmod_hydrograph.tableWidget.itemChanged.disconnect(self.update_vfsmod_hydrograph_graph)
        #Obtain information
        direccion = self.obtain_direction_vfsmod(self.dlg_base.line_source.text())
        if not os.path.exists(direccion):
            self.warning_message(f"{direccion} does not exist")
            return
        with open(direccion, "r") as archivo:
            lineas = archivo.readlines()
            columna_1 = []
            columna_2 = []
            for linea in lineas:
                columnas = linea.split()
                if len(columnas) >= 2:
                    columna_1.append(float(columnas[0]))
                    columna_2.append(float(columnas[1]))
        #Add source area width, source area flow path length and peak flow of incoming hydrograph
        self.dlg_vfsmod_hydrograph.width.setText(str(columna_1[0]))
        self.dlg_vfsmod_hydrograph.length.setText(str(columna_2[0]))
        self.dlg_vfsmod_hydrograph.peak.setText(str(columna_2[1]))
        #Add the table
        time = columna_1[2:]
        runoff = columna_2[2:]
        df = pd.DataFrame(data = {"time":time,"runoff":runoff})
        self.dlg_vfsmod_hydrograph.tableWidget.setRowCount(len(time))
        for fila in range(len(time)):
            for columna in range(2):
                item = QTableWidgetItem(str(df.iloc[fila,columna]))
                self.dlg_vfsmod_hydrograph.tableWidget.setItem(fila, columna, item)
                item.setTextAlignment(Qt.AlignCenter)
        #We show the dialog
        self.dlg_vfsmod_hydrograph.show()
        self.show_hydrograph_vfsmod_graph()
        #Connect again update of graph to avoid all the updates
        self.dlg_vfsmod_hydrograph.tableWidget.itemChanged.connect(self.update_vfsmod_hydrograph_graph)
        self.update_vfsmod_hydrograph_graph()
        
    def enable_disable_water_quality_dialog(self):
        """Method to enable/disable widgets in the water quality dialog"""
        if self.dlg_water_quality.check_direct.isChecked():
            self.dlg_water_quality.line_koc.setReadOnly(True)
            self.dlg_water_quality.line_oc.setReadOnly(True)
            self.dlg_water_quality.line_kd.setReadOnly(False)
            self.dlg_water_quality.line_koc.setStyleSheet("background-color: #d9d9d9;")
            self.dlg_water_quality.line_oc.setStyleSheet("background-color: #d9d9d9;")
            self.dlg_water_quality.line_kd.setStyleSheet("background-color: #f0f0f0;")
            
        else:
            self.dlg_water_quality.line_koc.setReadOnly(False)
            self.dlg_water_quality.line_oc.setReadOnly(False)
            self.dlg_water_quality.line_kd.setReadOnly(True)
            self.dlg_water_quality.line_koc.setStyleSheet("background-color: #f0f0f0;")
            self.dlg_water_quality.line_oc.setStyleSheet("background-color: #f0f0f0;")
            self.dlg_water_quality.line_kd.setStyleSheet("background-color: #d9d9d9;")
            
            
    
    def show_soil_curves(self):
        """Show soil curves dialog with changes in the text"""
        #Add text
        if self.dlg_infiltration_soil.radioButton_3.isChecked(): 
            self.dlg_soil_curves.label_2.setText("THETA TYPE: van Genuchten")
            self.dlg_soil_curves.label_3.setText("OR")
            self.dlg_soil_curves.label_4.setText("VGALPHA, 1/m")
            self.dlg_soil_curves.label_5.setText("VGN")
            self.dlg_soil_curves.label_6.setText("VGM")
            self.dlg_soil_curves.label_6.setVisible(True)
            self.dlg_soil_curves.lineEdit_4.setVisible(True)
            
        elif self.dlg_infiltration_soil.radioButton_4.isChecked(): 
            self.dlg_soil_curves.label_2.setText("THETA TYPE: Brooks and Corey")
            self.dlg_soil_curves.label_3.setText("OR")
            self.dlg_soil_curves.label_4.setText("BCALPHA, 1/m")
            self.dlg_soil_curves.label_5.setText("BCLAMBDA")
            self.dlg_soil_curves.label_6.setVisible(False)
            self.dlg_soil_curves.lineEdit_4.setVisible(False)
            
        if self.dlg_infiltration_soil.radioButton_5.isChecked(): 
            self.dlg_soil_curves.label_7.setText("KUN TYPE: van Genuchten")
            self.dlg_soil_curves.label_8.setText("VGM")
            self.dlg_soil_curves.label_9.setVisible(False)
            self.dlg_soil_curves.lineEdit_6.setVisible(False)
            
        elif self.dlg_infiltration_soil.radioButton_6.isChecked(): 
            self.dlg_soil_curves.label_7.setText("KUN TYPE: Brooks and Corey")
            self.dlg_soil_curves.label_8.setText("BCETA")
            self.dlg_soil_curves.label_9.setVisible(True)
            self.dlg_soil_curves.lineEdit_6.setVisible(True)
            
        elif self.dlg_infiltration_soil.radioButton_7.isChecked(): 
            self.dlg_soil_curves.label_7.setText("KUN TYPE: Gardner")
            self.dlg_soil_curves.label_8.setText("GDALPHA")
            self.dlg_soil_curves.label_9.setVisible(False)
            self.dlg_soil_curves.lineEdit_6.setVisible(False)
            
        #Show dialog
        self.dlg_soil_curves.show()
    
    def update_k_units_cmh_1(self):
        """Method to update K units (cm/h) when text changed in the other units for the first layer"""
        try:
            try:
                self.dlg_infiltration_soil.line_vertical_cmh.textChanged.disconnect(self.update_k_units_ms_1)
            except:
                pass
            self.dlg_infiltration_soil.line_vertical_cmh.setText(f"{float(self.dlg_infiltration_soil.line_vertical_ms.text())*(100*3600)}")
            self.dlg_infiltration_soil.line_vertical_cmh.textChanged.connect(self.update_k_units_ms_1)
        except:
            pass
            
    def update_k_units_ms_1(self):
        """Method to update K units (m/s) when text changed in the other units for the first layer"""
        try:
            try:
                self.dlg_infiltration_soil.line_vertical_ms.textChanged.disconnect(self.update_k_units_cmh_1)
            except:
                pass
            self.dlg_infiltration_soil.line_vertical_ms.setText(f"{float(self.dlg_infiltration_soil.line_vertical_cmh.text())/(100*3600)}")
            self.dlg_infiltration_soil.line_vertical_ms.textChanged.connect(self.update_k_units_cmh_1)
        except:
            pass
    
    def update_k_units_cmh_2(self):
        """Method to update K units (cm/h) when text changed in the other units for the second layer"""
        try:
            try:
                self.dlg_infiltration_soil.line_vertical_cmh_2.textChanged.disconnect(self.update_k_units_ms_2)
            except:
                pass
            self.dlg_infiltration_soil.line_vertical_cmh_2.setText(f"{float(self.dlg_infiltration_soil.line_vertical_ms_2.text())*(100*3600)}")
            self.dlg_infiltration_soil.line_vertical_cmh_2.textChanged.connect(self.update_k_units_ms_2)
        except:
            pass
        
    def update_k_units_ms_2(self):
        """Method to update K units (m/s) when text changed in the other units for the second layer"""
        try:
            try:
                self.dlg_infiltration_soil.line_vertical_ms_2.textChanged.disconnect(self.update_k_units_cmh_2)
            except:
                pass
            self.dlg_infiltration_soil.line_vertical_ms_2.setText(f"{float(self.dlg_infiltration_soil.line_vertical_cmh_2.text())/(100*3600)}")
            self.dlg_infiltration_soil.line_vertical_ms_2.textChanged.connect(self.update_k_units_cmh_2)
        except:
            pass
            
    def show_input_soil_properties(self):
        """Method to add the option of putting the information about Input h_e(m)?"""
        if self.dlg_infiltration_soil.check_input.isChecked():
            self.dlg_infiltration_soil.line_input.setVisible(True)
        else:
            self.dlg_infiltration_soil.line_input.setVisible(False)
    
    def show_water_table(self):
        """Method to add water table dialog option"""
        if self.dlg_infiltration_soil.check_water_table.isChecked():
            self.dlg_infiltration_soil.frame_6.setVisible(True)
            #We change color of lineEdits that are not going to be modifiable
            self.dlg_infiltration_soil.line_average.setStyleSheet("background-color: #d9d9d9;")
            self.dlg_infiltration_soil.line_average_2.setStyleSheet("background-color: #d9d9d9;")
            self.dlg_infiltration_soil.line_initial.setStyleSheet("background-color: #d9d9d9;")
            self.dlg_infiltration_soil.line_initial_2.setStyleSheet("background-color: #d9d9d9;")
            #We put not modifiable
            self.dlg_infiltration_soil.line_average.setReadOnly(True)
            self.dlg_infiltration_soil.line_average_2.setReadOnly(True)
            self.dlg_infiltration_soil.line_initial.setReadOnly(True)
            self.dlg_infiltration_soil.line_initial_2.setReadOnly(True)
            
        else:
            #We change color of lineEdits that are going to be modifiable
            self.dlg_infiltration_soil.frame_6.setVisible(False)
            self.dlg_infiltration_soil.line_average.setStyleSheet("background-color: #f0f0f0;")
            self.dlg_infiltration_soil.line_average_2.setStyleSheet("background-color: #f0f0f0;")
            self.dlg_infiltration_soil.line_initial.setStyleSheet("background-color: #f0f0f0;")
            self.dlg_infiltration_soil.line_initial_2.setStyleSheet("background-color: #f0f0f0;")
            #We put modifiable
            self.dlg_infiltration_soil.line_average.setReadOnly(False)
            self.dlg_infiltration_soil.line_average_2.setReadOnly(False)
            self.dlg_infiltration_soil.line_initial.setReadOnly(False)
            self.dlg_infiltration_soil.line_initial_2.setReadOnly(False)
    
    def show_second_layer(self):
        """Method to add or quit second layer in infiltration and soil properties"""
        if self.dlg_infiltration_soil.radio_one.isChecked():
            self.dlg_infiltration_soil.frame_5.setVisible(False)
        if self.dlg_infiltration_soil.radio_two.isChecked():
            self.dlg_infiltration_soil.frame_5.setVisible(True)
    
    def add_row(self):
        """Method to add rows in the buffer segment table"""
        table = self.dlg_buffer_segment.tableWidget
        row_position = table.rowCount()
        table.insertRow(row_position)
        # Center cell contents in the new row
        for column in range(table.columnCount()):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_position, column, item)

    
    def remove_row(self,numero_table_input):
        """Method to add rows in the buffer segment table"""
        table = self.dlg_buffer_segment.tableWidget
        selected_row = table.rowCount()
        if selected_row >= 0:
            table.removeRow(selected_row-1)
        #Update graph
        self.update_buffer_segment_graph()
    
    def vfsmod_hyetograph_add_row(self):
        """Method to add row in the vfsmod hyetograph"""
        table = self.dlg_vfsmod_hyetograph.tableWidget
        row_position = table.rowCount()
        table.insertRow(row_position)
        # Center cell contents in the new row
        for column in range(table.columnCount()):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_position, column, item)
        
    def vfsmod_hyetograph_remove_row(self):
        """Method to remove row in the vfsmod hyetograph"""
        table = self.dlg_vfsmod_hyetograph.tableWidget
        selected_row = table.rowCount()
        if selected_row >= 0:
            table.removeRow(selected_row-1)
        #Update graph
        self.update_vfsmod_hyetograph_graph()
    
    def vfsmod_hydrograph_add_row(self):
        """Method to add row in the vfsmod hydrograph"""
        table = self.dlg_vfsmod_hydrograph.tableWidget
        row_position = table.rowCount()
        table.insertRow(row_position)
        # Center cell contents in the new row
        for column in range(table.columnCount()):
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row_position, column, item)
        
    def vfsmod_hydrograph_remove_row(self):
        """Method to remove row in the vfsmod hydrograph"""
        table = self.dlg_vfsmod_hydrograph.tableWidget
        selected_row = table.rowCount()
        if selected_row >= 0:
            table.removeRow(selected_row-1)
        #Update graph
        self.update_vfsmod_hydrograph_graph()
    
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QVfsmod'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""
        
        # show the dialog
        self.dlg_base.show()
        self.dlg_base.raise_()
        self.dlg_base.activateWindow()
    
    
    def select_directory_vfsmod(self):
        """Method to select the directory among the local files for VFSMOD"""
        fname = QFileDialog.getExistingDirectory(self.dlg_base, "Select directory", "C/")
        if fname!="":
            self.dlg_base.working_directory_vfsmod.setText(fname)
    
    def water_quality_dialog(self):
        """Method to add in the dialog the widgets when water quality is selected"""
        if self.dlg_base.water_quality.isChecked():
            #Combobox
            self.dlg_base.combo_water.setVisible(True)
            #Water quality properties
            self.dlg_base.label_quality_properties.setVisible(True)
            self.dlg_base.line_water.setVisible(True)
            self.dlg_base.edit_water.setVisible(True)
            self.dlg_base.browse_water.setVisible(True)
            #Water quality summary
            self.dlg_base.label_water_summary.setVisible(True)
            self.dlg_base.line_quality.setVisible(True)
            self.dlg_base.browse_quality.setVisible(True)
            self.dlg_base.output_quality.setVisible(True)
        else:
            #Combobox
            self.dlg_base.combo_water.setVisible(False)
            #Water quality properties
            self.dlg_base.label_quality_properties.setVisible(False)
            self.dlg_base.line_water.setVisible(False)
            self.dlg_base.edit_water.setVisible(False)
            self.dlg_base.browse_water.setVisible(False)
            #Water quality summary
            self.dlg_base.label_water_summary.setVisible(False)
            self.dlg_base.line_quality.setVisible(False)
            self.dlg_base.browse_quality.setVisible(False)
            self.dlg_base.output_quality.setVisible(False)
    
    def select_lis_design(self):
        """Method to select the .lis file among the local files for the design"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select UH Project File",working_directory , "LIS files (*.lis)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.design_uh_file.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.design_uh_file.setText(fname[0])
    
    def select_prj_design(self):
        """Method to select the .prj file among the local files for the design"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Filter Strip Project File", working_directory, "PRJ files (*.prj)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.design_vfs_file.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.design_vfs_file.setText(fname[0])
    
    def select_lis(self):
        """Method to select the .lis file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select UH Project File",working_directory , "LIS files (*.lis)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.uh_file.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.uh_file.setText(fname[0])
            #Update filepaths
            self.add_values_uh_outputs_dialog()
            
    def select_inp(self):
        """Method to select the .inp file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select UH Input File", working_directory, "INP files (*.inp)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.uh_input.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.uh_input.setText(fname[0])


    def select_iro(self):
        """Method to select the .iro file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Hydrograph File", working_directory, "IRO files (*.iro)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_hydrograph.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_hydrograph.setText(fname[0])
        #Check if UH outputs exist
        self.check_uh_output_exist()
    
    def select_irn(self):
        """Method to select the .irn file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Hyetograph File", working_directory, "IRN files (*.irn)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_hyetograph.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_hyetograph.setText(fname[0])
        #Check if UH outputs exist
        self.check_uh_output_exist()
                
    def select_isd(self):
        """Method to select the .isd file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Incoming Sedimentograph File", working_directory, "ISD files (*.isd)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_sedimentograph.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_sedimentograph.setText(fname[0])
        #Check if UH outputs exist
        self.check_uh_output_exist()
                
    def select_out(self):
        """Method to select the .out file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Output Information Part 1 File", working_directory, "OUT files (*.out)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_output_1.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_output_1.setText(fname[0])
        #Check if UH outputs exist
        self.check_uh_output_exist()
                
    def select_hyt(self):
        """Method to select the .hyt file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Output Information Part 2 File", working_directory, "HYT files (*.hyt)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_output_2.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_output_2.setText(fname[0])
        #Check if UH outputs exist
        self.check_uh_output_exist()  
    
    
    def select_prj(self):
        """Method to select the .prj file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Filter Strip Project File", working_directory, "PRJ files (*.prj)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_project_vfsmod.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_project_vfsmod.setText(fname[0])
            #Update filepaths
            self.add_values_vfs_outputs_dialog()
            
    def select_ikw(self):
        """Method to select the .ikw file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Overland Flow Inputs File", working_directory, "IKW files (*.ikw)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_overland.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_overland.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_iso(self):
        """Method to select the .iso file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Infiltration - Soil Properties File", working_directory, "ISO files (*.iso)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_infiltration.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_infiltration.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_igr(self):
        """Method to select the .igr file among the local files"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Buffer Vegetation Properties File", working_directory, "IGR files (*.igr)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_buffer.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_buffer.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_isd_vfsmod(self):
        """Method to select the .isd file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Incoming Sediment Characteristics File", working_directory, "ISD files (*.isd)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_incoming.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_incoming.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_irn_vfsmod(self):
        """Method to select the .irn file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Storm Hyetograph File", working_directory, "IRN files (*.irn)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_storm.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_storm.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_iro_vfsmod(self):
        """Method to select the .iro file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Source Area Storm Runoff File", working_directory, "IRO files (*.iro)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_source.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_source.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_iwq(self):
        """Method to select the .iwq file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Water Quality Properties File", working_directory, "IWQ files (*.iwq)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_water.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_water.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_og1(self):
        """Method to select the .og1 file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Sediment Transport File", working_directory, "OG1 files (*.og1)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_sediment.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_sediment.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_og2(self):
        """Method to select the .og2 file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Flow throug FVS File", working_directory, "OG2 files (*.og2)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_flow.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_flow.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
        
    def select_ohy(self):
        """Method to select the .ohy file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Detailed Hydrograph File", working_directory, "OHY files (*.ohy)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_hydrograph_2.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_hydrograph_2.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_osm(self):
        """Method to select the .osm file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Water and Sediment Balances File", working_directory, "OSM files (*.osm)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_waterland.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_waterland.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
    
    def select_osp(self):
        """Method to select the .osp file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Overall Summary File", working_directory, "OSP files (*.osp)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_overall.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_overall.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()

    def select_owq(self):
        """Method to select the .owq file among the local files for vfsmod"""
        working_directory = self.dlg_base.working_directory_vfsmod.text()
        fname = QFileDialog.getOpenFileName(self.dlg_base, "Select Water Quality Summary File", working_directory, "OWQ files (*.owq)")
        if fname[0]!="":
            #Put the relative path if the file is inside the folder
            if os.path.commonpath([os.path.normpath(fname[0]), os.path.normpath(working_directory)]) == os.path.normpath(working_directory):
                self.dlg_base.line_quality.setText(os.path.relpath(fname[0], working_directory))
            else: #absolute path
                self.dlg_base.line_quality.setText(fname[0])
        #Check if VFSMOD outputs exist
        self.check_vfsmod_output_exist()
 
    
    def uh_execution(self):
        """Method for executing the UH module"""
        
        #Save inputs from the dialog
        self.project_file = self.dlg_base.working_directory_vfsmod.text()
        self.name_project = self.dlg_base.name_files.text()
        
        #Create required folders in working directory
        self.create_folders_in_directory()
        
        #Create .inp file
        self.create_inp_file()
        
        #Create .lis file
        self.create_lis_file()
        
        #Update .bat information for the execution of UH
        self.update_bat_uh()
        
        #Execute bat
        resultado = subprocess.run([self.plugin_directory+"\\executables\\execution.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        
        #Put warning
        if not "...FINISHED..." in resultado.stdout:
            self.warning_message(str(resultado.stdout))
        else:
            self.warning_message("UH executed succesfully!")
            
        
        #Check if UH outputs exist
        self.check_uh_output_exist()
    
    def warning_message(self,message):
        """Method to put a warning message"""
        #Put text
        self.dlg_warning_message.warning.setText(message)
        #Put to the front
        self.dlg_warning_message.raise_()
        self.dlg_warning_message.activateWindow()
        #Adjust size
        self.dlg_warning_message.adjustSize()
        #Show the dialog
        self.dlg_warning_message.show()
        
    def update_bat_uh(self):
        """Metod to update bat for the execution of UH"""
        f = open(self.plugin_directory+"\\executables\\execution.bat","w+")
        linea_uno = "cd {}".format(f'"{os.path.dirname(self.obtain_direction_vfsmod(self.dlg_base.uh_file.text()))}\\"')
        linea_dos = f'"{self.plugin_directory}\\executables\\uh" {os.path.basename(self.dlg_base.uh_file.text())}'
        linea_tres = "Pause"
        f.write("{} \n".format(linea_uno))
        f.write("{} \n".format(linea_dos))
        f.write("{} \n".format(linea_tres))
        f.close()
    
    
    def obtain_direction_vfsmod(self,direction):
        """Method to obtain the absolute path direction. The difference with the other is that
        here is respect to the working directory of vfsmod"""
        carpeta = self.dlg_base.working_directory_vfsmod.text()
        if not os.path.isabs(direction): #relative path
            return os.path.join(carpeta, direction)
        else: #absolute path
            return direction
            
    def create_lis_file(self):
        """Metod to create the .lis file for the UH execution"""
        lis_file = self.obtain_direction_vfsmod(self.dlg_base.uh_file.text())
        with open(lis_file, 'w') as archivo:
            archivo.write(f"inp={self.obtain_direction_vfsmod(self.dlg_base.uh_input.text())}  \n")
            archivo.write(f"iro={self.obtain_direction_vfsmod(self.dlg_base.line_hydrograph.text())}  \n")
            archivo.write(f"irn={self.obtain_direction_vfsmod(self.dlg_base.line_hyetograph.text())}  \n")
            archivo.write(f"isd={self.obtain_direction_vfsmod(self.dlg_base.line_sedimentograph.text())}  \n")
            archivo.write(f"out={self.obtain_direction_vfsmod(self.dlg_base.line_output_1.text())}  \n")
            archivo.write(f"hyt={self.obtain_direction_vfsmod(self.dlg_base.line_output_2.text())}  \n")
        #Update the design dialog
        self.add_storm_duration_to_design()
    
    def create_inp_file(self):
        """Metod to create the .inp file for the UH execution"""
        #Inputs
        rainfall_amount = float(self.dlg_base.rainfall.text())
        storm_duration = float(self.dlg_base.storm_duration.text())
        curve_number = float(self.dlg_base.curve_number.text())
        length = float(self.dlg_base.length_source.text())
        slope = float(self.dlg_base.slope_source.text())
        area = float(self.dlg_base.area_source.text())
        K_factor = float(self.dlg_base.k_factor.text())
        organic_matter = float(self.dlg_base.organic_matter.text())
        particle_size = float(self.dlg_base.particle_diameter.text())
        crop_factor = float(self.dlg_base.crop_factor.text())
        practice_factor = float(self.dlg_base.practice_factor.text())
        
        if self.dlg_base.williams.isChecked(): rainfall_factor = 1
        elif self.dlg_base.creams_gleams.isChecked(): rainfall_factor = 2
        
        soil_type = [self.dlg_base.soil_type.itemText(i) for i in range(self.dlg_base.soil_type.count())][self.dlg_base.soil_type.currentIndex()]
        storm_type = int(self.dlg_base.storm_type.currentIndex())+1
        
        try:
            time_to_half = float(self.dlg_user_storm.half.text())
        except:
            self.warning_message("Please select correct time to the middle time in the storm (P/P24=0.5)")
        
        table = self.dlg_user_storm.tableWidget
        rows = table.rowCount()
        user_defined_storm = pd.DataFrame(data = {"Time":[table.item(row, 0).text() for row in range(rows)],
            "Cumulated":[table.item(row, 1).text() for row in range(rows)]})
        
        #Create file
        inp_file = self.obtain_direction_vfsmod(self.dlg_base.uh_input.text())
        with open(inp_file, 'w') as archivo:
            linea_uno = f" {rainfall_amount}  {curve_number}  {area}  {storm_type}  {storm_duration}  {length}  {slope}       'P,CN,A,storm type,D,L,Y"
            linea_dos = "                                           'Note: Storm type I,IA,II,III (j=1,4)"
            linea_tres = f"{soil_type}                     'Soil Type"
            linea_cuatro = f"  {K_factor}  {crop_factor}  {practice_factor}  {particle_size}                           'K, C, P, Dp "
            linea_cinco = f"  {rainfall_factor}                                 'IREOTY"
            linea_seis = f"  {organic_matter}                            'Soil Org Matter"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            archivo.write(f"{linea_tres}\n")
            archivo.write(f"{linea_cuatro}\n")
            archivo.write(f"{linea_cinco}\n")
            archivo.write(f"{linea_seis}\n")
            if storm_type == 5:
                archivo.write(f"{time_to_half} 'tmid (h) Time for mid storm point P/P24=0.5\n")
                for i in range(len(user_defined_storm)):
                    archivo.write(f"{user_defined_storm.iloc[i,0]}	{user_defined_storm.iloc[i,1]}\n")
            archivo.write("\n")
        
        
    def create_ikw_file(self,close =False):
        """Method to create .ikw file"""
        #Inputs
        simulation_title = self.dlg_overland_flow.simulation_title.text()
        buffer_length = self.dlg_overland_flow.length.text()
        width_strip = self.dlg_overland_flow.width.text()
        number_nodes = self.dlg_overland_flow.nodes.text()
        time_weigth = self.dlg_overland_flow.time.text()
        number_element_nodal = self.dlg_overland_flow.nodal.text()
        petrov_galerkin = self.dlg_overland_flow.petrov.text()
        courant_number = self.dlg_overland_flow.courant.text()
        maximum_iterations = self.dlg_overland_flow.maximum.text()
        output_element_information = self.dlg_overland_flow.output.text()
        #Buffer segment
        table = self.dlg_buffer_segment.tableWidget
        rows = table.rowCount()
        buffer_segment_data = pd.DataFrame(data = {"Distance":[table.item(row, 0).text() for row in range(rows)],
            "Roughness":[table.item(row, 1).text() for row in range(rows)],
            "Slope":[table.item(row, 2).text() for row in range(rows)]})
        #Water quality
        if self.dlg_base.water_quality.isChecked(): water_quality =1
        else: water_quality = 0
        
        ikw_file =self.obtain_direction_vfsmod(self.dlg_base.line_overland.text())
        with open(ikw_file, 'w') as archivo:
            linea_uno = f"{simulation_title}                      "
            linea_dos = f" {width_strip}"
            linea_tres = f" {buffer_length}   {number_nodes}   {time_weigth}   {courant_number}   {maximum_iterations}   {number_element_nodal}   {output_element_information}   {petrov_galerkin}"
            linea_cuatro = f" {len(buffer_segment_data)}"
            linea_cinco = ""
            for i in range(len(buffer_segment_data)):
                linea_cinco +=f" {buffer_segment_data.iloc[i,0]}   {buffer_segment_data.iloc[i,1]}   {buffer_segment_data.iloc[i,2]}\n"
            linea_seis = f" {water_quality}"
            linea_siete = "-------------------------------------\n title\n fwidth\n vl n thetaw cr maxiter npol ielout kpg\n nprop\n sx(iprop), rna(iprop), soa(iprop), iprop=1,nprop\nWQ flag=1 if Pesticides Bayer Option has been chosen\n"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            archivo.write(f"{linea_tres}\n")
            archivo.write(f"{linea_cuatro}\n")
            archivo.write(f"{linea_cinco}")
            archivo.write(f"{linea_seis}\n")
            archivo.write(f"{linea_siete}")
        
        #Update value in design
        self.add_vfs_length_spacing()
        
        #Close dialog
        if close:
            self.dlg_overland_flow.close()
        
    def create_iso_file(self,close =False):
        """Method to create .iso file"""
        #Inputs
        #Layer one
        saturate_conductivity = float(self.dlg_infiltration_soil.line_vertical_ms.text())
        suction_front = float(self.dlg_infiltration_soil.line_average.text())
        saturated_content = float(self.dlg_infiltration_soil.line_saturated.text())
        initial_content = float(self.dlg_infiltration_soil.line_initial.text())
        maximum_storage = float(self.dlg_infiltration_soil.line_maximum.text())
        fraction_filter  = float(self.dlg_infiltration_soil.line_fraction.text())
        #Layer two
        saturate_conductivity_2 = float(self.dlg_infiltration_soil.line_vertical_ms_2.text())
        suction_front_2 = float(self.dlg_infiltration_soil.line_average_2.text())
        saturated_content_2 = float(self.dlg_infiltration_soil.line_saturated_2.text())
        initial_content_2 = float(self.dlg_infiltration_soil.line_initial_2.text())
        
        #If there is a second layer then we average with depth
        if self.dlg_infiltration_soil.radio_two.isChecked():
            depth_one = float(self.dlg_infiltration_soil.line_bottom.text())
            depth_two = float(self.dlg_infiltration_soil.line_bottom_2.text())
            saturate_conductivity = (saturate_conductivity*depth_one+saturate_conductivity_2*depth_two)/(depth_one+depth_two)
            suction_front = (suction_front*depth_one+suction_front_2*depth_two)/(depth_one+depth_two)
            saturated_content = (saturated_content*depth_one+saturated_content_2*depth_two)/(depth_one+depth_two)
            initial_content = (initial_content*depth_one+initial_content_2*depth_two)/(depth_one+depth_two)
        
        #We create the file
        iso_file =self.obtain_direction_vfsmod(self.dlg_base.line_infiltration.text())
        #If no water table
        if not self.dlg_infiltration_soil.check_water_table.isChecked():
            with open(iso_file, 'w') as archivo:
                linea_uno = f"  {saturate_conductivity}   {suction_front}   {saturated_content}   {initial_content}   {maximum_storage}   {fraction_filter}"     
                linea_dos = " \n     -------------------------------------\n Ks(m/s)   Sav(m)  Theta-s   Theta-i   Sm(m)   Schk(ponding ck)  WTD(Water Table Depth / No value means 'standard' iso file)\n WTD(m, no value or non numeric value means no water table present and lines below not needed)\n ITHETATYPE OR/OR  VGALPHA/BCALPHA VGN/BCLAMBDA VGM\n IKUNSATYPE VGM/BCETA/GDNALPHA         BCALPHA \n"
                archivo.write(f"{linea_uno}\n")
                archivo.write(f"{linea_dos}")
        else:
            #Inputs only for water table
            water_table_depth = float(self.dlg_infiltration_soil.line_water_depth.text())
            if self.dlg_infiltration_soil.radioButton_3.isChecked(): ITHETATYPE = 1
            elif self.dlg_infiltration_soil.radioButton_4.isChecked(): ITHETATYPE = 2
            if self.dlg_infiltration_soil.radioButton_5.isChecked(): IKUNSTYPE = 1
            elif self.dlg_infiltration_soil.radioButton_6.isChecked(): IKUNSTYPE = 2
            elif self.dlg_infiltration_soil.radioButton_7.isChecked(): IKUNSTYPE = 3
            RVH = self.dlg_infiltration_soil.line_input.text()
            
            with open(iso_file, 'w') as archivo:
                linea_uno = f"  {saturate_conductivity}   {suction_front}   {saturated_content}   {initial_content}   {maximum_storage}   {fraction_filter}"     
                linea_dos = f"   {water_table_depth}"
                if self.dlg_infiltration_soil.radioButton_3.isChecked():
                    linea_tres = f"  {ITHETATYPE}   {self.dlg_soil_curves.lineEdit.text()}   {self.dlg_soil_curves.lineEdit_2.text()}   {self.dlg_soil_curves.lineEdit_3.text()}   {self.dlg_soil_curves.lineEdit_4.text()}"
                else:
                    linea_tres = f"  {ITHETATYPE}   {self.dlg_soil_curves.lineEdit.text()}   {self.dlg_soil_curves.lineEdit_2.text()}   {self.dlg_soil_curves.lineEdit_3.text()}"
                if self.dlg_infiltration_soil.radioButton_5.isChecked() or self.dlg_infiltration_soil.radioButton_7.isChecked():
                    linea_cuatro = f"  {IKUNSTYPE}   {self.dlg_soil_curves.lineEdit_5.text()}"
                else:
                    linea_cuatro = f"  {IKUNSTYPE}   {self.dlg_soil_curves.lineEdit_5.text()}   {self.dlg_soil_curves.lineEdit_6.text()}"
                if self.dlg_infiltration_soil.check_input.isChecked():
                    linea_cinco = f" {RVH}"
                linea_seis = " \n     -------------------------------------\n Ks(m/s)   Sav(m)  Theta-s   Theta-i   Sm(m)   Schk(ponding ck)  WTD(Water Table Depth / No value means 'standard' iso file)\n WTD(m, no value or non numeric value means no water table present and lines below not needed)\n ITHETATYPE OR/OR  VGALPHA/BCALPHA VGN/BCLAMBDA VGM\n IKUNSATYPE VGM/BCETA/GDNALPHA         BCALPHA \n"
                archivo.write(f"{linea_uno}\n")
                archivo.write(f"{linea_dos}\n")
                archivo.write(f"{linea_tres}\n")
                archivo.write(f"{linea_cuatro}\n")
                if self.dlg_infiltration_soil.check_input.isChecked():
                    archivo.write(f"{linea_cinco}\n")
                archivo.write(f"{linea_seis}")
        
        #Close dialog
        if close:
            self.dlg_infiltration_soil.close()
        
    def create_igr_file(self,close = False):
        """Method to create the .igr file"""
        #Inputs
        spacing = float(self.dlg_buffer_properties.spacing_grass.text())
        roughness_grass = float(self.dlg_buffer_properties.roughness_grass.text())
        height_grass = float(self.dlg_buffer_properties.height_grass.text())
        roughness_bare = float(self.dlg_buffer_properties.roughness_bare.text())
        feedback = float(self.dlg_buffer_properties.feedback.text())
        #We create the file
        igr_file =self.obtain_direction_vfsmod(self.dlg_base.line_buffer.text())
        with open(igr_file, 'w') as archivo:
            linea_uno = f" {spacing}   {roughness_grass}   {height_grass}   {roughness_bare}   {feedback}"
            linea_dos = "--------------------------------------------\n SS(cm)  Vn(s/cm^1/3)  H(cm)  Vn2(s/m^1/3)  ICO(0 or 1)"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            
        #Update value in design
        self.add_vfs_length_spacing()
        
        #Close dialog
        if close:
            self.dlg_buffer_properties.close()
        
    def create_iwq_file(self, close =False):
        """Mehtod to crete the .iwq file"""
        #Inputs
        if self.dlg_water_quality.check_direct.isChecked(): direct_input = 0
        else: direct_input = 1
        IWQPRO = self.dlg_water_quality.trapping_equation.currentIndex()+1
        a = self.dlg_water_quality.equation_a.text()
        b = self.dlg_water_quality.equation_b.text()
        c = self.dlg_water_quality.equation_c.text()
        d = self.dlg_water_quality.equation_d.text()
        e = self.dlg_water_quality.equation_e.text()
        vkoc = self.dlg_water_quality.line_koc.text()
        vkd = self.dlg_water_quality.line_kd.text()
        oc = self.dlg_water_quality.line_oc.text()
        clay = self.dlg_water_quality.line_clay.text()
        days = self.dlg_water_quality.days.text()
        half_life = self.dlg_water_quality.half_life.text()
        field_capacity = self.dlg_water_quality.field_capacity.text()
        mass = self.dlg_water_quality.mass.text()
        thickness = self.dlg_water_quality.thickness.text()
        dgld = self.dlg_water_quality.dispersion.text()
        dgmres0 = self.dlg_water_quality.remobilised.text()
        idg = int(self.dlg_water_quality.calculation.currentIndex())
        imob = self.dlg_water_quality.imob.text()
        
        #Create file
        iwq_file =self.obtain_direction_vfsmod(self.dlg_base.line_water.text())
        with open(iwq_file, 'w') as archivo:
            linea_uno = f"{IWQPRO} {a} {b} {c} {d} {e} ;IWQPRO CSAB(I)"
            if direct_input == 1:
                linea_dos = f"{direct_input}	{vkoc}	{oc}	; Kd proc.:0= Kd(L/Kg); 1=Koc (Koc L/Kg),%OC)"
            else:
                linea_dos = f"{direct_input}	{vkd}; Kd proc.:0= Kd(L/Kg); 1=Koc (Koc L/Kg),%OC)"
            linea_tres = f"{clay}			; %Clay content (in sediment?)"
            linea_cuatro = f"{idg} IDG"
            linea_cinco = f"{days} {half_life} {field_capacity} {mass} {thickness} {dgld} {dgmres0}     ; ndgday dgHalf FC dgPin dgML dgLD dgmres0"
            linea_seis = ""
            rows = self.dlg_water_quality.tableWidget.rowCount()
            for row in range(rows):
                item = self.dlg_water_quality.tableWidget.item(row, 1)
                value = item.text()
                linea_seis += f"{value} "
            linea_seis += "(dgT(i),i=1,ndgday) (Celsius)"
            
            linea_siete = ""
            for row in range(rows):
                item = self.dlg_water_quality.tableWidget.item(row, 2)
                value = item.text()
                linea_siete += f"{value} "
            linea_siete += "(dgTheta(i),i=1,ndgday (-)"
            linea_ocho = f"{imob}                                       ; IMOB"
            
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            archivo.write(f"{linea_tres}\n")
            
            if idg !=0:
                archivo.write(f"{linea_cuatro}\n")
                archivo.write(f"{linea_cinco}\n")
                archivo.write(f"{linea_seis}\n")
                archivo.write(f"{linea_siete}\n")
                archivo.write(f"{linea_ocho}\n")
        
        #Update ikw file to run pesticide module
        self.update_ikw_pesticide()
        
        #Close dialog
        if close:
            self.dlg_water_quality.close()
    
    def update_ikw_pesticide(self):
        """Method to update ikw when ikw file created"""
        ikw_file =self.obtain_direction_vfsmod(self.dlg_base.line_overland.text())
        if os.path.exists(ikw_file):
            #See if pesticide option is selected
            if self.dlg_base.water_quality.isChecked():execute_pesticide = 1
            else: execute_pesticide = 0
            with open(ikw_file, 'r') as file:
                lineas = file.readlines()
            row = 3+int(lineas[3])+1
            numbers_str = lineas[row]
            # Use regex to find all numbers in the string
            matches = re.findall(r'\S+', numbers_str)
            # Replace the specific number at the given index
            matches[0] = str(execute_pesticide)
            # Rebuild the string by replacing only the specific number
            lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
            with open(ikw_file, 'w') as archivo:
                for i in lineas:
                    archivo.write(i)
    
    def create_isd_file(self,close =False):
        """Method to create the .isd file"""
        #Inputs
        concentration = float(self.dlg_incoming_sediment.line_concentration.text())
        particle_class = int(self.dlg_incoming_sediment.line_class.text())
        size = float(self.dlg_incoming_sediment.line_size.text())
        porosity = float(self.dlg_incoming_sediment.line_porosity.text())
        portion = float(self.dlg_incoming_sediment.line_portion.text())
        density = float(self.dlg_incoming_sediment.line_sediment.text())
        #Create file
        isd_file =self.obtain_direction_vfsmod(self.dlg_base.line_incoming.text())
        with open(isd_file, 'w') as archivo:
            linea_uno = f"   {particle_class}   {portion}   {concentration}   {porosity}     Npart, Coarse, Ci(g/cm3), Por"
            linea_dos = f"   {size}   {density}           Dp(cm), SG(g/cm3)"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
        
        #Close dialog
        self.dlg_incoming_sediment.close()
    
    def create_irn_file(self,close=False):
        """Method to create the .irn file"""
        #Inputs
        maximum = self.dlg_vfsmod_hyetograph.maximum_rainfall.text()
        table = self.dlg_vfsmod_hyetograph.tableWidget
        rows = table.rowCount()
        hyetograph = pd.DataFrame(data = {"Time":[table.item(row, 0).text() for row in range(rows)],
            "Precipitation":[table.item(row, 1).text() for row in range(rows)]})
        #We calculate de number of intervals. If the first value is 0 then we dont take it
        number_steps = rows

        #Create file
        irn_file =self.obtain_direction_vfsmod(self.dlg_base.line_storm.text())
        with open(irn_file, 'w') as archivo:
            linea_uno = f"  {number_steps}   {maximum}                     NRAIN, RPEAK(m/s)"
            linea_dos = f"   {hyetograph.iloc[0,0]}    {hyetograph.iloc[0,1]}          time(s), rainfall rate (m/s)"
            linea_tres = ""
            for row in range(1,len(hyetograph)):
                linea_tres += f"   {hyetograph.iloc[row,0]}    {hyetograph.iloc[row,1]}\n"
            linea_cuatro = "------------------------------"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            archivo.write(f"{linea_tres}")
            archivo.write(f"{linea_cuatro}\n")
        
        if close:
            self.dlg_vfsmod_hyetograph.close()
    
    def create_iro_file(self,close = False):
        """Method to create the .iro file"""
        #Inputs
        width = self.dlg_vfsmod_hydrograph.width.text()
        length = self.dlg_vfsmod_hydrograph.length.text()
        peak = self.dlg_vfsmod_hydrograph.peak.text()
        table = self.dlg_vfsmod_hydrograph.tableWidget
        rows = table.rowCount()
        hydrograph = pd.DataFrame(data = {"Time":[table.item(row, 0).text() for row in range(rows)],
            "Discharge":[table.item(row, 1).text() for row in range(rows)]})
        #Create file
        iro_file =self.obtain_direction_vfsmod(self.dlg_base.line_source.text())
        with open(iro_file, 'w') as archivo:
            linea_uno = f"     {width}    {length}                     Swidth(m), Slength(m)"
            linea_dos = f"    {rows}   {peak}                   nbcroff, bcropeak (m3/s)"
            linea_tres = f"   {hydrograph.iloc[0,0]}   {hydrograph.iloc[0,1]}           time(s), ro(m3/s)\n"
            for row in range(1,len(hydrograph)):
                linea_tres += f"   {hydrograph.iloc[row,0]}   {hydrograph.iloc[row,1]}\n"
            linea_cuatro = "------------------------------"
            archivo.write(f"{linea_uno}\n")
            archivo.write(f"{linea_dos}\n")
            archivo.write(f"{linea_tres}")
            archivo.write(f"{linea_cuatro}\n")
        if close:
            self.dlg_vfsmod_hydrograph.close()
            
    def create_folders_in_directory(self):
        """Metod to create the required folders in the working directory"""
        #Function to create a folder
        def create_folder(name_folder): #function to create a folder
            parent_dir = self.project_file
            path_file = os.path.join(parent_dir, name_folder)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
        #First we save in a list all the folders that they exist
        lineEdits = [self.dlg_base.uh_file,self.dlg_base.uh_input,self.dlg_base.line_hydrograph,
            self.dlg_base.line_hyetograph,self.dlg_base.line_sedimentograph,self.dlg_base.line_output_1,self.dlg_base.line_output_2]
        for i in lineEdits:
            directory = os.path.dirname(i.text())
            if not os.path.exists(directory):
                create_folder(directory)
            
    def update_file_names(self):
        """Method to update file names when the name of the files is changed"""
        lineEdits_extension = {self.dlg_base.uh_file:"lis",self.dlg_base.uh_input:"inp",self.dlg_base.line_hydrograph:"iro",
            self.dlg_base.line_hyetograph:"irn",self.dlg_base.line_sedimentograph:"isd",self.dlg_base.line_output_1:"out",
            self.dlg_base.line_output_2:"hyt",self.dlg_base.line_overland:"ikw",self.dlg_base.line_infiltration:"iso",
            self.dlg_base.line_buffer:"igr",self.dlg_base.line_incoming:"isd",self.dlg_base.line_storm:"irn",
            self.dlg_base.line_source:"iro",self.dlg_base.line_water:"iwq",self.dlg_base.line_sediment:"og1",
            self.dlg_base.line_flow:"og2",self.dlg_base.line_hydrograph_2:"ohy",self.dlg_base.line_waterland:"osm",
            self.dlg_base.line_overall:"osp",self.dlg_base.line_quality:"owq",self.dlg_base.line_project_vfsmod:"prj"}

        for i in lineEdits_extension.keys():
            extension = os.path.normpath(i.text()).split(".")[-1]
            if extension == "": extension = lineEdits_extension[i]
            directory = os.path.dirname(i.text())
            if directory=="":
                i.setText(self.dlg_base.name_files.text() + "."+extension)
            else:
                i.setText(directory + "\\"+ self.dlg_base.name_files.text() + "."+extension)
    
    def default_values(self):
        """Method to set default values for input values"""
        self.dlg_base.working_directory_vfsmod.setText(r"C:/borrar")
        #self.dlg_base.name_files.setText("prueba")
        self.dlg_base.uh_file.setText(".lis")
        self.dlg_base.uh_input.setText("inputs\.inp")
        
        #File paths
        #UH
        self.dlg_base.line_hydrograph.setText("inputs\.iro")
        self.dlg_base.line_hyetograph.setText("inputs\.irn")
        self.dlg_base.line_sedimentograph.setText("inputs\.isd")
        self.dlg_base.line_output_1.setText("output\.out")
        self.dlg_base.line_output_2.setText("output\.hyt")
        #VFSMOD
        self.dlg_base.line_project_vfsmod.setText(".prj")
        self.dlg_base.line_overland.setText("inputs\.ikw")
        self.dlg_base.line_infiltration.setText("inputs\.iso")
        self.dlg_base.line_buffer.setText("inputs\.igr")
        self.dlg_base.line_incoming.setText("inputs\.isd")
        self.dlg_base.line_storm.setText("inputs\.irn")
        self.dlg_base.line_source.setText("inputs\.iro")
        self.dlg_base.line_water.setText("inputs\.iwq")
        self.dlg_base.line_sediment.setText("output\.og1")
        self.dlg_base.line_flow.setText("output\.og2")
        self.dlg_base.line_hydrograph_2.setText("output\.ohy")
        self.dlg_base.line_waterland.setText("output\.osm")
        self.dlg_base.line_overall.setText("output\.osp")
        self.dlg_base.line_quality.setText("output\.owq")
        
        self.dlg_base.rainfall.setText("25")
        self.dlg_base.storm_duration.setText("6")
        self.dlg_base.curve_number.setText("85")
        self.dlg_base.length_source.setText("100")
        self.dlg_base.slope_source.setText("0.02")
        self.dlg_base.area_source.setText("0.5")
        self.dlg_base.k_factor.setText("-1")
        self.dlg_base.organic_matter.setText("1")
        self.dlg_base.particle_diameter.setText("-1")
        self.dlg_base.crop_factor.setText("1")
        self.dlg_base.practice_factor.setText("1")
        
        #Values of overland flow inputs
        self.dlg_overland_flow.simulation_title.setText("Unit9, g8, u183-91    ")
        self.dlg_overland_flow.length.setText("8.655")
        self.dlg_overland_flow.width.setText("3.87")
        self.dlg_overland_flow.nodes.setText("57")
        self.dlg_overland_flow.time.setText("0.5")
        self.dlg_overland_flow.nodal.setText("3")
        self.dlg_overland_flow.petrov.setText("1")
        self.dlg_overland_flow.courant.setText("0.8")
        self.dlg_overland_flow.maximum.setText("350")
        self.dlg_overland_flow.output.setText("1")
        
        #Strom type
        self.dlg_base.storm_type.setCurrentIndex(2)
        
        #Values of the buffer segment table
        buffer_segment = pd.DataFrame(data ={"Distance":[0.6182,1.2364,1.8546,2.4729,3.0911,3.7093,4.3275,4.9457,5.5639,6.1821,6.8004,7.4186,8.0368,8.655],
            "Roughness":[0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4],
            "Slope":[0.052778,0.032639,0.071528,0.075,0.031944,0.019444,0.029885,0.028947,0.041667,0.134028,0.079167,0.074306,0.040972,0.062346]})
        self.original_buffer_segments = buffer_segment
        self.dlg_buffer_segment.tableWidget.setRowCount(len(buffer_segment))
        for fila in range(len(buffer_segment)):
            for columna in range(len(buffer_segment.columns)):
                item = QTableWidgetItem(str(buffer_segment.iloc[fila,columna]))
                self.dlg_buffer_segment.tableWidget.setItem(fila, columna, item)
                item.setTextAlignment(Qt.AlignCenter)
        
        #Calibration
        self.dlg_base.no_vertical.setChecked(True)
        self.dlg_base.no_average.setChecked(True)
        self.dlg_base.no_saturated.setChecked(True)
        self.dlg_base.no_initial.setChecked(True)
        self.dlg_base.no_maximum.setChecked(True)
        self.dlg_base.no_fraction.setChecked(True)
        self.dlg_base.no_width.setChecked(True)
        self.dlg_base.no_length.setChecked(True)
        self.dlg_base.no_manning.setChecked(True)
        self.dlg_base.no_slope.setChecked(True)
        self.dlg_base.no_spacing.setChecked(True)
        self.dlg_base.no_roughness.setChecked(True)
        self.dlg_base.no_height.setChecked(True)
        self.dlg_base.no_bare.setChecked(True)
        self.dlg_base.no_coarse.setChecked(True)
        self.dlg_base.no_incoming.setChecked(True)
        self.dlg_base.no_porosity.setChecked(True)
        self.dlg_base.no_class.setChecked(True)
        self.dlg_base.no_density.setChecked(True)

        
        
    def user_defined_storm_type(self):
        """Metod to add the user defined storm type data"""
        if self.dlg_base.storm_type.currentIndex()==4:
            self.dlg_user_storm.show()
        else:
            self.dlg_user_storm.close()
    
    def check_uh_output_exist(self):
        """Method to check if the UH output exists"""
        buttons_dic = {self.dlg_base.line_hydrograph:self.dlg_base.output_hydrograph,self.dlg_base.line_hyetograph:self.dlg_base.output_hyetograph,self.dlg_base.line_sedimentograph:self.dlg_base.output_sedimentograph,
            self.dlg_base.line_output_1:self.dlg_base.output_output1,self.dlg_base.line_output_2:self.dlg_base.output_output2}
        for i in buttons_dic.keys():
            if os.path.exists(self.obtain_direction_vfsmod(i.text())) and i.text()!="":
                buttons_dic[i].setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;  /* Verde */
                    border: none;
                    color: white;
                    padding: 7px 7px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 10px;
                    margin: 0px 0px;
                    cursor: pointer;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049; /* Verde oscuro al pasar el ratón */
                }
                """)
                #Enable button to show outputs
                buttons_dic[i].setEnabled(True)
            else:
                buttons_dic[i].setStyleSheet("""
                QPushButton {
                    background-color: #808080;
                    border: none;
                    color: white;
                    padding: 7px 7px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 10px;
                    margin: 0px 0px;
                    cursor: pointer;
                    border-radius: 12px;
                }
                """)
                #Disable button to show outputs
                buttons_dic[i].setEnabled(False)
    
    def check_vfsmod_output_exist(self):
        """Method to check if the UH output exists"""
        buttons_dic = {self.dlg_base.line_sediment:self.dlg_base.output_sediment,self.dlg_base.line_flow:self.dlg_base.output_flow,
            self.dlg_base.line_hydrograph_2:self.dlg_base.output_hydrograph_2,self.dlg_base.line_waterland:self.dlg_base.output_waterland,self.dlg_base.line_overall:self.dlg_base.output_overall,
            self.dlg_base.line_quality:self.dlg_base.output_quality}
        for i in buttons_dic.keys():
            if os.path.exists(self.obtain_direction_vfsmod(i.text())) and i.text()!="":
                buttons_dic[i].setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;  /* Verde */
                    border: none;
                    color: white;
                    padding: 7px 7px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 10px;
                    margin: 0px 0px;
                    cursor: pointer;
                    border-radius: 12px;
                }
                QPushButton:hover {
                    background-color: #45a049; /* Verde oscuro al pasar el ratón */
                }
                """)
                #Enable button to show outputs
                buttons_dic[i].setEnabled(True)
            else:
                buttons_dic[i].setStyleSheet("""
                QPushButton {
                    background-color: #808080;
                    border: none;
                    color: white;
                    padding: 7px 7px;
                    text-align: center;
                    text-decoration: none;
                    font-size: 10px;
                    margin: 0px 0px;
                    cursor: pointer;
                    border-radius: 12px;
                }
                """)
                #Disable button to show outputs
                buttons_dic[i].setEnabled(False)
                
    def add_images(self):
        """Method to add images to the interface"""
        #Function to add images
        def add_image_button(path, button):
            icon_path_document = os.path.join(self.plugin_directory, path)
            button.setIcon(QIcon(icon_path_document))
        #Browse
        search_path = "images/search.svg"
        #Add remove rows
        add_image_button("images/add.svg",self.dlg_buffer_segment.add_row)
        add_image_button("images/remove.svg",self.dlg_buffer_segment.remove_row)
        add_image_button("images/add.svg",self.dlg_vfsmod_hyetograph.add)
        add_image_button("images/remove.svg",self.dlg_vfsmod_hyetograph.remove)
        add_image_button("images/add.svg",self.dlg_vfsmod_hydrograph.add)
        add_image_button("images/remove.svg",self.dlg_vfsmod_hydrograph.remove)
        
        
    def add_functions_outputs_hydrograph(self,dialog):
        """When creating the dialog fot hydrograph output for the outputs we add all the functionalities for them"""
        #Copy hydrograph to Clipboard
        self.dlg_output_hydrograph.copy.clicked.connect(self.copy_to_clipboard_hydrograph)
        #Print plot
        self.dlg_output_hydrograph.print.clicked.connect(self.save_hydrograph)
        
    def save_hydrograph(self):
        """Method to save the hydrograph in the local files"""
        opciones = QFileDialog.Options()
        archivo, _ = QFileDialog.getSaveFileName(None, "Save hydrograph", self.dlg_base.working_directory_vfsmod.text(), "PNG Files (*.png);;All Files (*)", options=opciones)
        if archivo:
            self.figure_hydrograph.savefig(archivo)
    
    
    def show_design_graph(self):
        """Method to show the results of the design"""
        if not hasattr(self, 'canvas_design_graph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_design_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_design_results_graph.frame)
            self.dlg_design_results_graph.frame.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_design_graph)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_design_graph.figure.clear()
        
        #Then we create the graph
        self.ax = self.canvas_design_graph.figure.subplots()
        self.line = None
        self.update_design_graph()
    
    def update_pesticide_coefficients(self):
        """Method to Sabbagh et al. (2009)  equation coefficients"""
        if self.dlg_water_quality.trapping_equation.currentIndex()==1:
            self.dlg_water_quality.frame_2.show()
        else:
            self.dlg_water_quality.frame_2.hide()
    
    def update_design_graph(self):
        """Method to update the graph of the design"""
        #Clear graph before drawing
        #Obtain data
        table = self.dlg_design_results.tableWidget
        rows = table.rowCount()
        columns = table.columnCount()
        # Obtain name of columns
        column_headers = []
        for column in range(columns):
            column_headers.append(table.horizontalHeaderItem(column).text())
        #Save data
        data = []
        for row in range(rows):
            row_data = []
            for column in range(columns):
                item = table.item(row, column)
                row_data.append(float(item.text()) if item is not None else None)
            data.append(row_data)

        # Convertir la lista a un DataFrame
        df = pd.DataFrame(data, columns=column_headers)
        #Create graph
        self.ax.clear()
        column_y = [self.dlg_design_results_graph.column.itemText(i) for i in range(self.dlg_design_results_graph.column.count())][self.dlg_design_results_graph.column.currentIndex()]
        column_x = df.columns[1]
        x = df[column_x]
        y = df[column_y]
        values_per_storm = len(df)/len(np.unique(df["Rainfall (mm)"]))
        list_range = list(range(0,len(df)+int(values_per_storm),int(values_per_storm)))
        for i in range(len(list_range)-1):
            self.ax.plot(x[list_range[i]:list_range[i+1]],y[list_range[i]:list_range[i+1]], linewidth=2, marker='o', markersize=4,label = f"{df['Rainfall (mm)'][list_range[i]]} mm")

        #Limits
        #self.ax.set_ylim([0, 1])
        #Labels
        self.ax.set_xlabel(column_x,size = 10,family="arial",weight = "bold",color = "black")
        self.ax.set_ylabel(column_y,size = 10,family="arial",weight = "bold",color = "black")
        #X ticks
        self.ax.tick_params(axis = "both",colors = "black",labelsize = 9)
        # Add legend
        self.ax.legend()
        
        #Remove previous line
        try:
            self.line.remove()
        except:
            pass
            
        #Add threshold
        value = self.dlg_design_results_graph.threshold.text()
        try:
            value = float(value)
            self.line = self.ax.axhline(y=value, color='r', linestyle='--', linewidth=2, zorder=1)
        except ValueError:
            value = 0
        
        #Add crossing point between threshold and lines and put it in a table
        self.dlg_design_results_graph.tableWidget.setRowCount(1)
        self.dlg_design_results_graph.tableWidget.setColumnCount(len(list_range)-1)
        self.dlg_design_results_graph.tableWidget.setHorizontalHeaderLabels([f"{df['Rainfall (mm)'][list_range[i]]} mm" for i in range(len(list_range)-1)])
        for i in range(len(list_range)-1):
            try:
                x_values = x[list_range[i]:list_range[i+1]]
                y_values = y[list_range[i]:list_range[i+1]]
                f = interp1d(y_values, x_values)
                x_interpolado = str(round(f(value).item(),2))
            except ValueError:
                if column_x == "VFS Length (m)":
                    if value>list(y_values)[0] and column_y!="Total Infiltration in Filter":
                        x_interpolado = str(list(x_values)[0])
                    elif value<list(y_values)[0] and column_y=="Total Infiltration in Filter":
                        x_interpolado = str(list(x_values)[0])
                    else:
                        x_interpolado = "x"
                elif column_x == "Vegetation Spacing (cm)":
                    if value>list(y_values)[0] and column_y!="Total Infiltration in Filter":
                        x_interpolado = str(list(x_values)[-1])
                    elif value<list(y_values)[0] and column_y=="Total Infiltration in Filter":
                        x_interpolado = str(list(x_values)[-1])
                    else:
                        x_interpolado = "x"
                        
            item = QTableWidgetItem(x_interpolado)
            self.dlg_design_results_graph.tableWidget.setItem(0, i, item)
            item.setTextAlignment(Qt.AlignCenter)
            
        #Change name of row
        if column_x == "VFS Length (m)":
            self.dlg_design_results_graph.tableWidget.setVerticalHeaderLabels(["VFS Length (m)"])
        elif column_x == "Vegetation Spacing (cm)":
            self.dlg_design_results_graph.tableWidget.setVerticalHeaderLabels(["Vegetation Spacing (cm)"])
        
       # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
        self.canvas_design_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
        #Draw canvas
        self.canvas_design_graph.draw()
        
    def show_hydrograph(self):
        """Method to show hydrograph results"""
        #First we clear the frame that is going to contain the graph
        self.dlg_output_hydrograph = output_hydrograph()
        self.add_functions_outputs_hydrograph(self.dlg_output_hydrograph)
        #We obtain the information of the .iro file
        with open(self.obtain_direction_vfsmod(self.dlg_base.line_hydrograph.text()), "r") as archivo:
            lineas = archivo.readlines()
        columna_1 = []
        columna_2 = []
        for linea in lineas:
            columnas = linea.split()
            if len(columnas) >= 2:
                columna_1.append(float(columnas[0]))
                columna_2.append(float(columnas[1]))

        time = columna_1[2:]
        discharge = columna_2[2:]
        
        #We change time from s to min 
        time = [x/60 for x in time]
        
        #This is to copy to clipboard 
        self.hydrograph_uh_1 = time
        self.hydrograph_uh_2 = discharge
        
        
        #We create the graph
        fig = plt.figure()
        plt.rcParams["figure.figsize"] = [12, 10]
        ax0 = plt.subplot()
        ax0.plot(time,discharge,color='blue', linewidth=2, marker='o', markersize=4)

        #Axis
        ax0.set_xlabel("Time (min)",size = 10,family="arial",weight = "bold",color = "black")
        ax0.set_ylabel("Discharge (m$^{3}$/s)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        ax0.tick_params(axis = "both",colors = "black",labelsize = 9)

        #Thousand separator
        #Separador de miles
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        ax0.xaxis.set_major_formatter(x_format)
        
        #Title
        plt.title("Hydrograph")
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        plt.subplots_adjust(bottom=0.15)
        plt.subplots_adjust(left=0.17)
        
        #Add the plot to the interface
        # Convertir el gráfico a un canvas Qt
        self.canvas = FigureCanvas(fig)

        # Crear un layout y añadir el canvas
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        # Añadir el layout al contenedor
        self.dlg_output_hydrograph.frame.setLayout(layout)
        
        #Put the option of seing the data by hovering the graph
        self.current_annotation_one = None
        self.current_annotation_two = None
        self.current_vline = None
        self.current_hline = None
        
        # Connect hover event
        def on_hover(event):
            if event.inaxes == ax0:
                # Remove the previous annotation if it exists
                if self.current_annotation_one is not None:
                    self.current_annotation_one.remove()
                    self.current_annotation_one = None
                if self.current_annotation_two is not None:
                    self.current_annotation_two.remove()
                    self.current_annotation_two = None
                # Find the closest point
                x = min(time, key=lambda x: abs(x - event.xdata))
                y = discharge[time.index(x)]
                # Remove the previous vertical and horizontal lines if they exist
                if self.current_vline is not None:
                    self.current_vline.remove()
                    self.current_vline = None
                if self.current_hline is not None:
                    self.current_hline.remove()
                    self.current_hline = None
                self.current_vline = ax0.axvline(x=x, color='red', linestyle='--', linewidth=1)
                self.current_hline = ax0.axhline(y=y, color='red', linestyle='--', linewidth=1)
                bbox_props = dict(boxstyle="round,pad=0.3", edgecolor="red", facecolor="white", lw=1)
                self.current_annotation_one = ax0.annotate(f"{y:.4f} m$^{3}$/s", 
                                                   xy=(ax0.get_xlim()[0], y),  # Position on the left edge of the plot
                                                   xytext=(-15, 0),
                                                   textcoords="offset points",
                                                   va='center', ha='right', color='red',bbox=bbox_props, fontsize = 8)

                self.current_annotation_two = ax0.annotate(f"{x:.2f} min", 
                                                   xy=(x, ax0.get_ylim()[0]),  # Position on the bottom edge of the plot
                                                   xytext=(0, -15),
                                                   textcoords="offset points",
                                                   va='top', ha='center', color='red',bbox=bbox_props, fontsize = 8)
                self.canvas.draw()
            else: #delete all lines and text if we are not hovering the graph
                if self.current_annotation_one is not None:
                    self.current_annotation_one.remove()
                    self.current_annotation_one = None
                if self.current_annotation_two is not None:
                    self.current_annotation_two.remove()
                    self.current_annotation_two = None
                if self.current_vline is not None:
                    self.current_vline.remove()
                    self.current_vline = None
                if self.current_hline is not None:
                    self.current_hline.remove()
                    self.current_hline = None
                self.canvas.draw()

        # Connect the hover event to the figure
        fig.canvas.mpl_connect("motion_notify_event", on_hover)
        
        #This is to save the plot
        self.figure_hydrograph = fig

        # Mostrar el diálogo o ventana
        self.dlg_output_hydrograph.show()
    
    def add_functions_outputs_hyetograph(self):
        """When creating the dialog fot hyetograph output for the outputs we add all the functionalities for them"""
        print("a")
        
    def show_hyetograph(self):
        """Method to show hydrograph results"""
        #First we clear the frame that is going to contain the graph
        self.dlg_output_hyetograph = hyetograph()
        self.add_functions_outputs_hyetograph()
        #We obtain the information of the .iro file
        with open(self.obtain_direction_vfsmod(self.dlg_base.line_hyetograph.text()), "r") as archivo:
            lineas = archivo.readlines()
        columna_1 = []
        columna_2 = []
        for linea in lineas:
            columnas = linea.split()
            if len(columnas) >= 2:
                columna_1.append(float(columnas[0]))
                columna_2.append(float(columnas[1]))

        time = columna_1[1:]
        precipitation = columna_2[1:]
        
        #We change time from s to min and precipitation to mm/h
        time = [x/60 for x in time]
        precipitation = [x*1000*3600 for x in precipitation]
        
        #This is to copy to clipboard 
        self.hydrograph_uh_1 = time
        self.hydrograph_uh_2 = precipitation
        
        
        #We create the graph
        fig = plt.figure()
        plt.rcParams["figure.figsize"] = [12, 10]
        ax0 = plt.subplot()
        
        widths = [time[i+1] - time[i] for i in range(len(time)-1)]
        ax0.bar(time[:-1],precipitation[:-1],width=widths,color='blue', align='edge', edgecolor='black', linewidth=0.5)

        #Axis
        ax0.set_xlabel("Time (min)",size = 10,family="arial",weight = "bold",color = "black")
        ax0.set_ylabel("Precipitation (mm/h)",size = 10,family="arial",weight = "bold",color = "black")

        #X ticks
        ax0.tick_params(axis = "both",colors = "black",labelsize = 9)

        #Thousand separator
        #Separador de miles
        def xfunc(x,pos):
            s = '{:0,d}'.format(int(x))
            return s
        x_format = tkr.FuncFormatter(xfunc)
        ax0.xaxis.set_major_formatter(x_format)
        
        #Title
        plt.title("Hyetograph")
        
        # Adjust bottom margin. If not then the graph is too big and I dont know how to change the graph size
        plt.subplots_adjust(bottom=0.15)
        plt.subplots_adjust(left=0.17)
        
        #Add the plot to the interface
        # Convertir el gráfico a un canvas Qt
        self.canvas = FigureCanvas(fig)

        # Crear un layout y añadir el canvas
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        # Añadir el layout al contenedor
        self.dlg_output_hyetograph.frame.setLayout(layout)
        
        #Put the option of seing the data by hovering the graph
        self.current_annotation_one = None
        self.current_annotation_two = None
        self.current_vline = None
        self.current_hline = None
        
        # Connect hover event
        def on_hover(event):
            if event.inaxes == ax0:
                # Remove the previous annotation if it exists
                if self.current_annotation_one is not None:
                    self.current_annotation_one.remove()
                    self.current_annotation_one = None
                if self.current_annotation_two is not None:
                    self.current_annotation_two.remove()
                    self.current_annotation_two = None
                # Find the closest point
                x = min(time, key=lambda x: abs(x - event.xdata))
                y = precipitation[time.index(x)]
                # Remove the previous vertical and horizontal lines if they exist
                if self.current_vline is not None:
                    self.current_vline.remove()
                    self.current_vline = None
                if self.current_hline is not None:
                    self.current_hline.remove()
                    self.current_hline = None
                self.current_vline = ax0.axvline(x=x, color='red', linestyle='--', linewidth=1)
                self.current_hline = ax0.axhline(y=y, color='red', linestyle='--', linewidth=1)
                bbox_props = dict(boxstyle="round,pad=0.3", edgecolor="red", facecolor="white", lw=1)
                self.current_annotation_one = ax0.annotate(f"{y:.4f} mm/h", 
                                                   xy=(ax0.get_xlim()[0], y),  # Position on the left edge of the plot
                                                   xytext=(-15, 0),
                                                   textcoords="offset points",
                                                   va='center', ha='right', color='red',bbox=bbox_props, fontsize = 8)

                self.current_annotation_two = ax0.annotate(f"{x:.2f} min", 
                                                   xy=(x, ax0.get_ylim()[0]),  # Position on the bottom edge of the plot
                                                   xytext=(0, -15),
                                                   textcoords="offset points",
                                                   va='top', ha='center', color='red',bbox=bbox_props, fontsize = 8)
                self.canvas.draw()
            else: #delete all lines and text if we are not hovering the graph
                if self.current_annotation_one is not None:
                    self.current_annotation_one.remove()
                    self.current_annotation_one = None
                if self.current_annotation_two is not None:
                    self.current_annotation_two.remove()
                    self.current_annotation_two = None
                if self.current_vline is not None:
                    self.current_vline.remove()
                    self.current_vline = None
                if self.current_hline is not None:
                    self.current_hline.remove()
                    self.current_hline = None
                self.canvas.draw()

        # Connect the hover event to the figure
        fig.canvas.mpl_connect("motion_notify_event", on_hover)
        
        #This is to save the plot
        self.figure_hyetograph = fig

        # Mostrar el diálogo o ventana
        self.dlg_output_hyetograph.show()



#PARALELIZATION OF DESIGN
def wrapper_design_paralelization(args):
    """Esta función envuelve la función original para manejar múltiples argumentos"""
    i, core_id, param_values,working_directory,length_checked,spacing_checked, vfs_file_design= args
    return design_paralelization(i, core_id, param_values,working_directory,length_checked,spacing_checked,vfs_file_design)

def design_paralelization(number_execution,core,combinations_design,working_directory,length_checked,spacing_checked,vfs_file_design):
    '''Function to run in paralell design analysis'''
    error = False
    #We change the values
    modify_inp_file_design(combinations_design[number_execution][0],core,working_directory)
    if length_checked:
        modify_ikw_file_design(vfs_file_design,working_directory,combinations_design[number_execution][1],core)
    if spacing_checked:
        modify_igr_file_design(combinations_design[number_execution][2],core,working_directory)
    
    #Execution
    resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_uh_{core}.bat"],
        capture_output=True, 
        text=True, 
        shell=True)
    #Put warning
    if not "...FINISHED..." in resultado.stdout:            
        error = True
        
    #Correct hietograph file
    correct_irn_file(working_directory+f"\\design\\inputs\\design_{core}.irn") 
    
    #VFS
    resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_vfs_{core}.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
    
    #Put warning
    if not "...FINISHED..." in resultado.stdout:
        error = True
    
    #Save outputs
    return save_outputs_design(working_directory,error,length_checked,spacing_checked,number_execution,combinations_design,core)
    


def modify_inp_file_design(new_value, core,working_directory):
    """Method to modfiy rainfall"""
    filepath = working_directory+fr"\design\inputs\design_{core}.inp"
    with open(filepath, 'r') as file:
        lineas = file.readlines()
    numbers_str = lineas[0]
    # Use regex to find all numbers in the string
    matches = re.findall(r'\S+', numbers_str)
    # Replace the specific number at the given index
    matches[0] = str(new_value)
    # Rebuild the string by replacing only the specific number
    lineas[0] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    with open(filepath, 'w') as archivo:
        for i in lineas:
            archivo.write(i)

def modify_igr_file_design(new_value, core,working_directory):
    """Method to modfiy inputs in design analysis"""
    filepath = working_directory+fr"\design\inputs\design_{core}.igr"
    with open(filepath, 'r') as file:
        lineas = file.readlines()
    numbers_str = lineas[0]
    # Use regex to find all numbers in the string
    matches = re.findall(r'\S+', numbers_str)
    # Replace the specific number at the given index
    matches[0] = str(new_value)
    # Rebuild the string by replacing only the specific number
    lineas[0] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    with open(filepath, 'w') as archivo:
        for i in lineas:
            archivo.write(i)



def modify_ikw_file_design(vfs_file_design,working_directory,value_change,core):
    """Metod to create the .ikw file for the design execution"""
    #First we save the .ikw file path
    ruta = vfs_file_design
    if os.path.exists(ruta) and os.path.isfile(ruta):
        ikw = working_directory+f"\\design\\inputs\\design_{core}.ikw"
        #We substitute value of length
        with open(ikw, "r") as archivo:
            lineas = archivo.readlines()
        def modify_number_in_string(numbers_str, index, new_value):
            # Use regex to find all numbers in the string
            matches = re.findall(r'\S+', numbers_str)
            # Replace the specific number at the given index
            matches[index] = str(new_value)
            # Rebuild the string by replacing only the specific number
            return re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        lineas[2] = modify_number_in_string(lineas[2],0,value_change)
        
        #Then we update the segments
        number_segments = int(lineas[3])
        length = list(map(float, lineas[2].split()))[0]
        new_interval = length/number_segments

        #Data frame, but we take it from the original, not from the last execution
        #We import dataframe of segments from the original file
        with open(ruta, "r") as archivo:
            lineas_prj = archivo.readlines()
        ikw = lineas_prj[0].split("=")[-1]
        if not os.path.isabs(ikw): #relative path
            ikw = os.path.join(os.path.dirname(ruta), ikw)
        ikw = ikw.replace("\n", "")
        with open(ikw, "r") as archivo:
            lineas_ikw_original = archivo.readlines()
            
        df = pd.DataFrame(data = {"Distance":[list(map(float, lineas_ikw_original[x].split()))[0] for x in range(4,4+number_segments)],
                             "Manning":[list(map(float, lineas_ikw_original[x].split()))[1] for x in range(4,4+number_segments)],
                             "Slope":[list(map(float, lineas_ikw_original[x].split()))[2] for x in range(4,4+number_segments)]})
        
        
        
       
        #We update the dataframe
        df_a = df.copy()
        actual_length = max(df["Distance"])
        length_to_change = value_change
        if length_to_change <= actual_length:
            df_a = df[df["Distance"]<=length_to_change]
            df_a.loc[df.index[-1], "Distance"] = length_to_change
        else:
            df_a.loc[df.index[-1], "Distance"] = length_to_change
        
        
        #Add to the file information 
        lineas[3] = modify_number_in_string(lineas[3],0,len(df_a)) #change number of segments
        
        
        
        #THIS PART OF THE EXECUTION APPARENTLY DOESNT DO NOTHING BUT IF I DELETE I HAVE ERROR IN THE LAS EXECUTION OF THE PARALELIZATION
        #We update the dataframe
        new_distances = np.linspace(new_interval, new_interval * number_segments, number_segments)
        def weighted_average(df, new_distances, new_interval, column):
            averages = []
            for dist in new_distances:
                start, end = dist - new_interval, dist
                
                # Calcular el solapamiento entre los intervalos originales y el nuevo intervalo
                overlap = np.minimum(df["Distance"], end) - np.maximum(df["Distance"].shift(fill_value=0), start)
                
                # Asegurarse de que el solapamiento sea positivo o al menos cero
                overlap = np.clip(overlap, 0, new_interval)
                
                # Calcular los pesos basados en el solapamiento
                weights = overlap / new_interval
                
                # Verificar si la suma de los pesos es mayor que cero para evitar NaN
                total_weight = np.sum(weights)
                if total_weight > 0:
                    avg = np.sum(weights * df[column]) / total_weight
                    averages.append(round(avg, 6))
                else:
                    # Si no hay pesos válidos, usar el valor del intervalo anterior o un valor predeterminado
                    averages.append(df[column].iloc[0])  # o cualquier otro valor predeterminado
            return averages

        new_df = pd.DataFrame({
            "Distance": new_distances,
            "Manning": weighted_average(df, new_distances, new_interval, "Manning"),
            "Slope": weighted_average(df, new_distances, new_interval, "Slope")
        })
        
        
        
        
        contenido = ""
        for i in lineas[:4]:    
            contenido+=f"{i}"
        for i in range(len(df_a)):
            contenido +=f" {df_a.iloc[i,0]}   {df_a.iloc[i,1]}   {df_a.iloc[i,2]}\n"
        for i in lineas[-8:]:    
            contenido+=f"{i}"

        with open(working_directory+f"\\design\\inputs\\design_{core}.ikw", 'w') as archivo:
            archivo.write(contenido)


def save_outputs_design(working_directory,error,length_checked,spacing_checked,number_execution,combinations_design,core):
    """Function to save outputs in the design process"""
    #Obtain the values
    if error:
        df_conc = pd.DataFrame(data = {"Total Runoff from source (mm)":[np.nan],
            "Total Runoff from Source (m3)":[np.nan],"Total Runoff out from Filter (mm)":[np.nan],
            "Total Runoff out from Filter (m3)":[np.nan],"Total Infiltration in Filter":[np.nan],
            "Mass Sediment Input to Filter":[np.nan],"Concentration Sediment in Runoff from source Area":[np.nan],
            "Mass Sediment Output from Filter":[np.nan],"Concentration Sediment in Runoff exiting the Filter":[np.nan],
            "Sediment Delivery Ratio":[np.nan],"Runoff Delivery Ratio":[np.nan]})
        
        if length_checked:
            df_conc.insert(0,"VFS Length (m)",[combinations_design[number_execution][1]])
        if spacing_checked:
            df_conc.insert(0,"Vegetation Spacing (cm)",[combinations_design[number_execution][2]])
        df_conc.insert(0,"Rainfall (mm)",[combinations_design[number_execution][0]])

    
    else:
        ruta = working_directory+f"\\design\\output\\design_{core}.osp"
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        #Function to obtain specific results form .osp file
        def obtain_result(string):
            try:
                for i in lineas:
                    if i.split("=")[-1]==string:
                        for k in i.split("=")[0].split(" "):
                            try:
                                output = float(k)
                                break
                            except:
                                pass
                return output
                
            except UnboundLocalError:
                return np.nan
        
        #Obtain results
        runoff_from_source_mm = obtain_result(" Total Runoff from Source (mm depth over Source Area)\n")
        runoff_from_source_m3 = obtain_result(" Total Runoff from Source\n")
        runoff_out_filter_mm = obtain_result(" Total Runoff out from Filter (mm depth over Source+Filter)\n")
        runoff_out_filter_m3 = obtain_result(" Total Runoff out from Filter\n")
        infiltration_filter = obtain_result(" Total Infiltration in Filter\n")
        mass_sediment_input_filter = obtain_result(" Mass Sediment Input to Filter\n")
        concentration_sediment_source = obtain_result(" Concentration Sediment in Runoff from source Area\n")
        sediment_out_filter = obtain_result(" Mass Sediment Output from Filter\n")
        concentration_sediment_filter = obtain_result(" Concentration Sediment in Runoff exiting the Filter\n")
        sdr = obtain_result(" Sediment Delivery Ratio\n")
        rdr = obtain_result(" Runoff Delivery Ratio\n")
        
        #Dataframe to concatenate results
        df_conc = pd.DataFrame(data = {"Total Runoff from source (mm)":[runoff_from_source_mm],
            "Total Runoff from Source (m3)":[runoff_from_source_m3],"Total Runoff out from Filter (mm)":[runoff_out_filter_mm],
            "Total Runoff out from Filter (m3)":[runoff_out_filter_m3],"Total Infiltration in Filter":[infiltration_filter],
            "Mass Sediment Input to Filter":[mass_sediment_input_filter],"Concentration Sediment in Runoff from source Area":[concentration_sediment_source],
            "Mass Sediment Output from Filter":[sediment_out_filter],"Concentration Sediment in Runoff exiting the Filter":[concentration_sediment_filter],
            "Sediment Delivery Ratio":[sdr],"Runoff Delivery Ratio":[rdr]})
        
        if length_checked:
            df_conc.insert(0,"VFS Length (m)",[combinations_design[number_execution][1]])
        if spacing_checked:
            df_conc.insert(0,"Vegetation Spacing (cm)",[combinations_design[number_execution][2]])
        df_conc.insert(0,"Rainfall (mm)",[combinations_design[number_execution][0]])
        
    return df_conc




#PARALELIZATION OF UNCERTAINITY
def wrapper_uncertainity_paralelization(args):
    """Esta función envuelve la función original para manejar múltiples argumentos"""
    i, core_id, param_values, dic_data, sensitivity_parameters, working_directory, vfs_uncertainity_file_file,water_quality = args
    return uncertainity_paralelization(i, core_id, param_values, dic_data, sensitivity_parameters, working_directory, vfs_uncertainity_file_file,water_quality)


def uncertainity_paralelization(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_uncertainity_file_file,water_quality):
    '''Function to run in paralell uncertainity analysis'''
    execution = execution_uncertainity_analysis(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_uncertainity_file_file)
    #Save results
    if execution == "error":
        return save_results_uncertainity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality ,error = True)
    else:
        return save_results_uncertainity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality ,error = False)

def execution_uncertainity_analysis(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_uncertainity_file):
    """Function for the each execution of the uncertainity analysis"""
    #We change the values of the inputs
    execute_uh = False
    for k,i in enumerate(dic_data.keys()):
        #Change inputs
        value_change = param_values[number_execution][k]
        #If buffer length, roughness or slope is selected then change in another way
        if i == "Buffer length (m)":
            information_parameter = sensitivity_parameters[i]
            modify_inputs_uncertainity(information_parameter[0],information_parameter[1],information_parameter[2],value_change,information_parameter[3],core,working_directory)
            change_buffer_length_uncertainity(value_change,core,vfs_uncertainity_file,working_directory)
        elif i == "Filter Manning n (RNA s/m^1/3)":
            change_filter_manning_uncertainity(value_change,1,core,working_directory)
        elif i == "Average Filter Slope":
            change_filter_manning_uncertainity(value_change,2,core,working_directory)
        else:
            information_parameter = sensitivity_parameters[i]
            modify_inputs_uncertainity(information_parameter[0],information_parameter[1],information_parameter[2],value_change,information_parameter[3],core,working_directory)
        #Check if there is the need to execute UH
        if information_parameter[3]=="uh":
            execute_uh = True
           
    #We execute
    #Only execute UH if there are parameters that need to be executed in UH
    if execute_uh:
        resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_uh_{core}.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        #Put warning
        if not "...FINISHED..." in resultado.stdout:            
            return "error"
            
        #Correct hietograph file
        correct_irn_file(working_directory+f"\\uncertainity\\inputs\\uncertainity_{core}.irn") 
    
    #VFS
    resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_vfs_{core}.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
    
    #Put warning
    if not "...FINISHED..." in resultado.stdout:
        return "error"


def modify_inputs_uncertainity(extension, row, column, new_value, process,core,working_directory):
    """Method to modfiy inputs in uncertainity analysis"""
    if process == "uh":
        ruta = os.path.normpath(working_directory+fr"\uncertainity\uncertainity_{core}.lis")
    else:
        ruta = os.path.normpath(working_directory+fr"\uncertainity\uncertainity_{core}.prj")
    with open(ruta, "r") as archivo:
        lineas_prj = archivo.readlines()
    for i in lineas_prj:
        if i.split(".")[-1].replace("\n", "").replace(" ","") == extension:
            filepath = i.split("=")[-1]
            break
    if not os.path.isabs(filepath): #relative path
        filepath = os.path.join(os.path.dirname(ruta), filepath)
    filepath = filepath.replace("\n", "")

    with open(filepath, 'r') as file:
        lineas = file.readlines()
    numbers_str = lineas[row]
    # Use regex to find all numbers in the string
    matches = re.findall(r'\S+', numbers_str)
    # Replace the specific number at the given index
    matches[column] = str(new_value)
    # Rebuild the string by replacing only the specific number
    lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    with open(filepath, 'w') as archivo:
        for i in lineas:
            archivo.write(i)


def change_buffer_length_uncertainity(value_change,core,vfs_uncertainity_file,working_directory):
    """Method to modifi length of buffer in uncertainity analysis"""
    #First we save the .ikw file path
    ruta = vfs_uncertainity_file
    ikw = working_directory+f"\\uncertainity\\inputs\\uncertainity_{core}.ikw"
    #We substitute value of length
    with open(ikw, "r") as archivo:
        lineas = archivo.readlines()
    
    def modify_number_in_string(numbers_str, index, new_value):
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        matches[index] = str(new_value)
        # Rebuild the string by replacing only the specific number
        return re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    lineas[2] = modify_number_in_string(lineas[2],0,value_change)
    
    #Then we update the segments
    number_segments = int(lineas[3])
    length = list(map(float, lineas[2].split()))[0]
    new_interval = length/number_segments

    #Data frame, but we take it from the original, not from the last execution
    #We import dataframe of segments from the original file
    with open(ruta, "r") as archivo:
        lineas_prj = archivo.readlines()
    ikw = lineas_prj[0].split("=")[-1]
    if not os.path.isabs(ikw): #relative path
        ikw = os.path.join(os.path.dirname(ruta), ikw)
    ikw = ikw.replace("\n", "")
    with open(ikw, "r") as archivo:
        lineas_ikw_original = archivo.readlines()
        
    df = pd.DataFrame(data = {"Distance":[list(map(float, lineas_ikw_original[x].split()))[0] for x in range(4,4+number_segments)],
                         "Manning":[list(map(float, lineas_ikw_original[x].split()))[1] for x in range(4,4+number_segments)],
                         "Slope":[list(map(float, lineas_ikw_original[x].split()))[2] for x in range(4,4+number_segments)]})
    
    #We update the dataframe
    df_a = df.copy()
    actual_length = max(df["Distance"])
    length_to_change = value_change
    if length_to_change <= actual_length:
        df_a = df[df["Distance"]<=length_to_change]
        df_a.loc[df.index[-1], "Distance"] = length_to_change
    else:
        df_a.loc[df.index[-1], "Distance"] = length_to_change
    
    
    #Add to the file information 
    lineas[3] = modify_number_in_string(lineas[3],0,len(df_a)) #change number of segments
    
    
    
    #THIS PART OF THE EXECUTION APPARENTLY DOESNT DO NOTHING BUT IF I DELETE I HAVE ERROR IN THE LAS EXECUTION OF THE PARALELIZATION
    #We update the dataframe
    new_distances = np.linspace(new_interval, new_interval * number_segments, number_segments)
    def weighted_average(df, new_distances, new_interval, column):
        averages = []
        for dist in new_distances:
            start, end = dist - new_interval, dist
            
            # Calcular el solapamiento entre los intervalos originales y el nuevo intervalo
            overlap = np.minimum(df["Distance"], end) - np.maximum(df["Distance"].shift(fill_value=0), start)
            
            # Asegurarse de que el solapamiento sea positivo o al menos cero
            overlap = np.clip(overlap, 0, new_interval)
            
            # Calcular los pesos basados en el solapamiento
            weights = overlap / new_interval
            
            # Verificar si la suma de los pesos es mayor que cero para evitar NaN
            total_weight = np.sum(weights)
            if total_weight > 0:
                avg = np.sum(weights * df[column]) / total_weight
                averages.append(round(avg, 6))
            else:
                # Si no hay pesos válidos, usar el valor del intervalo anterior o un valor predeterminado
                averages.append(df[column].iloc[0])  # o cualquier otro valor predeterminado
        return averages

    new_df = pd.DataFrame({
        "Distance": new_distances,
        "Manning": weighted_average(df, new_distances, new_interval, "Manning"),
        "Slope": weighted_average(df, new_distances, new_interval, "Slope")
    })
    
    
    
    
    
    
    contenido = ""
    for i in lineas[:4]:    
        contenido+=f"{i}"
    for i in range(len(df_a)):
        contenido +=f" {df_a.iloc[i,0]}   {df_a.iloc[i,1]}   {df_a.iloc[i,2]}\n"
    for i in lineas[-8:]:    
        contenido+=f"{i}"
    with open(working_directory+f"\\uncertainity\\inputs\\uncertainity_{core}.ikw", 'w') as archivo:
        archivo.write(contenido)

def change_filter_manning_uncertainity(value_change,column,core,working_directory):
    """Method to change the manning and slope value of the buffer in uncertainity analysis"""
    #We obtain information of ikw file
    ikw = working_directory+f"\\uncertainity\\inputs\\uncertainity_{core}.ikw"
    
    with open(ikw, "r") as archivo:
        lineas = archivo.readlines()
    
    for row in range(4,len(lineas)):
        numbers_str = lineas[row]
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        if len(matches)==1:
            break
        matches[column] = str(value_change)
        # Rebuild the string by replacing only the specific number
        lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        
        with open(ikw, 'w') as archivo:
            for i in lineas:
                archivo.write(i)


def save_results_uncertainity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality,error):
    """Method to save uncertainity results"""
    #Obtain the values
    if error:
        #Dataframe to concatenate to the uncertainity results
        df_conc = pd.DataFrame(data = {"Error":[1],"Total Runoff from source (mm)":[-1],
            "Total Runoff from Source (m3)":[-1],"Total Runoff out from Filter (mm)":[-1],
            "Total Runoff out from Filter (m3)":[-1],"Total Infiltration in Filter (m3)":[-1],
            "Mass Sediment Input to Filter (kg)":[-1],"Concentration Sediment in Runoff from source Area (g/L)":[-1],
            "Mass Sediment Output from Filter (kg)":[-1],"Concentration Sediment in Runoff exiting the Filter (g/L)":[-1],
            "Sediment Delivery Ratio":[-1],"Runoff Delivery Ratio":[-1]})
        #Add water quality parameters if present
        if water_quality:
            df_conc["Leachate depth (m)"]=-1.0
    else:
        ruta = working_directory+f"\\uncertainity\\output\\uncertainity_{core}.osp"
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
        #Function to obtain specific results form .osp file
        def obtain_result(string):
            try:
                for i in lineas:
                    if i.split("=")[-1]==string:
                        for k in i.split("=")[0].split(" "):
                            try:
                                output = float(k)
                                break
                            except:
                                pass
                return output
                
            except UnboundLocalError:
                return -1.0
        
        #Obtain results
        runoff_from_source_mm = obtain_result(" Total Runoff from Source (mm depth over Source Area)\n")
        runoff_from_source_m3 = obtain_result(" Total Runoff from Source\n")
        runoff_out_filter_mm = obtain_result(" Total Runoff out from Filter (mm depth over Source+Filter)\n")
        runoff_out_filter_m3 = obtain_result(" Total Runoff out from Filter\n")
        infiltration_filter = obtain_result(" Total Infiltration in Filter\n")
        mass_sediment_input_filter = obtain_result(" Mass Sediment Input to Filter\n")
        concentration_sediment_source = obtain_result(" Concentration Sediment in Runoff from source Area\n")
        sediment_out_filter = obtain_result(" Mass Sediment Output from Filter\n")
        concentration_sediment_filter = obtain_result(" Concentration Sediment in Runoff exiting the Filter\n")
        sdr = obtain_result(" Sediment Delivery Ratio\n")
        rdr = obtain_result(" Runoff Delivery Ratio\n")
        
        #Obtain results ohy
        ruta = working_directory+f"\\uncertainity\\output\\uncertainity_{core}.ohy"
        with open(ruta, "r") as archivo:
            lineas_ohy = archivo.readlines()
        water_front_depth =float(lineas_ohy[-1].split()[-2])
        
        #Dataframe to concatenate results
        df_conc = pd.DataFrame(data = {"Error":[0],"Total Runoff from source (mm)":[runoff_from_source_mm],
            "Total Runoff from Source (m3)":[runoff_from_source_m3],"Total Runoff out from Filter (mm)":[runoff_out_filter_mm],
            "Total Runoff out from Filter (m3)":[runoff_out_filter_m3],"Total Infiltration in Filter (m3)":[infiltration_filter],
            "Mass Sediment Input to Filter (kg)":[mass_sediment_input_filter],"Concentration Sediment in Runoff from source Area (g/L)":[concentration_sediment_source],
            "Mass Sediment Output from Filter (kg)":[sediment_out_filter],"Concentration Sediment in Runoff exiting the Filter (g/L)":[concentration_sediment_filter],
            "Sediment Delivery Ratio":[sdr],"Runoff Delivery Ratio":[rdr],"Water Front Depth (m)":[water_front_depth]})
        #Add water quality parameters if present
        if water_quality:
            #Obtain results water quality
            with open(working_directory+f"\\uncertainity\\output\\uncertainity_{core}.owq", "r") as archivo:
                lineas_owq = archivo.readlines()
            valores = []
            for i in range(len(lineas_owq)):
                if lineas_owq[i] == "      Z(m)      C(mg/L)      S(mg/mg)\n":
                    for k in range(i+2,len(lineas_owq)):
                        if len(lineas_owq[k].split())==0 or (float(lineas_owq[k].split()[1])==float(0)) and (float(lineas_owq[k].split()[2])==float(0)):
                            profundidad_lixiviado = float(lineas_owq[k].split()[0])
                            break
            df_conc["Leachate depth (m)"]=profundidad_lixiviado
    
    #Add the values of inputs 
    for k,i in enumerate(dic_data.keys()):
        df_conc.insert(0,i,[param_values[number_execution][k]])
        
    return df_conc
    


#PARALELIZATION OF SENSITIVITY
def wrapper_sensitivity_paralelization(args):
    """Esta función envuelve la función original para manejar múltiples argumentos"""
    i, core_id, param_values, dic_data, sensitivity_parameters, working_directory, vfs_sensitivity_file,water_quality = args
    return sensitivity_paralelization(i, core_id, param_values, dic_data, sensitivity_parameters, working_directory, vfs_sensitivity_file,water_quality)


def sensitivity_paralelization(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_sensitivity_file,water_quality):
    '''Function to run in paralell sensitivity analysis'''
    execution = execution_sensitivity_analysis(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_sensitivity_file)
    #Save results
    if execution == "error":
        return save_results_sensitivity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality ,error = True)
    else:
        return save_results_sensitivity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality ,error = False)


def execution_sensitivity_analysis(number_execution,core,param_values,dic_data,sensitivity_parameters,working_directory,vfs_sensitivity_file):
    """Function for the each execution of the sensitivity analysis"""
    #We change the values of the inputs
    execute_uh = False
    for k,i in enumerate(dic_data.keys()):
        #Change inputs
        value_change = param_values[number_execution][k]
        #If buffer length, rougheness or slope is selected then change in another way
        if i == "Buffer length (m)":
            information_parameter = sensitivity_parameters[i]
            modify_inputs_sensitivity(information_parameter[0],information_parameter[1],information_parameter[2],value_change,information_parameter[3],core,working_directory)
            change_buffer_length_sensitivity(value_change,core,vfs_sensitivity_file,working_directory)
        elif i == "Filter Manning n (RNA s/m^1/3)":
            change_filter_manning_sensitivity(value_change,1,core,working_directory)
        elif i == "Average Filter Slope":
            change_filter_manning_sensitivity(value_change,2,core,working_directory)
        else:
            information_parameter = sensitivity_parameters[i]
            modify_inputs_sensitivity(information_parameter[0],information_parameter[1],information_parameter[2],value_change,information_parameter[3],core,working_directory)
        #Check if there is the need to execute UH
        if information_parameter[3]=="uh":
            execute_uh = True
           
    
    #We execute
    #Only execute UH if there are parameters that need to be executed in UH
    if execute_uh:
        resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_uh_{core}.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
        #Put warning
        if not "...FINISHED..." in resultado.stdout:            
            return "error"
    
    
        #Correct hietograph file
        correct_irn_file(working_directory+f"\\sensitivity\\inputs\\sensitivity_{core}.irn") 
    
    #VFS
    resultado = subprocess.run([os.path.dirname(__file__)+f"\\executables\\execution_vfs_{core}.bat"],
            capture_output=True, 
            text=True, 
            shell=True)
    
    #Put warning
    if not "...FINISHED..." in resultado.stdout:
        return "error"

def modify_inputs_sensitivity(extension, row, column, new_value, process,core,working_directory):
    """Function to modfiy inputs in sensitivity analysis"""
    if process == "uh":
        ruta = os.path.normpath(working_directory+f"\sensitivity\sensitivity_{core}.lis")
    else:
        ruta = os.path.normpath(working_directory+f"\sensitivity\sensitivity_{core}.prj")
    with open(ruta, "r") as archivo:
        lineas_prj = archivo.readlines()
    for i in lineas_prj:
        if i.split(".")[-1].replace("\n", "").replace(" ","") == extension:
            filepath = i.split("=")[-1]
            break
    if not os.path.isabs(filepath): #relative path
        filepath = os.path.join(os.path.dirname(ruta), filepath)
    filepath = filepath.replace("\n", "")

    with open(filepath, 'r') as file:
        lineas = file.readlines()
    numbers_str = lineas[row]
    # Use regex to find all numbers in the string
    matches = re.findall(r'\S+', numbers_str)
    # Replace the specific number at the given index
    matches[column] = str(new_value)
    # Rebuild the string by replacing only the specific number
    lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    with open(filepath, 'w') as archivo:
        for i in lineas:
            archivo.write(i)

    
def change_buffer_length_sensitivity(value_change,core,vfs_sensitivity_file,working_directory):
    """Function to modifi length of buffer in sensitivity analysis"""
    #First we save the .ikw file path
    ruta = vfs_sensitivity_file
    ikw = working_directory+f"\\sensitivity\\inputs\\sensitivity_{core}.ikw"
    #We substitute value of length
    with open(ikw, "r") as archivo:
        lineas = archivo.readlines()
    
    def modify_number_in_string(numbers_str, index, new_value):
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        matches[index] = str(new_value)
        # Rebuild the string by replacing only the specific number
        return re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
    lineas[2] = modify_number_in_string(lineas[2],0,value_change)
    
    #Then we update the segments
    number_segments = int(lineas[3])
    length = list(map(float, lineas[2].split()))[0]
    new_interval = length/number_segments

    #Data frame, but we take it from the original, not from the last execution
    #We import dataframe of segments from the original file
    with open(ruta, "r") as archivo:
        lineas_prj = archivo.readlines()
    ikw = lineas_prj[0].split("=")[-1]
    if not os.path.isabs(ikw): #relative path
        ikw = os.path.join(os.path.dirname(ruta), ikw)
    ikw = ikw.replace("\n", "")
    with open(ikw, "r") as archivo:
        lineas_ikw_original = archivo.readlines()
        
    df = pd.DataFrame(data = {"Distance":[list(map(float, lineas_ikw_original[x].split()))[0] for x in range(4,4+number_segments)],
                         "Manning":[list(map(float, lineas_ikw_original[x].split()))[1] for x in range(4,4+number_segments)],
                         "Slope":[list(map(float, lineas_ikw_original[x].split()))[2] for x in range(4,4+number_segments)]})
    
    #We update the dataframe
    df_a = df.copy()
    actual_length = max(df["Distance"])
    length_to_change = value_change
    if length_to_change <= actual_length:
        df_a = df[df["Distance"]<=length_to_change]
        df_a.loc[df.index[-1], "Distance"] = length_to_change
    else:
        df_a.loc[df.index[-1], "Distance"] = length_to_change
    
    
    #Add to the file information 
    lineas[3] = modify_number_in_string(lineas[3],0,len(df_a)) #change number of segments
    
    
    
    #THIS PART OF THE EXECUTION APPARENTLY DOESNT DO NOTHING BUT IF I DELETE I HAVE ERROR IN THE LAS EXECUTION OF THE PARALELIZATION
    #We update the dataframe
    new_distances = np.linspace(new_interval, new_interval * number_segments, number_segments)
    def weighted_average(df, new_distances, new_interval, column):
        averages = []
        for dist in new_distances:
            start, end = dist - new_interval, dist
            
            # Calcular el solapamiento entre los intervalos originales y el nuevo intervalo
            overlap = np.minimum(df["Distance"], end) - np.maximum(df["Distance"].shift(fill_value=0), start)
            
            # Asegurarse de que el solapamiento sea positivo o al menos cero
            overlap = np.clip(overlap, 0, new_interval)
            
            # Calcular los pesos basados en el solapamiento
            weights = overlap / new_interval
            
            # Verificar si la suma de los pesos es mayor que cero para evitar NaN
            total_weight = np.sum(weights)
            if total_weight > 0:
                avg = np.sum(weights * df[column]) / total_weight
                averages.append(round(avg, 6))
            else:
                # Si no hay pesos válidos, usar el valor del intervalo anterior o un valor predeterminado
                averages.append(df[column].iloc[0])  # o cualquier otro valor predeterminado
        return averages

    new_df = pd.DataFrame({
        "Distance": new_distances,
        "Manning": weighted_average(df, new_distances, new_interval, "Manning"),
        "Slope": weighted_average(df, new_distances, new_interval, "Slope")
    })
    
    
    
    
    
    
    contenido = ""
    for i in lineas[:4]:    
        contenido+=f"{i}"
    for i in range(len(df_a)):
        contenido +=f" {df_a.iloc[i,0]}   {df_a.iloc[i,1]}   {df_a.iloc[i,2]}\n"
    for i in lineas[-8:]:    
        contenido+=f"{i}"
    with open(working_directory+f"\\sensitivity\\inputs\\sensitivity_{core}.ikw", 'w') as archivo:
        archivo.write(contenido)
    
def change_filter_manning_sensitivity(value_change,column,core,working_directory):
    """Function to change the manning and slope value of the buffer in sensitivity analysis"""
    #We obtain information of ikw file
    ikw = working_directory+f"\\sensitivity\\inputs\\sensitivity_{core}.ikw"
    
    with open(ikw, "r") as archivo:
        lineas = archivo.readlines()
    
    for row in range(4,len(lineas)):
        numbers_str = lineas[row]
        # Use regex to find all numbers in the string
        matches = re.findall(r'\S+', numbers_str)
        # Replace the specific number at the given index
        if len(matches)==1:
            break
        matches[column] = str(value_change)
        # Rebuild the string by replacing only the specific number
        lineas[row] = re.sub(r'\S+', lambda m, it=iter(matches): next(it), numbers_str, count=len(matches))
        
        with open(ikw, 'w') as archivo:
            for i in lineas:
                archivo.write(i)


def correct_irn_file(path):
    """Function to correct the .irn file (the number of steps)"""
    #Open file
    with open(path, "r") as archivo:
        lineas = archivo.readlines()
    #Calculate the number of steps in hietograph
    number_steps = 0
    for i in lineas:
        try:
            float(i.strip().split(" ")[0]) #first number of the line
            number_steps += 1
        except:
            pass
    number_steps -=1
    #Add to the text
    splits = lineas[0].split(" ")
    for k,i in enumerate(splits):
        try:
            float(i)
            splits[k] = str(number_steps)
            break
        except:
            pass
    lineas[0] = " ".join(splits)
    #Save the file
    contenido = ""
    for i in lineas:    
        contenido+=f"{i}"
    with open(path, 'w') as archivo:
        archivo.write(contenido)


def save_results_sensitivity_analysis(number_execution,core,working_directory,dic_data,param_values,water_quality,error):
    """Function to save sensitivity results"""
    #Obtain the values
    if error:
        #Dataframe to concatenate to the sensitivity results
        df_conc = pd.DataFrame(data = {"Error":[1],"Total Runoff from source (mm)":[-1.0],
            "Total Runoff from Source (m3)":[-1.0],"Total Runoff out from Filter (mm)":[-1.0],
            "Total Runoff out from Filter (m3)":[-1.0],"Total Infiltration in Filter (m3)":[-1.0],
            "Mass Sediment Input to Filter (kg)":[-1.0],"Concentration Sediment in Runoff from source Area (g/L)":[-1.0],
            "Mass Sediment Output from Filter (kg)":[-1.0],"Concentration Sediment in Runoff exiting the Filter (g/L)":[-1.0],
            "Sediment Delivery Ratio":[-1.0],"Runoff Delivery Ratio":[-1.0],"Water Front Depth (m)":[-1.0]})
        #Add water quality parameters if present
        if water_quality:
            df_conc["Leachate depth (m)"]=-1.0

    else:
        ruta = working_directory+f"\\sensitivity\\output\\sensitivity_{core}.osp"
        with open(ruta, "r") as archivo:
            lineas = archivo.readlines()
            
        #Function to obtain specific results form .osp file
        def obtain_result(string):
            try:
                for i in lineas:
                    if i.split("=")[-1]==string:
                        for k in i.split("=")[0].split(" "):
                            try:
                                output = float(k)
                                break
                            except:
                                pass
                return output
                
            except UnboundLocalError:
                return -1.0
                
        
        #Obtain results osp
        runoff_from_source_mm = obtain_result(" Total Runoff from Source (mm depth over Source Area)\n")  
        runoff_from_source_m3 = obtain_result(" Total Runoff from Source\n")
        runoff_out_filter_mm = obtain_result(" Total Runoff out from Filter (mm depth over Source+Filter)\n")
        runoff_out_filter_m3 = obtain_result(" Total Runoff out from Filter\n")
        infiltration_filter = obtain_result(" Total Infiltration in Filter\n")
        mass_sediment_input_filter = obtain_result(" Mass Sediment Input to Filter\n")
        concentration_sediment_source = obtain_result(" Concentration Sediment in Runoff from source Area\n")
        sediment_out_filter = obtain_result(" Mass Sediment Output from Filter\n")
        concentration_sediment_filter = obtain_result(" Concentration Sediment in Runoff exiting the Filter\n")
        sdr = obtain_result(" Sediment Delivery Ratio\n")
        rdr = obtain_result(" Runoff Delivery Ratio\n")

            
        
        #Obtain results ohy
        ruta = working_directory+f"\\sensitivity\\output\\sensitivity_{core}.ohy"
        with open(ruta, "r") as archivo:
            lineas_ohy = archivo.readlines()
        water_front_depth =float(lineas_ohy[-1].split()[-2])
        

        
        #Dataframe to concatenate results
        df_conc = pd.DataFrame(data = {"Error":[0],"Total Runoff from source (mm)":[runoff_from_source_mm],
            "Total Runoff from Source (m3)":[runoff_from_source_m3],"Total Runoff out from Filter (mm)":[runoff_out_filter_mm],
            "Total Runoff out from Filter (m3)":[runoff_out_filter_m3],"Total Infiltration in Filter (m3)":[infiltration_filter],
            "Mass Sediment Input to Filter (kg)":[mass_sediment_input_filter],"Concentration Sediment in Runoff from source Area (g/L)":[concentration_sediment_source],
            "Mass Sediment Output from Filter (kg)":[sediment_out_filter],"Concentration Sediment in Runoff exiting the Filter (g/L)":[concentration_sediment_filter],
            "Sediment Delivery Ratio":[sdr],"Runoff Delivery Ratio":[rdr],"Water Front Depth (m)":[water_front_depth]})
        #Add water quality parameters if present
        if water_quality:
            #Obtain results water quality
            with open(working_directory+f"\\sensitivity\\output\\sensitivity_{core}.owq", "r") as archivo:
                lineas_owq = archivo.readlines()
            valores = []
            for i in range(len(lineas_owq)):
                if lineas_owq[i] == "      Z(m)      C(mg/L)      S(mg/mg)\n":
                    for k in range(i+2,len(lineas_owq)):
                        if len(lineas_owq[k].split())==0 or (float(lineas_owq[k].split()[1])==float(0)) and (float(lineas_owq[k].split()[2])==float(0)):
                            profundidad_lixiviado = float(lineas_owq[k].split()[0])
                            break
                        
            df_conc["Leachate depth (m)"]=profundidad_lixiviado
        
    #Add the values of inputs 
    for k,i in enumerate(dic_data.keys()):
        df_conc.insert(0,i,[param_values[number_execution][k]])
    
    return df_conc


class DesignAnalysisThread(QThread):
    """Class to run parallelization of design analysis with QThread so we can se the progress bar"""
    update_progress = pyqtSignal(list)
    def __init__(self, args_list):
        super().__init__()
        self.args_list = args_list
    def run(self):
        with Pool(processes=psutil.cpu_count(logical=False)) as pool:
            async_results = [
                pool.apply_async(
                    wrapper_design_paralelization,
                    args=(args,),
                    callback=lambda result, idx=i: self.callback(idx, result)  # Cambiado aquí
                ) for i, args in enumerate(self.args_list)
            ]
            pool.close()
            pool.join()  # Espera a que todos los procesos terminen
            
            # Captura y maneja las excepciones
            for i, async_result in enumerate(async_results):
                try:
                    async_result.get()  # Esto lanzará la excepción si ocurrió alguna
                except Exception as e:
                    print(f"Error en proceso {i}: {e}")
            
        

    def callback(self, execution_num,result):  # Cambiado para recibir solo execution_num
        self.update_progress.emit([execution_num,result])


class SensitivityAnalysisThread(QThread):
    """Class to run parallelization of sensitivity analysis with QThread so we can se the progress bar"""
    update_progress = pyqtSignal(list)
    def __init__(self, args_list):
        super().__init__()
        self.args_list = args_list
    def run(self):
        with Pool(processes=psutil.cpu_count(logical=False)) as pool:
            async_results = [
                pool.apply_async(
                    wrapper_sensitivity_paralelization,
                    args=(args,),
                    callback=lambda result, idx=i: self.callback(idx, result)  # Cambiado aquí
                ) for i, args in enumerate(self.args_list)
            ]
            pool.close()
            pool.join()  # Espera a que todos los procesos terminen
        
            # Captura y maneja las excepciones
            for i, async_result in enumerate(async_results):
                try:
                    async_result.get()  # Esto lanzará la excepción si ocurrió alguna
                except Exception as e:
                    print(f"Error en proceso {i}: {e}")
        

    def callback(self, execution_num,result):  # Cambiado para recibir solo execution_num
        self.update_progress.emit([execution_num,result])

class UncertainityAnalysisThread(QThread):
    """Class to run parallelization of uncertainity analysis with QThread so we can se the progress bar"""
    update_progress = pyqtSignal(list)
    def __init__(self, args_list):
        super().__init__()
        self.args_list = args_list
    def run(self):
        with Pool(processes=psutil.cpu_count(logical=False)) as pool:
            async_results = [
                pool.apply_async(
                    wrapper_uncertainity_paralelization,
                    args=(args,),
                    callback=lambda result, idx=i: self.callback(idx, result)  # Cambiado aquí
                ) for i, args in enumerate(self.args_list)
            ]
            pool.close()
            pool.join()  # Espera a que todos los procesos terminen
            
            # Captura y maneja las excepciones
            for i, async_result in enumerate(async_results):
                try:
                    async_result.get()  # Esto lanzará la excepción si ocurrió alguna
                except Exception as e:
                    print(f"Error en proceso {i}: {e}")
            
        

    def callback(self, execution_num,result):  # Cambiado para recibir solo execution_num
        self.update_progress.emit([execution_num,result])

if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    
    dialog = qvfsmod()
    dialog.run()
    sys.exit(app.exec_())
    
    
