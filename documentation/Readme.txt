CONTENTS OF THIS FILE (VFSMOD-W V5.X.X)

1. Installation and Execution Information
2. How Can the Model be Used?
3. Current Issues/Hints/Problems and Workarounds
---------------------------------------------------------

1. Installation and Execution Information

This package consists of three programs to assist users in evaluating and developing 
design specifications for vegetative filter strips for trapping sediment and pesticides 
and enhancing infiltration. The programs are the graphical user interface (GUI – vfsmod-w.exe  
v5.x.x),a program to estimate rainfall hyetographs, runoff hydrographs and storm-based erosion 
losses from typical source areas (UH – uh.exe, version 2.4.6 or later), and the vegetative 
filter strip model (VFSMOD – vfsm.exe, version 2.4.6 or later).  The GUI was developed to 
assist users in executing the Vegetative Filter Strip Model, VFSMOD and UH. Development of 
the graphical user interface program (GUI) was started in March 2000. Since that time we 
have continued to improve the interface and add new features to the system. As such we expect 
there will be a number of bugs that may appear from time to time. The graphical front end, 
GUI, for VFSMOD was developed using Visual Basic .NET. The Visual Basic source code is 
not available but interested parties can submit requests for changes to the authors. The
programs UH and VFSMOD were developed in FORTRAN and the source code is supplied with the
installation package.

This program is supplied for installation via Windows Installer. Obtain the package form the 
VFSMOD download page and save the package in your temporary directory.  You will Administrator
privileges to install the package on machines with Windows NT or later, since the packages
copies a few files into the Windows system directories. Please notice that the new version
requires Microsoft  .NET to be installed in your machine if you are running Windows versions
 XP or earlier (instructions to install it are provided in the installer), and also the 
Matlab Run Time Environment if you currently don't have Matlab 7 or above installed in your
machine (the installation package provides a link to install this and it can also be downloaded
from VFSMOD download page).

The install package includes the complete Win32 distribution for vfsmod. The default installation
directory is: C:\vfsmod-w which you can change. For example, if 
the installation was done for C:\vfsmod-w, then this directory would contain:

C:\vfsmod-w

Vfsmod-w.exe			Graphical user interface
Vfsmod-w.hlp			Windows Help file
vfsmod-w.cfg			Program configuration file
Uh.exe				Utility program, uh
Vfsm.exe			Vegetative filter strip model, vfsmod
Sample2.lis			Sample project for uh
Sample.prj			Sample project for vfsmod
SampleP.prj			Sample project for vfsmod that includes a water quality (pesticides) component.

globalSensitivity.exe		Global sensitivity component
globalSensitivity.exe.config	Global sensitivity configuration
MSCOMCTL.OCX			GUI forms and dll files
comct332.ocx			GUI forms and dll files
comdlg32.oca			GUI forms and dll files
comdlg32.ocx			GUI forms and dll files
mschrt20.ocx			GUI forms and dll files
mscomct2.ocx			GUI forms and dll files
msde.dll			GUI forms and dll files
mshflxgd.ocx			GUI forms and dll files
msmask32.ocx			GUI forms and dll files
msvcrt40.dll			GUI forms and dll files
richtx32.ocx			GUI forms and dll files

Documentation\		Documentation directory
	vfsm-draft.pdf		User manual
	0Announce_v5.0.xx.txt
	0README-failed-simulations.txt
	0Readme.txt
	0disclaim.txt
	0r_notes_v5.0.xx.txt
	lic_v4.txt
Inputs\			Directory containing the inputs
	Sample.igr		Sample Overland flow inputs for vfsm
	Sample.ikw		Sample Buffer vegetation inputs for vfsm

	SampleP.ikw		Sample Buffer vegetation inputs for vfsm that includes a flag for the water quality (pesticides) component.
	Sample.irn		Sample Rainfall hyetograph for vfsm
	Sample.iro		Sample Runoff hydrograph for vfsm
	Sample.isd		Sample Incoming sediment characteristics for vfsm
	Sample.iso		Sample Infiltration soil properties for vfsm
	Sample.iwq		Sample water quality file for pesticide trapping
	Sample2.igr		Sample overland flow inputs created by uh
	Sample2.inp		Sample inputs for uh
	Sample2.iso		Sample infiltration soil properties created by uh
