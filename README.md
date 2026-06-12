# VFSMOD GUI

**Written by:** Iñigo Barberena Ruiz
**Email:** [inigo.barberena@unavarra.es](mailto:inigo.barberena@unavarra.es)

## Overview

VFSMOD GUI is a graphical user interface designed to facilitate the setup, execution and analysis of the results performed with the Vegetative Filter Strip Modeling System (VFSMOD).

VFSMOD is a physically-based model developed to simulate hydrological processes, sediment transport, and pollutant removal within vegetative filter strips (VFS). These systems are widely used as a best management practice to reduce runoff pollution from agricultural, forest, urban, and transportation areas.

The original VFSMOD model is distributed as a stand-alone Fortran application and has been integrated into several environmental risk assessment and management frameworks in both North America and Europe.


# VFSMOD GUI

**Written by:** Iñigo Barberena Ruiz
**Email:** [inigo.barberena@unavarra.es](mailto:inigo.barberena@unavarra.es)

## Overview

VFSMOD GUI is a cross-platform graphical user interface developed to simplify the setup, calibration, design, evaluation, and optimization of vegetative filter strips (VFS) using the Vegetative Filter Strip MODel (VFSMOD).

The software provides a user-friendly environment that extends the capabilities of the original VFSMOD model, allowing users to perform complete VFS design and assessment workflows without requiring command-line interaction. The GUI is written in Python and is designed to facilitate both research and practical applications related to agricultural and environmental management.

## About VFSMOD

VFSMOD is a physically-based model developed to simulate hydrological processes, sediment transport, and pollutant removal within vegetative filter strips. The model evaluates runoff routing, infiltration, sediment trapping, and contaminant reduction, providing a comprehensive framework for assessing the effectiveness of VFS as a best management practice for reducing non-point source pollution.

## Main Features

* User-friendly graphical interface for VFSMOD.
* Cross-platform implementation written entirely in Python.
* Simplified creation and management of VFSMOD input files.
* Integrated execution of VFSMOD simulations.
* Visualization and analysis of simulation results.
* Calibration tools for parameter estimation and model evaluation.
* Statistical hypothesis-testing framework to support model calibration.
* Design and evaluation of vegetative filter strips under uncertainty.
* Robust design workflow that explicitly accounts for uncertainty in system parameters.
* Comprehensive workflow covering calibration, design, and performance assessment within a single environment.

## Design Under Uncertainty

One of the main innovations of VFSMOD GUI is the incorporation of uncertainty into the filter strip design process. The software implements a workflow that combines model calibration with uncertainty-aware design, allowing users to obtain more robust and realistic estimates of VFS performance.

Rather than relying solely on a single calibrated parameter set, the framework considers parameter uncertainty during the design stage, improving confidence in the predicted pollutant mitigation performance of vegetative filter strips.

## Applications

VFSMOD GUI can be used for:

* Agricultural runoff management.
* Sediment control studies.
* Nutrient and pesticide mitigation assessment.
* Design of vegetative filter strips.
* Environmental risk assessment studies.
* Evaluation of best management practices (BMPs) for water quality protection.



Complete information about the VFSMOD model can be found at:

https://abe.ufl.edu/carpena/vfsmod/


## Installation

Installation packages for both Windows and macOS are available in the VFSMOD_GUI_Distributions folder.

Windows

Run:

vfsmod_gui_setup.exe

and follow the installation wizard. During the installation process, users will be asked to specify, among other settings, the directory where VFSMOD GUI projects and executable files will be stored.

macOS

Run:

vfsmod_gui.pkg

and follow the installation wizard. During the installation process, users will be asked to specify the directory where VFSMOD GUI projects will be stored.

Unlike the Windows version, the VFSMOD executable files are automatically installed in the system's Application Support directory:

~/Library/Application Support

## Full Documentation

A file named Documentation.docx is included in the installation directory. This document corresponds to a chapter of the doctoral thesis developed by Iñigo Barberena Ruiz and provides detailed information about the software, its methodology, and its capabilities.

Users are encouraged to consult this document for a comprehensive description of the workflow, calibration procedures, uncertainty analysis, and design tools available in VFSMOD GUI.


## Licensing
VFSMOD by (c) Iñigo Barberena Ruiz and Rafael Muñoz-Carpena is licensed under CC BY-ND 4.0

The model is provided to you as an educational, research, and general application tool under the terms of the Creative Commons license, CC BY-ND 4.0 (Creative Commons Attribution-NoDerivatives 4.0 International). This license requires that reusers give credit to the creator. It allows reusers to copy and distribute the material in any medium or format in unadapted form only, even for commercial purposes.