Output\			Directory containing the outputs from uh and vfsm
Patterns\		Directory  with the substitution rules for the global sensitivity analysis.
	pattern.igr		These are the labeled files with the substitutions
	pattern.ikw		"
	pattern.inp		"
	pattern.irn		"
	pattern.iro		"
	pattern.isd		"
	pattern.iso		"

SourceCode\
	INSTALL.txt		Text file with installation instructions
	disclaim.txt		Text file with program disclaimer
	setup.txt	 	Text file for compilation instructions
	Uh			FORTRAN source code for UH
	Vfsm			FORTRAN source code for VFSMOD
Inverse\		Directory for the automatic inverse simulation engine
	inputs\			Directory used internally by the inverse engine during execution
	output\			Directory used internally by the inverse engine during execution	
	inverse.cfg		Configuration file written by the GUI with inverse simulation options
	meas_gso.txt		Sample measured sedigraph for optimization
	meas_hyd.txt		Sample measured sedigraph for optimization
	start_inv.exe		Matlab simulation engine called by GUI
	start_inv.ctf		Libraries for Matlab simulation engine


And after your first execution of vfsmod-w, you will be prompted to filled the Options file (vfsmod-w.cfg). The Directory for Saving Project Files should be:

C:\vfsmod-w

As you encounter problems, you can e-mail us for help/assistance.  In most cases, you 
should send us copies of the files giving problems along with a detailed description so 
we can re-create the problem. A web-address to report problems and suggestions is 
under development. We will e-mail our registered users when this is available.  At 
present, e-mail your problems to carpena@ufl.edu 


2. How Can the Model be Used?

This package can be used to comprehensively evaluate and develop designs for 
vegetative filter strips to trap sediment and enhance infiltration. A typical 
application of the package would follow the outline below.

1.	Develop input datasets for UH to generate storm data for a typical 
upslope source area.
2.	Run UH to develop input hydrograph and hyetograph data for VFSMOD
3.	Develop input datasets for VFSMOD for describing the filter strip
4.	Run VFSMOD to simulate the performance
5.	Modify any of the inputs for UH and/or VFSMOD to better reflect 
target source area – filter strip.
6.	Use the Design Option to examine a range of storm events – filter 
strip combinations to evaluate alternate possible designs.

After Step 5 or 6, an alternate path could examine the uncertainty associated 
with the proposed design. Following this path, the user can use the Sensitivity 
and Uncertainty Options to investigate. The steps would be:

1.	Use the Sensitivity options to identify the most sensitive 
parameters for the design centered on the base input values for the 
target source area and filter strip.
2.	Select the most sensitive parameters and assign these probability distributions
3.	Use the Uncertainty section to perform Monte Carlo Simulations
4.	Using the Analysis portion of the Uncertainty Section, examine the 
probability distributions for the key outputs of interest and assign 
confidence intervals and other estimates on the final filter strip designs 
(note: the program supplies basic statistics and the actual simulated data 
to allow the users to use other outside analysis tools to complete this 
analysis – users are welcome to contact us for suggestions).



3. Current Issues/Hints/Problems and Workarounds

1.	Download installation files to your temp directory and unzip and/or execute into a 
subdirectory.  After setup is complete, you can delete the subdirectory. You can 
delete the zip file, but you may want to keep this in case you need to re-install the 
program.
2.	During setup, you may receive a message that setup needs to update your 
system. If you receive this message, then allow setup to update your system. 
After setup updates your system, reboot and execute setup again. This is usually the case
if you do not have the Visual Studio installer.  You may also have to install the
Microsoft Data Access Controls (mdac), if so , then you will need to reboot and start
the install again to complete installation.
3.	In Windows 98, the MSDOS command window that vfsm.exe and uh.exe 
executes within is not automatically closed. You should close this manually.
4.	On some systems, if you choose to install the package in drv:\Program Files, 
then the execution menu may not work correctly for uh and vfsm. We have seen 
this on Windows NT 4.0 systems. The default install directory is drv:\vfsmod. To 
avoid this problem, we recommend you use this directory.
5.	If you have a previous version of vfsmod on your computer, you should 
uninstall prior to installing this version.
6.	With this version, on Windows NT, 2000, and XP, you will need 
Administrator privileges to install. A few system files are copied into the 
Windows System directories.






